"""İş olayları için yayın kanalı (event bus).

Boru hattı ayrı bir iş parçacığında (thread) çalışır, çünkü sayısal hesap
olay döngüsünü (event loop) bloke eder. Buradaki kanal, o iş parçacığından
gelen olayları güvenli biçimde asenkron dünyaya taşır.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class JobEventBus:
    """İş kimliğine göre olay dağıtımı yapar."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._finished: set[str] = set()

    def subscribe(self, job_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[job_id].append(queue)
        return queue

    def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        queues = self._subscribers.get(job_id)
        if not queues:
            return
        if queue in queues:
            queues.remove(queue)
        if not queues:
            self._subscribers.pop(job_id, None)

    def publish_threadsafe(
        self, loop: asyncio.AbstractEventLoop, job_id: str, payload: dict[str, Any]
    ) -> None:
        """Başka bir iş parçacığından olay yayınlar."""
        loop.call_soon_threadsafe(self._publish, job_id, payload)

    def _publish(self, job_id: str, payload: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(job_id, [])):
            queue.put_nowait(payload)

    def mark_finished(self, job_id: str) -> None:
        self._finished.add(job_id)

    def is_finished(self, job_id: str) -> bool:
        return job_id in self._finished


#: Uygulama genelinde tek kanal kullanılır.
event_bus = JobEventBus()
