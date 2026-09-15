"""İş (job) uç noktaları: oluşturma, izleme ve canlı akış."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..core.job_store import job_store
from ..core.models import Job, JobRequest, JobStatus, JobSummary, TraceEvent, User
from ..core.pipeline import Pipeline
from .auth import get_current_user
from .events import event_bus

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
pipeline = Pipeline()


def _run_pipeline(job: Job, loop: asyncio.AbstractEventLoop | None) -> Job:
    """Boru hattını çalıştırır; olayları varsa canlı kanala yollar."""
    delay = job.request.stage_delay_ms / 1000.0

    def on_event(event: TraceEvent) -> None:
        if loop is not None:
            event_bus.publish_threadsafe(
                loop,
                job.id,
                {"type": "stage", "event": json.loads(event.model_dump_json())},
            )
        if delay:
            time.sleep(delay)

    result = pipeline.run(job, on_event=on_event)
    job_store.save(result)

    if loop is not None:
        event_bus.publish_threadsafe(
            loop,
            job.id,
            {"type": "done", "job": json.loads(result.model_dump_json())},
        )
    event_bus.mark_finished(job.id)
    return result


@router.post("", response_model=Job)
async def create_job(
    request: JobRequest,
    stream: bool = Query(
        default=False,
        description=(
            "Doğru verilirse iş arka planda başlatılır ve sonuç olay akışından izlenir. "
            "Yanlış verilirse istek, iş bitene kadar bekler."
        ),
    ),
    user: User = Depends(get_current_user),
) -> Job:
    """Yeni bir iş oluşturur ve çalıştırır."""
    job = job_store.create(request, owner_id=user.id)

    if stream:
        loop = asyncio.get_running_loop()
        # Hesap yoğun olduğu için ayrı bir iş parçacığında çalıştırılır.
        asyncio.get_running_loop().run_in_executor(None, _run_pipeline, job, loop)
        return job

    # Hata durumunda da iş nesnesi döndürülür, HTTP hatası atılmaz: hangi aşamada
    # durulduğunu göstermek, isteği başarısız saymaktan daha öğreticidir.
    return await asyncio.get_running_loop().run_in_executor(None, _run_pipeline, job, None)


@router.get("", response_model=list[JobSummary])
async def list_jobs(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
) -> list[JobSummary]:
    """Kullanıcının son işleri."""
    return job_store.list_summaries(owner_id=user.id, limit=limit)


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str, user: User = Depends(get_current_user)) -> Job:
    """Tek bir işin tüm ayrıntısı."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"İş bulunamadı: {job_id}")
    return job


@router.get("/{job_id}/events")
async def stream_job_events(job_id: str, user: User = Depends(get_current_user)):
    """İşin aşamalarını canlı olarak yayınlar (Server-Sent Events).

    Önce halihazırda kaydedilmiş aşamalar tekrar gönderilir, sonra yeni
    olaylar akmaya devam eder. Bu sayede istemci geç bağlansa bile hiçbir
    adımı kaçırmaz.
    """
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"İş bulunamadı: {job_id}")

    queue = event_bus.subscribe(job_id)

    async def generator():
        try:
            # 1. Kaçırılan aşamaları tekrar gönder.
            current = job_store.get(job_id)
            if current:
                for event in current.events:
                    yield _sse(
                        {"type": "stage", "event": json.loads(event.model_dump_json())}
                    )
                if current.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    yield _sse({"type": "done", "job": json.loads(current.model_dump_json())})
                    return

            # 2. Yeni olayları akıt.
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                except TimeoutError:
                    yield ": bekleniyor\n\n"  # bağlantıyı canlı tut
                    continue
                yield _sse(payload)
                if payload.get("type") == "done":
                    return
        finally:
            event_bus.unsubscribe(job_id, queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
