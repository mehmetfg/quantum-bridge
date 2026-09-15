"""Problem 3: Deutsch-Jozsa algoritması.

Elimizde bir kara kutu fonksiyon var. Bu fonksiyon ya her girdiye aynı cevabı
veriyor (sabit), ya da girdilerin tam yarısına sıfır, yarısına bir veriyor
(dengeli). Hangisi olduğunu bulmamız isteniyor.

Klasik olarak en kötü durumda girdilerin yarısından bir fazlasını denemek
gerekir: 20 bitlik bir girdide bu yarım milyondan fazla sorgu demektir.

Kuantum olarak tek bir sorgu yeter. Bunun sebebi, süperpozisyon sayesinde
fonksiyonun tüm girdilere aynı anda uygulanması ve girişim (interference)
sayesinde istenmeyen ihtimallerin birbirini götürmesidir.

Bu, kuantum üstünlüğünün kanıtlanmış ilk örneğidir. Pratik faydası sınırlıdır
ama fikri göstermek için en berrak örnektir.
"""

from __future__ import annotations

from typing import Any

from ..core.models import FinalResult
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit
from .base import Decoded, Problem, ProblemSpec, RoutingHints, ValidationError

ORACLE_LABELS = {
    "constant_0": "Sabit: her girdiye 0 döndürür",
    "constant_1": "Sabit: her girdiye 1 döndürür",
    "balanced_parity": "Dengeli: girdideki 1'lerin sayısının tekliği",
    "balanced_first_bit": "Dengeli: sadece ilk bite bakar",
}


class DeutschJozsaProblem(Problem):
    id = "deutsch-jozsa"
    title = "Deutsch-Jozsa: sabit mi, dengeli mi?"
    category = "Algoritma"
    short_description = "Bir kara kutu fonksiyonun türünü tek sorguda belirle."
    description = (
        "Gizli fonksiyon bir kuantum kapı dizisine (oracle) gömülür. Tüm girdiler aynı "
        "anda süperpozisyon halinde fonksiyona verilir. Çıkışta ikinci bir Hadamard katmanı, "
        "sabit fonksiyonlarda tüm olasılığı sıfır dizgisine toplar; dengeli fonksiyonlarda "
        "ise sıfır dizgisinin olasılığını tamamen yok eder. Sonucu okumak yeterlidir."
    )
    quantum_advantage = (
        "Tek sorgu. Klasik en kötü durumda 2 üzeri (n eksi 1) artı 1 sorgu gerekir; "
        "kuantumda girdi uzunluğundan bağımsız olarak bir sorgu yeter."
    )
    classical_comparison = (
        "Klasik algoritma girdileri tek tek dener. İki farklı sonuç görürse dengeli der; "
        "yarıdan bir fazlasını aynı görürse sabit der. Bu, girdi uzunluğuyla üstel büyür."
    )
    difficulty = "orta"
    concepts = ["girişim", "oracle", "faz geri tepmesi", "üstel hızlanma"]

    @property
    def default_input(self) -> dict[str, Any]:
        return {"n_bits": 3, "oracle": "balanced_parity"}

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "n_bits": {
                "type": "integer",
                "label": "Girdi bit sayısı",
                "min": 1,
                "max": 6,
                "default": 3,
                "help": "Fonksiyonun kaç bitlik girdi aldığı. Klasik maliyet buna göre üstel büyür.",
            },
            "oracle": {
                "type": "select",
                "label": "Gizli fonksiyon",
                "options": [
                    {"value": key, "label": label} for key, label in ORACLE_LABELS.items()
                ],
                "default": "balanced_parity",
                "help": "Algoritma bu seçimi bilmiyormuş gibi davranır; görevi türü bulmaktır.",
            },
        }

    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        n_bits = int(raw_input.get("n_bits", 3))
        oracle = str(raw_input.get("oracle", "balanced_parity"))
        if not 1 <= n_bits <= 6:
            raise ValidationError("Girdi bit sayısı 1 ile 6 arasında olmalıdır.")
        if oracle not in ORACLE_LABELS:
            raise ValidationError(f"Bilinmeyen fonksiyon türü: {oracle}")
        if oracle == "balanced_first_bit" and n_bits < 1:
            raise ValidationError("Bu fonksiyon en az 1 bitlik girdi ister.")
        truth = "sabit" if oracle.startswith("constant") else "dengeli"
        return ProblemSpec(
            problem_id=self.id,
            params={"n_bits": n_bits, "oracle": oracle, "truth": truth},
            notes=[
                f"Girdi uzayı {2 ** n_bits} farklı değer içeriyor.",
                f"Klasik en kötü durum: {2 ** (n_bits - 1) + 1} sorgu.",
                "Kuantum: 1 sorgu.",
            ],
        )

    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        n_bits = spec.params["n_bits"]
        classical_worst = 2 ** (n_bits - 1) + 1
        return RoutingHints(
            n_qubits=n_bits + 1,
            shots=256,
            encoding="oracle gömme ve faz geri tepmesi (phase kickback)",
            strategy="Hadamard sandviçi: süperpozisyon, oracle, tekrar Hadamard",
            confidence_target=0.99,
            reasoning=[
                f"{n_bits} girdi kubiti ve 1 yardımcı (ancilla) kubit gerekiyor, toplam {n_bits + 1}.",
                "Yardımcı kubit eksi durumuna hazırlanır. Bu, fonksiyonun cevabını "
                "genliğin işaretine yazmasını sağlar; buna faz geri tepmesi denir.",
                "Atış sayısı 256 seçildi. İdeal koşulda tek atış yeterlidir; tekrar sadece "
                "gürültü varken sonucun ne kadar temiz olduğunu görmek için.",
                f"Klasik en kötü durumda {classical_worst} sorgu gerekirdi, kuantumda 1 sorgu.",
            ],
            rejected_alternatives=[
                "Klasik tarama: küçük bit sayılarında daha basit ve yeterli. Kuantum kazancı "
                "ancak girdi uzunluğu büyüdükçe anlam kazanır.",
            ],
        )

    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        n_bits = spec.params["n_bits"]
        oracle = spec.params["oracle"]
        ancilla = n_bits  # son kubit yardımcı kubittir

        circuit = Circuit(n_qubits=n_qubits, name="deutsch-jozsa")

        circuit.barrier_label("Yardımcı kubiti eksi durumuna hazırla")
        circuit.x(ancilla)
        circuit.h(ancilla)

        circuit.barrier_label("Tüm girdileri aynı anda süperpozisyona sok")
        for q in range(n_bits):
            circuit.h(q)

        circuit.barrier_label("Gizli fonksiyonu uygula (oracle)")
        self._apply_oracle(circuit, oracle, n_bits, ancilla)

        circuit.barrier_label("Girişim: ihtimalleri birbirine karıştır")
        for q in range(n_bits):
            circuit.h(q)

        circuit.measure(*range(n_bits))
        return circuit

    @staticmethod
    def _apply_oracle(circuit: Circuit, oracle: str, n_bits: int, ancilla: int) -> None:
        if oracle == "constant_0":
            # Hiçbir şey yapma: f(x) = 0 her zaman.
            return
        if oracle == "constant_1":
            # Yardımcı kubiti her zaman çevir: f(x) = 1 her zaman.
            circuit.x(ancilla)
            return
        if oracle == "balanced_parity":
            # f(x) = x içindeki 1'lerin sayısının tekliği. Tam yarı yarıya böler.
            for q in range(n_bits):
                circuit.cx(q, ancilla)
            return
        if oracle == "balanced_first_bit":
            # f(x) = ilk bit. Bu da girdileri tam ikiye böler.
            circuit.cx(0, ancilla)
            return
        raise ValueError(f"Bilinmeyen oracle: {oracle}")

    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        n_bits = spec.params["n_bits"]
        total = sum(raw.counts.values()) or 1
        all_zeros = "0" * n_bits
        zero_count = raw.counts.get(all_zeros, 0)
        p_zero = zero_count / total

        # Karar kuralı: sıfır dizgisi baskınsa fonksiyon sabittir.
        verdict = "sabit" if p_zero > 0.5 else "dengeli"
        confidence = round(p_zero if verdict == "sabit" else 1 - p_zero, 4)

        return Decoded(
            answer=verdict,
            answer_label=f"Fonksiyon {verdict}",
            confidence=confidence,
            explanation=[
                f"Sıfır dizgisi ({all_zeros}) {zero_count} kez gözlendi, "
                f"toplam {total} atışın yüzde {p_zero * 100:.1f} kadarı.",
                (
                    "Sabit fonksiyonda tüm olasılık sıfır dizgisinde toplanır, çünkü "
                    "diğer ihtimallerin genlikleri birbirini götürür."
                    if verdict == "sabit"
                    else "Dengeli fonksiyonda sıfır dizgisinin genliği tamamen yok olur, "
                    "bu yüzden gözlenmemesi beklenir."
                ),
                "Karar tek bir ölçümle verilebilirdi. Tekrar edilmesinin tek sebebi, "
                "gürültünün sonucu ne kadar bozduğunu görmektir.",
            ],
            details={
                "p_zero": round(p_zero, 4),
                "all_zeros": all_zeros,
                "distribution": raw.counts,
                "n_bits": n_bits,
            },
        )

    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        n_bits = spec.params["n_bits"]
        truth = spec.params["truth"]
        verdict = decoded.answer
        classical_worst = 2 ** (n_bits - 1) + 1
        correct = verdict == truth

        return FinalResult(
            answer=verdict,
            answer_label=decoded.answer_label,
            confidence=decoded.confidence,
            verified=correct,
            verification_note=(
                f"Klasik doğrulama: gizli fonksiyon gerçekten {truth}. Kuantum sonucu "
                f"{'doğru' if correct else 'yanlış'} çıktı. Bu karşılaştırmayı sadece "
                "simülasyonda yapabiliyoruz, çünkü fonksiyonu biz seçtik."
            ),
            classical_usage=(
                f"Klasik program, {classical_worst} sorgu yerine 1 sorgu harcadı ve sonucu "
                f"'{verdict}' olarak bir değişkene yazdı. Gerçek bir sistemde bu değişken, "
                "bir sonraki karar dalını belirlerdi."
            ),
            details={
                "verdict": verdict,
                "ground_truth": truth,
                "oracle": spec.params["oracle"],
                "oracle_label": ORACLE_LABELS[spec.params["oracle"]],
                "quantum_queries": 1,
                "classical_worst_case_queries": classical_worst,
                "speedup_factor": classical_worst,
            },
        )
