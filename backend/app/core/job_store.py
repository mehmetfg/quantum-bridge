"""Bellek içi iş deposu.

Şu an işler süreç belleğinde tutulur. Sunucu yeniden başlarsa geçmiş kaybolur.
Demo ve eğitim için bu yeterlidir ve kurulum gerektirmemesi bir avantajdır.

Bir sonraki aşamada kalıcı veritabanına geçmek için değiştirilmesi gereken
tek yer bu dosyadır: arayüz ve boru hattı JobStore'un yöntemlerini çağırır,
verinin nerede durduğunu bilmez.
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict

from .models import Job, JobRequest, JobSummary


class JobStore:
    """Sıralı, sınırlı boyutlu iş deposu."""

    def __init__(self, max_jobs: int = 200) -> None:
        self._jobs: OrderedDict[str, Job] = OrderedDict()
        self._lock = threading.Lock()
        self._max_jobs = max_jobs

    def create(self, request: JobRequest, owner_id: str = "demo") -> Job:
        job = Job(
            id=uuid.uuid4().hex[:12],
            problem_id=request.problem_id,
            request=request,
            owner_id=owner_id,
        )
        with self._lock:
            self._jobs[job.id] = job
            while len(self._jobs) > self._max_jobs:
                self._jobs.popitem(last=False)
        return job

    def save(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_summaries(self, owner_id: str | None = None, limit: int = 30) -> list[JobSummary]:
        """En yeniden eskiye doğru iş özetleri."""
        with self._lock:
            jobs = list(self._jobs.values())

        if owner_id is not None:
            jobs = [j for j in jobs if j.owner_id == owner_id]

        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [
            JobSummary(
                id=j.id,
                problem_id=j.problem_id,
                problem_title=j.problem_title or j.problem_id,
                status=j.status,
                created_at=j.created_at,
                answer_label=j.result.answer_label if j.result else None,
                confidence=j.result.confidence if j.result else None,
                total_duration_ms=j.total_duration_ms,
            )
            for j in jobs[:limit]
        ]

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()


#: Uygulama genelinde tek bir depo kullanılır.
job_store = JobStore()
