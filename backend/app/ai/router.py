"""Yapay zeka yönlendirici (AI router).

Veri merkezinin içinde, bu işe göre özelleştirilmiş bir karar katmanı
olduğunu düşünün. Görevi şu soruya cevap vermektir:

    "Bu işin hangi parçası kuantuma gitmeli, hangi parametrelerle?"

Yaygın bir yanlış anlama var, baştan düzeltmek gerekir: kuantum bilgisayar
genel amaçlı bir hızlandırıcı değildir. Bir yapay zeka modelinin tamamını
kuantum bilgisayarda eğitmek bugün pratik değildir, araştırma aşamasındadır.

Bugün gerçekçi olan şey hibrit hesaplamadır: klasik sistem ve yapay zeka
işin büyük kısmını yapar, yalnızca kuantumun avantajlı olduğu küçük alt
problem kuantuma gönderilir. Bu yönlendirici tam olarak o seçimi yapar.

Şu anki sürüm kural tabanlıdır ve bilerek tamamen şeffaftır: her kararın
gerekçesi metin olarak üretilir ve arayüzde gösterilir. Öğrenmek için
kara kutu bir modelden daha değerlidir. Bir dil modeline bağlanmak
isterseniz llm_adapter.py dosyası bu kararları zenginleştirmek için hazır
durumda bekliyor.
"""

from __future__ import annotations

from ..core.models import JobRequest, RoutingDecision
from ..problems.base import Problem, ProblemSpec

#: Kuantum avantajının anlamlı olmaya başladığı kabaca eşikler.
#: Bu sayılar kesin değil, büyüklük mertebesi göstergesidir.
ADVANTAGE_THRESHOLDS = {
    "grover-search": 1_000,
    "deutsch-jozsa": 20,
    "bernstein-vazirani": 64,
}


class QuantumRouter:
    """Kural tabanlı, şeffaf yönlendirici."""

    def decide(
        self, problem: Problem, spec: ProblemSpec, request: JobRequest
    ) -> RoutingDecision:
        hints = problem.routing_hints(spec)

        # Kullanıcı atış sayısını elle verdiyse ona saygı gösteririz,
        # ama farkı gerekçeye yazarız.
        shots = request.shots or hints.shots
        reasoning = list(hints.reasoning)

        if request.shots and request.shots != hints.shots:
            reasoning.append(
                f"Yönlendirici {hints.shots} atış önermişti, kullanıcı {request.shots} seçti. "
                "Kullanıcı tercihi geçerli sayıldı."
            )

        reasoning.extend(self._scale_reasoning(problem.id, spec))
        reasoning.append(self._shots_precision_note(shots))

        if request.noise_level != "ideal":
            reasoning.append(
                f"Gürültü seviyesi '{request.noise_level}' seçildi. Bu, gerçek donanımın "
                "hata davranışını taklit eder ve sonucun güvenini düşürmesi beklenir."
            )

        return RoutingDecision(
            use_quantum=True,
            n_qubits=hints.n_qubits,
            shots=shots,
            encoding=hints.encoding,
            strategy=hints.strategy,
            confidence_target=hints.confidence_target,
            reasoning=reasoning,
            rejected_alternatives=hints.rejected_alternatives,
            cost_estimate=self._cost_estimate(hints.n_qubits, shots),
            source="kural-tabanlı",
        )

    @staticmethod
    def _scale_reasoning(problem_id: str, spec: ProblemSpec) -> list[str]:
        """Bu problem boyutunda kuantum gerçekten kazandırıyor mu?"""
        threshold = ADVANTAGE_THRESHOLDS.get(problem_id)
        if threshold is None:
            return [
                "Bu problemde kuantum kazancı hız değil, niteliktir: klasik olarak "
                "üretilemeyen bir şey üretiliyor."
            ]
        size = (
            spec.params.get("n_states")
            or 2 ** spec.params.get("n_bits", 0)
            or 0
        )
        if size >= threshold:
            return [
                f"Problem boyutu {size}, anlamlı kazanç eşiği {threshold}. Bu ölçekte "
                "kuantum yaklaşımı klasiğe göre gerçekten avantajlı."
            ]
        return [
            f"Dürüst değerlendirme: problem boyutu {size}, anlamlı kazanç eşiği ise "
            f"{threshold} civarı. Bu ölçekte klasik çözüm daha hızlı ve ucuzdur. "
            "Kuantum yolu burada öğrenmek ve mekanizmayı görmek için seçiliyor.",
        ]

    @staticmethod
    def _shots_precision_note(shots: int) -> str:
        """Atış sayısının istatistiksel hassasiyete etkisi."""
        error = 1.0 / (shots ** 0.5)
        return (
            f"{shots} atış, ölçülen oranlarda yaklaşık yüzde {error * 100:.1f} istatistik "
            "belirsizlik bırakır. Hassasiyeti iki katına çıkarmak için atış sayısını "
            "dört katına çıkarmak gerekir."
        )

    @staticmethod
    def _cost_estimate(n_qubits: int, shots: int) -> dict:
        """Sembolik maliyet tahmini: simülasyon ve gerçek donanım karşılaştırması."""
        state_size = 2 ** n_qubits
        # Gerçek donanımda tipik bir atış yaklaşık 100 mikrosaniye sürer.
        hardware_seconds = shots * 100e-6
        return {
            "state_dimension": state_size,
            "classical_memory_bytes": state_size * 16,
            "simulated_shots": shots,
            "estimated_hardware_seconds": round(hardware_seconds, 4),
            "note": (
                f"{n_qubits} kubit, klasik bellekte {state_size} genlik yani yaklaşık "
                f"{state_size * 16} bayt demektir. Bu boyut kolayca simüle edilir. "
                "Asıl eşik yaklaşık 50 kubittir: orada gereken bellek dünyadaki tüm "
                "bilgisayarların toplam belleğini aşar."
            ),
            "hardware_note": (
                f"Gerçek donanımda {shots} atış yaklaşık {hardware_seconds:.3f} saniye "
                "çalışma süresi demektir. Buna kuyrukta bekleme eklenir ve bekleme "
                "genellikle çalışma süresinden kat kat uzundur."
            ),
        }
