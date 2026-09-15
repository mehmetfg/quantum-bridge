"""Kuantum arka ucu icin ortak arayuz (interface).

Bu arayuzun sekli bilerek IBM Qiskit Runtime `Sampler` ciktisina benzetildi:
girdi bir devre ve atis sayisi, cikti ise olcum sayimlaridir (counts).
Boylece yerel simulatordan gercek donanima gecerken boru hattinin geri
kalani hic degismez; sadece bu arayuzu uygulayan yeni bir sinif yazilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from ..circuit import Circuit


@dataclass
class RawResult:
    """Kuantum tarafindan donen ham veri.

    Dikkat: burada "cevap" yoktur, sadece istatistik vardir. Olcum sayimlarini
    anlamli bir cevaba cevirmek klasik tarafin isidir (decode asamasi).
    """

    counts: dict[str, int]
    shots: int
    backend_name: str
    statevector: list[complex] | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    snapshots: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "counts": self.counts,
            "shots": self.shots,
            "backend_name": self.backend_name,
            "probabilities": self.probabilities,
            "statevector": (
                [{"re": round(a.real, 6), "im": round(a.imag, 6)} for a in self.statevector]
                if self.statevector is not None
                else None
            ),
            "snapshots": self.snapshots,
            "meta": self.meta,
        }


@dataclass
class BackendInfo:
    """Arka ucun tanitim karti; arayuzde secim listesinde gosterilir."""

    id: str
    name: str
    kind: str  # "simulator" | "hardware"
    max_qubits: int
    available: bool
    description: str
    supports_statevector: bool = False
    supports_noise: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind,
            "max_qubits": self.max_qubits,
            "available": self.available,
            "description": self.description,
            "supports_statevector": self.supports_statevector,
            "supports_noise": self.supports_noise,
            "notes": self.notes,
        }


@runtime_checkable
class QuantumBackend(Protocol):
    """Her kuantum arka ucunun uymasi gereken sozlesme."""

    @property
    def info(self) -> BackendInfo: ...

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        seed: int | None = None,
        noise_level: str = "ideal",
        collect_snapshots: bool = False,
    ) -> RawResult: ...
