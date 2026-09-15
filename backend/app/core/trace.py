"""İzleme (trace) toplayıcı.

Her aşama burada kayıt bırakır. Arayüzdeki canlı anlatım bu kayıtlardan
üretilir. Kayıtlar sadece "ne oldu" değil, "neden böyle yapıldı" bilgisini
de taşır; eğitim önceliği tam olarak burada somutlaşır.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from .models import STAGE_LABELS, Stage, TraceEvent


class TraceCollector:
    """Aşama kayıtlarını toplar ve isteyene anlık olarak iletir."""

    def __init__(self, on_event: Callable[[TraceEvent], None] | None = None) -> None:
        self.events: list[TraceEvent] = []
        self._on_event = on_event
        self._stage_started: float | None = None

    def start_stage(self) -> None:
        self._stage_started = time.perf_counter()

    def record(
        self,
        stage: Stage,
        details: list[str] | None = None,
        data: dict[str, Any] | None = None,
        status: str = "ok",
        summary_override: str | None = None,
    ) -> TraceEvent:
        """Bir aşamayı kaydeder ve dinleyiciye iletir."""
        labels = STAGE_LABELS[stage]
        duration = 0.0
        if self._stage_started is not None:
            duration = (time.perf_counter() - self._stage_started) * 1000.0
            self._stage_started = None

        event = TraceEvent(
            stage=stage,
            title=labels["title"],
            side=labels["side"],
            summary=summary_override or labels["summary"],
            why=labels["why"],
            details=details or [],
            data=data or {},
            duration_ms=round(duration, 3),
            status=status,
        )
        self.events.append(event)
        if self._on_event:
            self._on_event(event)
        return event

    def record_error(self, stage: Stage, message: str) -> TraceEvent:
        return self.record(
            stage,
            details=[message],
            status="error",
            summary_override="Bu aşamada hata oluştu ve iş durduruldu.",
        )

    @property
    def total_duration_ms(self) -> float:
        return round(sum(e.duration_ms for e in self.events), 3)
