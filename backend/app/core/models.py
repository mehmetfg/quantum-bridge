"""Veri modelleri (Pydantic).

Bu dosya, sistemin ortak dilidir. Arayuz ile arka uc arasinda gidip gelen
her sey burada tanimlanir.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Stage(StrEnum):
    """Bir isin gectigi alti asama.

    Bu siralama projenin butun fikridir: kuantum, tek basina bir cozum degil,
    klasik bir boru hattinin ortasindaki ozel bir duraktir.
    """

    INTAKE = "INTAKE"
    AI_ROUTING = "AI_ROUTING"
    ENCODE_OPTIMIZE = "ENCODE_OPTIMIZE"
    QUANTUM_EXEC = "QUANTUM_EXEC"
    DECODE = "DECODE"
    CLASSICAL_MERGE = "CLASSICAL_MERGE"


STAGE_ORDER: list[Stage] = [
    Stage.INTAKE,
    Stage.AI_ROUTING,
    Stage.ENCODE_OPTIMIZE,
    Stage.QUANTUM_EXEC,
    Stage.DECODE,
    Stage.CLASSICAL_MERGE,
]

STAGE_LABELS: dict[Stage, dict[str, str]] = {
    Stage.INTAKE: {
        "title": "Klasik giriş",
        "side": "klasik",
        "summary": "Kullanıcıdan gelen problem ve veri doğrulanır, iç biçime çevrilir.",
        "why": (
            "Kuantum tarafına hatalı veri göndermek pahalıdır: gerçek donanımda her "
            "çalıştırma kuyruk süresi ve ücret demektir. Doğrulama bu yüzden en başta yapılır."
        ),
    },
    Stage.AI_ROUTING: {
        "title": "Yapay zeka yönlendirme",
        "side": "yapay zeka",
        "summary": "Problemin kuantuma uygun olup olmadığı ve hangi parametrelerle gideceği kararlaştırılır.",
        "why": (
            "Kuantum bilgisayar genel amaçlı bir hızlandırıcı değildir. Yönlendiricinin "
            "asıl işi, işin kuantuma gitmesi gereken küçük parçasını seçmektir."
        ),
    },
    Stage.ENCODE_OPTIMIZE: {
        "title": "Kodlama ve sadeleştirme",
        "side": "klasik",
        "summary": "Problem bir kuantum devresine çevrilir, devre sadeleştirilir ve OpenQASM metni üretilir.",
        "why": (
            "Devredeki her fazladan kapı, gerçek donanımda fazladan hata demektir. "
            "Göndermeden önce sadeleştirmek, sonucun kalitesini doğrudan artırır."
        ),
    },
    Stage.QUANTUM_EXEC: {
        "title": "Kuantum çalıştırma",
        "side": "kuantum",
        "summary": "Devre kuantum arka ucunda birden çok kez çalıştırılır ve ham ölçüm sayımları toplanır.",
        "why": (
            "Tek bir ölçüm tek bir örnektir. Dağılımı görebilmek için aynı devre "
            "yüzlerce kez çalıştırılır; her tekrara atış (shot) denir."
        ),
    },
    Stage.DECODE: {
        "title": "Çözümleme",
        "side": "klasik",
        "summary": "Ham sayımlar istatistiksel olarak yorumlanır ve bir cevaba çevrilir.",
        "why": (
            "Kuantum tarafı cevap vermez, dağılım verir. Cevabı o dağılımdan çıkarmak "
            "ve ne kadar güvenilir olduğunu ölçmek klasik tarafın işidir."
        ),
    },
    Stage.CLASSICAL_MERGE: {
        "title": "Klasik birleştirme",
        "side": "klasik",
        "summary": "Cevap klasik olarak doğrulanır ve asıl iş akışının içine yerleştirilir.",
        "why": (
            "Hibrit hesaplamanın kapanış adımı budur. Kuantumdan gelen sonuç, klasik "
            "programın bir değişkeni haline gelmedikçe hiçbir işe yaramaz."
        ),
    },
}


class JobStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TraceEvent(BaseModel):
    """Bir asamada ne olduguna dair kayit. Arayuzdeki canli anlatimin kaynagi."""

    stage: Stage
    title: str
    side: str = Field(description="klasik, yapay zeka veya kuantum")
    summary: str
    why: str = Field(default="", description="Bu adım neden var")
    details: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "ok"


class ProblemInfo(BaseModel):
    """Bir problemin tanitim karti."""

    id: str
    title: str
    category: str
    short_description: str
    description: str
    quantum_advantage: str = Field(description="Kuantumun burada ne kazandırdığı")
    classical_comparison: str = Field(description="Aynı iş klasik olarak nasıl yapılırdı")
    difficulty: str = "başlangıç"
    default_input: dict[str, Any] = Field(default_factory=dict)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    concepts: list[str] = Field(default_factory=list)


class JobRequest(BaseModel):
    """Yeni is olusturma istegi."""

    problem_id: str
    input: dict[str, Any] = Field(default_factory=dict)
    shots: int | None = Field(default=None, ge=1, le=20000)
    backend_id: str | None = None
    noise_level: str = Field(default="ideal", pattern="^(ideal|low|medium|high)$")
    seed: int | None = None
    stage_delay_ms: int = Field(
        default=0,
        ge=0,
        le=2000,
        description=(
            "Aşamalar arasına eklenen yapay bekleme. Yalnızca gösterim içindir: "
            "sunum sırasında adımların tek tek izlenebilmesini sağlar."
        ),
    )


class RoutingDecision(BaseModel):
    """Yapay zeka yonlendiricinin karari."""

    use_quantum: bool
    n_qubits: int
    shots: int
    encoding: str
    strategy: str
    confidence_target: float
    reasoning: list[str] = Field(default_factory=list)
    rejected_alternatives: list[str] = Field(default_factory=list)
    cost_estimate: dict[str, Any] = Field(default_factory=dict)
    source: str = "kural-tabanli"


class FinalResult(BaseModel):
    """Isin son cikti paketi."""

    answer: Any
    answer_label: str
    confidence: float
    verified: bool | None = None
    verification_note: str = ""
    classical_usage: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    """Bir is (job): girdiden sonuca kadar tum hikaye."""

    id: str
    problem_id: str
    problem_title: str = ""
    status: JobStatus = JobStatus.QUEUED
    owner_id: str = "demo"
    request: JobRequest
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    current_stage: Stage | None = None
    events: list[TraceEvent] = Field(default_factory=list)
    routing: RoutingDecision | None = None
    circuit: dict[str, Any] | None = None
    qasm: str | None = None
    raw_result: dict[str, Any] | None = None
    result: FinalResult | None = None
    error: str | None = None
    total_duration_ms: float = 0.0


class JobSummary(BaseModel):
    """Liste ekranlari icin kisa is ozeti."""

    id: str
    problem_id: str
    problem_title: str
    status: JobStatus
    created_at: datetime
    answer_label: str | None = None
    confidence: float | None = None
    total_duration_ms: float = 0.0


class User(BaseModel):
    """Kullanıcı modeli.

    Şu an tek bir demo kullanıcı var ve giriş ekranı yok. Model yine de
    baştan burada duruyor ki, giriş özelliği eklendiğinde iş kayıtlarının
    sahipliği geçmişe dönük değiştirilmek zorunda kalmasın.
    """

    id: str
    display_name: str
    is_demo: bool = True
