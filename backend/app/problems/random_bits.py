"""Problem 1: Gercek rastgele sayi uretimi.

Klasik bilgisayarlar gercekten rastgele sayi uretemez. Urettikleri sey
"sozde rastgele" (pseudo-random) dizilerdir: bir baslangic degerinden
matematiksel olarak hesaplanirlar, bu yuzden baslangic degeri bilinirse
tum dizi bilinir.

Kuantum mekaniginde olcum sonucu ilkesel olarak belirsizdir. Superpozisyondaki
bir kubiti olcmek, tahmin edilemez bir bit uretir. Bu, kuantumun bugun
ticari olarak en olgun kullanimidir: kuantum rastgele sayi ureticileri
gercekten satilan urunlerdir.
"""

from __future__ import annotations

import math
from typing import Any

from ..core.models import FinalResult
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit
from .base import Decoded, Problem, ProblemSpec, RoutingHints, ValidationError

DEMO_LIST = ["Ahmet", "Beyza", "Can", "Deniz", "Elif", "Furkan", "Gizem", "Hakan"]


class RandomBitsProblem(Problem):
    id = "random-bits"
    title = "Gerçek rastgele sayı üretimi"
    category = "Rastgelelik"
    short_description = "Süperpozisyondaki kubitleri ölçerek tahmin edilemez sayılar üret."
    description = (
        "Her kubite bir Hadamard kapısı uygulanır. Kubit böylece yüzde elli sıfır, "
        "yüzde elli bir olma haline girer. Ölçüm yapıldığında sonuç belirlenir ve bu "
        "sonuç, evrendeki hiçbir hesapla önceden bilinemez. Üretilen bitler birleştirilerek "
        "sayılara çevrilir."
    )
    quantum_advantage = (
        "Rastgelelik hesaplanmaz, ölçümün kendisinden doğar. Sonucu önceden bilmenin "
        "bir yolu yoktur, çünkü bilgi ölçüm anında ortaya çıkar."
    )
    classical_comparison = (
        "Klasik bir üreteç, bir tohum değerinden (seed) formülle sayı üretir. Tohum "
        "ele geçerse tüm geçmiş ve gelecek çıktı bilinir. Güvenlik açısından kritik fark budur."
    )
    difficulty = "başlangıç"
    concepts = ["süperpozisyon", "ölçüm", "Hadamard kapısı"]

    @property
    def default_input(self) -> dict[str, Any]:
        return {"bit_count": 4, "how_many": 8}

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "bit_count": {
                "type": "integer",
                "label": "Sayı başına bit sayısı",
                "min": 1,
                "max": 8,
                "default": 4,
                "help": "Her sayı kaç bitten oluşsun. 4 bit, 0 ile 15 arası sayı demektir.",
            },
            "how_many": {
                "type": "integer",
                "label": "Kaç sayı üretilsin",
                "min": 1,
                "max": 256,
                "default": 8,
                "help": "Her sayı için devre bir kez çalıştırılır, yani bu aynı zamanda atış sayısıdır.",
            },
        }

    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        bit_count = int(raw_input.get("bit_count", 4))
        how_many = int(raw_input.get("how_many", 8))
        if not 1 <= bit_count <= 8:
            raise ValidationError("Bit sayısı 1 ile 8 arasında olmalıdır.")
        if not 1 <= how_many <= 256:
            raise ValidationError("Üretilecek sayı adedi 1 ile 256 arasında olmalıdır.")
        return ProblemSpec(
            problem_id=self.id,
            params={"bit_count": bit_count, "how_many": how_many},
            notes=[
                f"Her sayı {bit_count} bit, yani 0 ile {2 ** bit_count - 1} arasında.",
                f"Devre {how_many} kez çalıştırılacak; her çalıştırma bir sayı üretir.",
            ],
        )

    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        bit_count = spec.params["bit_count"]
        how_many = spec.params["how_many"]
        return RoutingHints(
            n_qubits=bit_count,
            shots=how_many,
            encoding="doğrudan bit eşlemesi (her kubit bir bit)",
            strategy="tam süperpozisyon ve ölçüm",
            confidence_target=0.0,
            reasoning=[
                f"Her sayı {bit_count} bit istendi, bu yüzden {bit_count} kubit yeterli.",
                f"Atış sayısı {how_many} seçildi çünkü her atış tam olarak bir sayı üretir; "
                "burada atış sayısı istatistik için değil, çıktı adedi için belirleyici.",
                "Kodlama gerekmez: kubitler ile bitler birebir eşleşir, bu en ucuz kodlamadır.",
            ],
            rejected_alternatives=[
                "Klasik sözde rastgele üreteç: çok daha hızlı ve ucuz, ama üretilen dizi "
                "tohum değerinden hesaplanabilir olduğu için gerçek rastgelelik değil.",
            ],
        )

    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        circuit = Circuit(n_qubits=n_qubits, name="rastgele-bit")
        circuit.barrier_label("Tüm kubitleri süperpozisyona sok")
        for q in range(n_qubits):
            circuit.h(q)
        circuit.measure_all()
        return circuit

    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        bit_count = spec.params["bit_count"]
        # Sayimlari tek tek orneklere geri acariz. Sira rastgele oldugu icin
        # acilis sirasi sonucu etkilemez, onemli olan degerlerin dagilimidir.
        numbers: list[int] = []
        bitstrings: list[str] = []
        for bitstring, count in raw.counts.items():
            for _ in range(count):
                numbers.append(int(bitstring, 2))
                bitstrings.append(bitstring)

        quality = self._uniformity(raw.counts, bit_count)
        return Decoded(
            answer=numbers,
            answer_label=", ".join(str(n) for n in numbers[:12])
            + ("..." if len(numbers) > 12 else ""),
            confidence=quality["score"],
            explanation=[
                f"{len(numbers)} adet sayı üretildi, her biri {bit_count} bitten oluşuyor.",
                f"Farklı değer sayısı: {len(raw.counts)}, mümkün olan {2 ** bit_count} değer.",
                quality["comment"],
                "Burada güven skoru, cevabın doğruluğu değil dağılımın düzgünlüğüdür. "
                "Rastgelelikte doğru cevap diye bir şey yoktur.",
            ],
            details={
                "numbers": numbers,
                "bitstrings": bitstrings,
                "uniformity": quality,
                "bit_count": bit_count,
            },
        )

    @staticmethod
    def _uniformity(counts: dict[str, int], bit_count: int) -> dict[str, Any]:
        """Dağılımın ne kadar düzgün olduğunu Shannon entropisi ile ölçer."""
        total = sum(counts.values())
        if total == 0:
            return {"score": 0.0, "entropy": 0.0, "max_entropy": bit_count, "comment": "Veri yok."}
        entropy = -sum(
            (c / total) * math.log2(c / total) for c in counts.values() if c > 0
        )
        max_entropy = float(bit_count)
        score = round(entropy / max_entropy, 4) if max_entropy else 1.0
        if total < 2 ** bit_count:
            comment = (
                f"Sadece {total} atış yapıldı ama {2 ** bit_count} farklı değer mümkün. "
                "Az sayıda örneklem, dağılımın düzgünlüğünü ölçmek için yetersizdir."
            )
        elif score > 0.95:
            comment = "Dağılım beklendiği gibi düzgün: hiçbir değer diğerlerine tercih edilmemiş."
        else:
            comment = (
                "Dağılım tam düzgün çıkmadı. Az atışta bu normaldir; atış sayısını "
                "artırmak dağılımı teorik değere yaklaştırır."
            )
        return {
            "score": min(score, 1.0),
            "entropy": round(entropy, 4),
            "max_entropy": max_entropy,
            "comment": comment,
        }

    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        """Klasik birleştirme: üretilen sayıları gerçek bir işe koşarız."""
        numbers: list[int] = decoded.details["numbers"]
        bit_count = spec.params["bit_count"]

        # Kullanim 1: bir listeyi kuantum rastgeleligi ile karistir.
        pool = list(DEMO_LIST)
        shuffled: list[str] = []
        cursor = list(numbers)
        while pool and cursor:
            index = cursor.pop(0) % len(pool)
            shuffled.append(pool.pop(index))

        # Kullanim 2: tek kullanimlik sifre uret.
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        token = "".join(alphabet[n % len(alphabet)] for n in numbers[:8])

        return FinalResult(
            answer=numbers,
            answer_label=f"{len(numbers)} adet {bit_count} bitlik rastgele sayı",
            confidence=decoded.confidence,
            verified=None,
            verification_note=(
                "Rastgelelik doğrulanamaz: doğru cevap diye bir şey yoktur. Yapılabilecek "
                "tek şey, dağılımın istatistiksel testlerden geçip geçmediğine bakmaktır."
            ),
            classical_usage=(
                "Üretilen sayılar klasik programda iki işe koşuldu: bir isim listesi "
                "karıştırıldı ve tek kullanımlık bir şifre üretildi. Kuantum tarafı "
                "burada sadece entropi kaynağıdır; işin kalanını klasik kod yapar."
            ),
            details={
                "numbers": numbers,
                "shuffled_list": shuffled,
                "original_list": DEMO_LIST,
                "one_time_token": token,
                "uniformity": decoded.details["uniformity"],
            },
        )
