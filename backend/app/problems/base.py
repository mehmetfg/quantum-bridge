"""Problem arayuzu.

Her problem uc soruya cevap verir:

1. build_circuit: bu problem hangi kuantum devresine cevrilir? (kodlama)
2. decode: donen olcum sayimlari ne anlama gelir? (cozumleme)
3. merge: bu cevap klasik programda nasil kullanilir? (birlestirme)

Bu ucluyu ayirmak kasitlidir. Cogu kisi kuantum hesaplamayi sadece birinci
adim sanir; oysa hibrit sistemlerde asil is ikinci ve ucuncu adimdadir.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..core.models import FinalResult, ProblemInfo
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit


@dataclass
class ProblemSpec:
    """Dogrulanmis ve ic bicime cevrilmis problem tanimi."""

    problem_id: str
    params: dict[str, Any]
    notes: list[str] = field(default_factory=list)


@dataclass
class RoutingHints:
    """Problemin yonlendiriciye verdigi ipuclari.

    Yonlendirici son karari verir ama kaynak bilgiyi problemden alir;
    boylece her yeni problem, yonlendiriciyi degistirmeden sisteme eklenir.
    """

    n_qubits: int
    shots: int
    encoding: str
    strategy: str
    confidence_target: float = 0.9
    reasoning: list[str] = field(default_factory=list)
    rejected_alternatives: list[str] = field(default_factory=list)


@dataclass
class Decoded:
    """Cozumleme ciktisi: ham sayimlardan cikarilan cevap."""

    answer: Any
    answer_label: str
    confidence: float
    explanation: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


class ValidationError(ValueError):
    """Kullanici girdisi gecersiz oldugunda firlatilir."""


class Problem(ABC):
    """Tum problemlerin ortak atasi."""

    id: str
    title: str
    category: str
    short_description: str
    description: str
    quantum_advantage: str
    classical_comparison: str
    difficulty: str = "baslangic"
    concepts: list[str] = []

    @property
    @abstractmethod
    def default_input(self) -> dict[str, Any]:
        """Arayuzun onceden doldurdugu ornek girdi."""

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """Arayuzun form uretmek icin kullandigi alan tanimlari."""

    @abstractmethod
    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        """Kullanici girdisini dogrular ve ic bicime cevirir."""

    @abstractmethod
    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        """Yonlendiriciye kaynak bilgi saglar."""

    @abstractmethod
    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        """Problemi kuantum devresine cevirir."""

    @abstractmethod
    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        """Ham olcum sayimlarini cevaba cevirir."""

    @abstractmethod
    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        """Cevabi klasik is akisinin icine yerlestirir ve mumkunse dogrular."""

    # Ortak yardimcilar -------------------------------------------------------

    @staticmethod
    def top_outcome(counts: dict[str, int]) -> tuple[str, int]:
        """En cok gozlenen olcum sonucunu ve sayisini dondurur."""
        if not counts:
            raise ValueError("Ölçüm sonucu boş geldi.")
        return max(counts.items(), key=lambda kv: kv[1])

    @staticmethod
    def confidence_of(counts: dict[str, int], outcome: str) -> float:
        """Bir sonucun tum atislar icindeki payi: sade bir guven olcusu."""
        total = sum(counts.values())
        return round(counts.get(outcome, 0) / total, 4) if total else 0.0

    def info(self) -> ProblemInfo:
        return ProblemInfo(
            id=self.id,
            title=self.title,
            category=self.category,
            short_description=self.short_description,
            description=self.description,
            quantum_advantage=self.quantum_advantage,
            classical_comparison=self.classical_comparison,
            difficulty=self.difficulty,
            default_input=self.default_input,
            input_schema=self.input_schema,
            concepts=list(self.concepts),
        )
