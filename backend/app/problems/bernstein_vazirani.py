"""Problem 4: Bernstein-Vazirani algoritması.

Gizli bir bit dizisi var. Kara kutu fonksiyon, verdiğiniz girdinin gizli
diziyle noktasal çarpımını (mod 2) döndürüyor. Gizli diziyi bulun.

Klasik olarak n bitlik gizli dizi için n sorgu gerekir: her sorguda tek bir
biti yalıtıp okursunuz.

Kuantum olarak tek sorgu yeter. Üstelik sonuç olasılıksal değil kesindir:
doğru cevap yüzde yüz olasılıkla gelir.

Bu algoritma, Deutsch-Jozsa'dan daha somut bir kazanç gösterir çünkü sadece
"evet ya da hayır" değil, tam bir veriyi geri getirir.
"""

from __future__ import annotations

from typing import Any

from ..core.models import FinalResult
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit
from .base import Decoded, Problem, ProblemSpec, RoutingHints, ValidationError


class BernsteinVaziraniProblem(Problem):
    id = "bernstein-vazirani"
    title = "Bernstein-Vazirani: gizli diziyi tek sorguda bul"
    category = "Algoritma"
    short_description = "Gizli bir bit dizisini tek kuantum sorgusuyla geri getir."
    description = (
        "Gizli dizi, kontrollü NOT kapılarının yerleşimi olarak bir kara kutuya gömülür. "
        "Tüm girdiler süperpozisyonda aynı anda sorulur. Gizli dizinin her biti, faz geri "
        "tepmesi yoluyla ilgili kubitin fazına yazılır. Son Hadamard katmanı bu faz bilgisini "
        "doğrudan okunabilir bitlere çevirir."
    )
    quantum_advantage = (
        "n bitlik gizli dizi için klasik n sorgu yerine 1 sorgu. Kazanç doğrusaldır, "
        "üstel değildir, ama sonuç olasılıksal değil kesindir."
    )
    classical_comparison = (
        "Klasik algoritma gizli dizinin bitlerini teker teker okur: sadece birinci biti 1 "
        "olan bir girdi sorarsanız cevap gizli dizinin birinci bitidir. n bit için n sorgu."
    )
    difficulty = "orta"
    concepts = ["faz geri tepmesi", "oracle", "Hadamard dönüşümü"]

    @property
    def default_input(self) -> dict[str, Any]:
        return {"secret": "1011"}

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "secret": {
                "type": "bitstring",
                "label": "Gizli bit dizisi",
                "max_length": 8,
                "default": "1011",
                "help": "Sadece 0 ve 1 karakterleri. Algoritma bunu bilmiyormuş gibi davranır.",
            }
        }

    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        secret = str(raw_input.get("secret", "1011")).strip()
        if not secret:
            raise ValidationError("Gizli dizi boş olamaz.")
        if any(ch not in "01" for ch in secret):
            raise ValidationError("Gizli dizi yalnızca 0 ve 1 karakterlerinden oluşmalıdır.")
        if len(secret) > 8:
            raise ValidationError("Gizli dizi en fazla 8 bit olabilir.")
        return ProblemSpec(
            problem_id=self.id,
            params={"secret": secret, "n_bits": len(secret)},
            notes=[
                f"Gizli dizi {len(secret)} bit uzunluğunda.",
                f"Klasik maliyet: {len(secret)} sorgu. Kuantum maliyet: 1 sorgu.",
            ],
        )

    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        n_bits = spec.params["n_bits"]
        secret = spec.params["secret"]
        ones = secret.count("1")
        return RoutingHints(
            n_qubits=n_bits + 1,
            shots=256,
            encoding="oracle içine CNOT yerleşimi olarak gömme",
            strategy="Hadamard sandviçi ve faz geri tepmesi",
            confidence_target=0.99,
            reasoning=[
                f"{n_bits} girdi kubiti ve 1 yardımcı kubit gerekiyor, toplam {n_bits + 1}.",
                f"Oracle içinde {ones} adet CNOT kapısı var; bu sayı gizli dizideki 1'lerin "
                "sayısına eşittir. Gerçek bir kara kutuda bu sayı görünmez, burada eğitim "
                "amacıyla açıkça söylüyoruz.",
                "Atış sayısı 256 seçildi. İdeal koşulda tek atış kesin sonuç verir, çünkü "
                "doğru cevabın olasılığı tam olarak birdir.",
                f"Klasik yöntem {n_bits} sorgu harcardı; kuantum 1 sorgu harcıyor.",
            ],
            rejected_alternatives=[
                f"Klasik bit bit okuma: {n_bits} sorguyla kesin sonuç verir ve bu boyutta "
                "daha ucuzdur. Kuantum burada prensibi göstermek için kullanılıyor.",
            ],
        )

    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        secret = spec.params["secret"]
        n_bits = spec.params["n_bits"]
        ancilla = n_bits

        circuit = Circuit(n_qubits=n_qubits, name="bernstein-vazirani")

        circuit.barrier_label("Yardımcı kubiti eksi durumuna hazırla")
        circuit.x(ancilla)
        circuit.h(ancilla)

        circuit.barrier_label("Tüm girdileri süperpozisyona sok")
        for q in range(n_bits):
            circuit.h(q)

        circuit.barrier_label("Gizli diziyi oracle olarak uygula")
        for q, bit in enumerate(secret):
            if bit == "1":
                circuit.cx(q, ancilla)

        circuit.barrier_label("Faz bilgisini okunabilir bitlere çevir")
        for q in range(n_bits):
            circuit.h(q)

        circuit.measure(*range(n_bits))
        return circuit

    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        outcome, count = self.top_outcome(raw.counts)
        confidence = self.confidence_of(raw.counts, outcome)
        total = sum(raw.counts.values())

        return Decoded(
            answer=outcome,
            answer_label=f"Gizli dizi: {outcome}",
            confidence=confidence,
            explanation=[
                f"En çok gözlenen sonuç '{outcome}', {total} atışın {count} tanesinde çıktı.",
                "İdeal koşulda bu oran yüzde yüz olur: doğru cevabın dışındaki tüm "
                "genlikler girişimle birbirini götürür.",
                (
                    "Başka sonuç gözlenmedi, yani devre gürültüsüz çalıştı."
                    if len(raw.counts) == 1
                    else f"{len(raw.counts) - 1} farklı hatalı sonuç da gözlendi. "
                    "Bunlar gürültünün doğrudan izidir."
                ),
            ],
            details={
                "recovered": outcome,
                "distribution": raw.counts,
                "unique_outcomes": len(raw.counts),
            },
        )

    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        secret = spec.params["secret"]
        n_bits = spec.params["n_bits"]
        recovered = decoded.answer
        correct = recovered == secret
        wrong_positions = [i for i, (a, b) in enumerate(zip(recovered, secret, strict=False)) if a != b]

        return FinalResult(
            answer=recovered,
            answer_label=decoded.answer_label,
            confidence=decoded.confidence,
            verified=correct,
            verification_note=(
                "Klasik doğrulama: geri getirilen dizi gizli diziyle bit bit karşılaştırıldı ve "
                "tam olarak eşleşti."
                if correct
                else f"Geri getirilen dizi hatalı. Uyuşmayan bit konumları: {wrong_positions}. "
                "Gürültü seviyesini düşürmek sonucu düzeltir."
            ),
            classical_usage=(
                f"Klasik program {n_bits} sorgu yerine 1 sorgu harcadı ve gizli diziyi bir "
                f"değişkene yazdı: '{recovered}'. Gerçek bir sistemde bu değer, bir sonraki "
                "adımın anahtarı veya adres bilgisi olurdu."
            ),
            details={
                "recovered": recovered,
                "ground_truth": secret,
                "wrong_positions": wrong_positions,
                "quantum_queries": 1,
                "classical_queries": n_bits,
                "speedup_factor": n_bits,
            },
        )
