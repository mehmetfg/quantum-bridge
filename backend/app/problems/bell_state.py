"""Problem 2: Dolaniklik (entanglement) gosterimi.

Iki kubit dolanik hale getirildiginde, tek tek her birinin sonucu rastgeledir
ama ikisi arasindaki iliski kesindir. Birini olcup sonucu ogrendiginizde,
digerinin sonucunu de anlamis olursunuz.

Einstein bunu "uzaktan hayaletimsi etki" diye elestirdi. Deneyler Einstein'in
degil, kuantum mekaniginin hakli oldugunu gosterdi ve bu calisma 2022 Nobel
Fizik Odulu'nu kazandi.

Bu problem, klasik bilgisayarda taklit edilemeyen ilk gercek kuantum olgusunu
gozle gorulur hale getirir.
"""

from __future__ import annotations

from typing import Any

from ..core.models import FinalResult
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit
from .base import Decoded, Problem, ProblemSpec, RoutingHints, ValidationError

STATE_LABELS = {
    "phi_plus": "Phi artı: (|00> + |11>) / karekök 2",
    "phi_minus": "Phi eksi: (|00> - |11>) / karekök 2",
    "psi_plus": "Psi artı: (|01> + |10>) / karekök 2",
    "psi_minus": "Psi eksi: (|01> - |10>) / karekök 2",
}


class BellStateProblem(Problem):
    id = "bell-state"
    title = "Dolanıklık: Bell ve GHZ durumları"
    category = "Temel olgular"
    short_description = "İki veya daha çok kubiti birbirine bağla, korelasyonu ölç."
    description = (
        "İlk kubit Hadamard ile süperpozisyona sokulur, sonra CNOT kapısıyla diğer "
        "kubitlere bağlanır. Sonuçta hiçbir kubitin tek başına belirli bir değeri yoktur, "
        "ama hepsi birlikte ölçüldüğünde ya hep sıfır ya hep bir çıkarlar. İkiden fazla "
        "kubit için aynı yapıya GHZ durumu denir."
    )
    quantum_advantage = (
        "Klasik bir sistemde iki bit ya bağımsızdır ya da önceden anlaşılmıştır. "
        "Dolanıklıkta ise sonuçlar önceden belirli değildir, buna rağmen mükemmel "
        "uyumludur. Bu, klasik olarak üretilemeyen bir korelasyondur."
    )
    classical_comparison = (
        "İki zarfa aynı rengi koyup uzağa göndermek klasik korelasyondur: renk baştan "
        "bellidir. Dolanıklıkta renk ölçüm anında belirlenir, yine de iki taraf uyuşur."
    )
    difficulty = "başlangıç"
    concepts = ["dolanıklık", "CNOT kapısı", "korelasyon", "GHZ durumu"]

    @property
    def default_input(self) -> dict[str, Any]:
        return {"parties": 2, "state": "phi_plus"}

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "parties": {
                "type": "integer",
                "label": "Kubit sayısı",
                "min": 2,
                "max": 6,
                "default": 2,
                "help": "2 kubit Bell durumu, 3 ve üzeri GHZ durumu üretir.",
            },
            "state": {
                "type": "select",
                "label": "Hedef durum",
                "options": [
                    {"value": "phi_plus", "label": STATE_LABELS["phi_plus"]},
                    {"value": "phi_minus", "label": STATE_LABELS["phi_minus"]},
                    {"value": "psi_plus", "label": STATE_LABELS["psi_plus"]},
                    {"value": "psi_minus", "label": STATE_LABELS["psi_minus"]},
                ],
                "default": "phi_plus",
                "help": "Dört Bell durumu birbirinden faz ve bit çevirmeleriyle ayrılır.",
            },
        }

    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        parties = int(raw_input.get("parties", 2))
        state = str(raw_input.get("state", "phi_plus"))
        if not 2 <= parties <= 6:
            raise ValidationError("Kubit sayısı 2 ile 6 arasında olmalıdır.")
        if state not in STATE_LABELS:
            raise ValidationError(f"Bilinmeyen durum: {state}")
        if parties > 2 and state != "phi_plus":
            raise ValidationError(
                "İkiden fazla kubitte yalnızca Phi artı temelli GHZ durumu üretilir."
            )
        return ProblemSpec(
            problem_id=self.id,
            params={"parties": parties, "state": state},
            notes=[
                "Bell durumu" if parties == 2 else f"{parties} kubitlik GHZ durumu",
                f"Hedef: {STATE_LABELS[state]}",
            ],
        )

    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        parties = spec.params["parties"]
        return RoutingHints(
            n_qubits=parties,
            shots=1024,
            encoding="durum hazırlama (state preparation)",
            strategy="Hadamard ile süperpozisyon, CNOT zinciri ile bağlama",
            confidence_target=0.95,
            reasoning=[
                f"{parties} kubit istendi; dolanıklık için ek kubite gerek yok.",
                "Atış sayısı 1024 seçildi. Burada aranan tek bir cevap değil, bir dağılım. "
                "1024 atışta yüzde 50 beklenen bir sonucun sapması yaklaşık yüzde 1,5 kalır.",
                f"CNOT kapısı sayısı {parties - 1}. Dolanıklığın maliyeti budur ve gerçek "
                "donanımda hatanın da ana kaynağıdır.",
            ],
            rejected_alternatives=[
                "Klasik simülasyonla korelasyon üretmek: sayılar aynı görünür ama "
                "dolanıklık değildir, çünkü sonuçlar baştan belirlidir.",
            ],
        )

    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        state = spec.params["state"]
        circuit = Circuit(n_qubits=n_qubits, name="dolaniklik")

        circuit.barrier_label("İlk kubiti süperpozisyona sok")
        circuit.h(0)

        circuit.barrier_label("CNOT zinciri ile kubitleri bağla")
        for q in range(1, n_qubits):
            circuit.cx(0, q)

        if state in ("phi_minus", "psi_minus"):
            circuit.barrier_label("Faz işaretini çevir")
            circuit.z(0)
        if state in ("psi_plus", "psi_minus"):
            circuit.barrier_label("İkinci kubiti çevirerek karşıt korelasyona geç")
            circuit.x(1)

        circuit.measure_all()
        return circuit

    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        parties = spec.params["parties"]
        state = spec.params["state"]
        total = sum(raw.counts.values()) or 1

        if state in ("phi_plus", "phi_minus"):
            expected = {"0" * parties, "1" * parties}
            relation = "aynı"
        else:
            expected = {"01", "10"}
            relation = "karşıt"

        correlated = sum(c for k, c in raw.counts.items() if k in expected)
        unexpected = {k: c for k, c in raw.counts.items() if k not in expected}
        correlation = round(correlated / total, 4)

        return Decoded(
            answer=correlation,
            answer_label=f"Korelasyon: yüzde {correlation * 100:.1f} ({relation} yönlü)",
            confidence=correlation,
            explanation=[
                f"Beklenen sonuçlar: {', '.join(sorted(expected))}.",
                f"{total} atışın {correlated} tanesi beklenen kalıba uydu.",
                (
                    "Beklenmeyen sonuç yok: dolanıklık tam."
                    if not unexpected
                    else f"Beklenmeyen sonuçlar: {unexpected}. Bunlar gürültünün izidir."
                ),
                "Dikkat edilecek nokta: tek tek her kubitin sonucu yaklaşık yarı yarıya "
                "dağılır, yani tek başına rastgeledir. Kesinlik ikisi arasındaki ilişkidedir.",
            ],
            details={
                "correlation": correlation,
                "expected_outcomes": sorted(expected),
                "unexpected": unexpected,
                "marginals": self._marginals(raw.counts, parties),
            },
        )

    @staticmethod
    def _marginals(counts: dict[str, int], parties: int) -> list[dict[str, Any]]:
        """Her kubitin tek başına 1 çıkma oranı: rastgele olduklarını gösterir."""
        total = sum(counts.values()) or 1
        result = []
        for q in range(parties):
            ones = sum(c for k, c in counts.items() if k[q] == "1")
            result.append({"qubit": q, "p_one": round(ones / total, 4)})
        return result

    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        correlation = decoded.details["correlation"]
        marginals = decoded.details["marginals"]
        parties = spec.params["parties"]
        verified = correlation >= 0.9

        return FinalResult(
            answer=correlation,
            answer_label=decoded.answer_label,
            confidence=correlation,
            verified=verified,
            verification_note=(
                "Klasik doğrulama: her kubitin tek başına 1 çıkma oranı yarıya yakın, "
                "buna rağmen ortak sonuç neredeyse her zaman uyumlu. Klasik bağımsız "
                "bitlerde bu ikisi aynı anda olamaz."
                if verified
                else "Korelasyon beklenen seviyenin altında kaldı. Gürültü seviyesini "
                "düşürüp tekrar denemek farkı gösterir."
            ),
            classical_usage=(
                f"Bu {parties} kubitlik durum, kuantum anahtar dağıtımının (QKD) temelidir. "
                "Klasik programda sonuç, iki taraf arasında ortak gizli anahtar üretmek için "
                "kullanılır: her iki taraf da ölçüm sonuçlarını bilir, dinleyen taraf bilemez."
            ),
            details={
                "correlation": correlation,
                "per_qubit_marginals": marginals,
                "shared_key_preview": "".join(
                    "1" if m["p_one"] >= 0.5 else "0" for m in marginals
                ),
            },
        )
