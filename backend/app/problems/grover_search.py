"""Problem 5: Grover arama algoritması.

Sırasız bir listede aradığınız öğeyi bulmak istiyorsunuz. Liste sıralı
olmadığı için klasik olarak yapabileceğiniz tek şey tek tek bakmaktır:
N öğe için ortalama N bölü 2, en kötü durumda N deneme.

Grover algoritması bunu yaklaşık karekök N denemeye indirir. Bir milyon
kayıtlı bir listede klasik yarım milyon deneme yerine bin deneme demektir.

Kazanç üstel değil karesel (quadratic) olduğu için Shor'un faktörleme
algoritması kadar çarpıcı değildir. Buna karşılık çok daha geniş bir problem
ailesine uygulanabilir: kısıt tatmini, optimizasyon, veritabanı araması.

Çalışma mantığı iki adımın tekrarıdır:
1. Oracle: doğru cevabın işaretini çevirir (görünmez bir işaret koyar).
2. Yayıcı (diffuser): ortalamaya göre yansıtır, işaretli olanın genliğini büyütür.

Bu tekrara "genlik yükseltme" (amplitude amplification) denir. Önemli ayrıntı:
gereğinden fazla tekrar başarıyı düşürür, çünkü genlik hedefi aşıp geri döner.
"""

from __future__ import annotations

import math
from typing import Any

from ..core.models import FinalResult
from ..quantum.backends.base import RawResult
from ..quantum.circuit import Circuit
from .base import Decoded, Problem, ProblemSpec, RoutingHints, ValidationError

DEFAULT_ITEMS = ["elma", "armut", "kiraz", "muz", "üzüm", "incir", "kayısı", "erik"]

#: 3 kubit, 8 öğe. Üstü için çok kontrollü kapının ayrıştırılması gerekir.
MAX_QUBITS = 3


class GroverSearchProblem(Problem):
    id = "grover-search"
    title = "Grover: sırasız listede arama"
    category = "Algoritma"
    short_description = "Sırasız bir listede aradığın öğeyi karekök sayıda adımda bul."
    description = (
        "Liste öğeleri kubit dizgilerine eşlenir. Oracle, aranan öğenin genliğinin işaretini "
        "çevirir. Yayıcı adımı bu işaretli genliği büyütür, diğerlerini küçültür. Doğru "
        "sayıda tekrardan sonra aranan öğe neredeyse kesin olarak ölçülür."
    )
    quantum_advantage = (
        "N öğe için klasik ortalama N bölü 2 deneme yerine yaklaşık karekök N deneme. "
        "Kazanç karesel; büyük listelerde ciddi fark yaratır."
    )
    classical_comparison = (
        "Sırasız listede klasik algoritmanın başka seçeneği yoktur: baştan sona tarar. "
        "Liste sıralı olsaydı ikili arama zaten logaritmik olurdu ve kuantuma gerek kalmazdı."
    )
    difficulty = "ileri"
    concepts = ["genlik yükseltme", "oracle", "yayıcı", "karesel hızlanma"]

    @property
    def default_input(self) -> dict[str, Any]:
        return {"items": DEFAULT_ITEMS, "target": "muz", "iterations": None}

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "items": {
                "type": "string_list",
                "label": "Liste öğeleri",
                "min_items": 2,
                "max_items": 8,
                "default": DEFAULT_ITEMS,
                "help": "En fazla 8 öğe. Sekiz öğe 3 kubit demektir.",
            },
            "target": {
                "type": "select_from_items",
                "label": "Aranan öğe",
                "default": "muz",
                "help": "Algoritma bu bilgiyi doğrudan görmez; oracle içine gömülür.",
            },
            "iterations": {
                "type": "integer",
                "label": "Tekrar sayısı",
                "min": 0,
                "max": 8,
                "default": None,
                "optional": True,
                "help": (
                    "Boş bırakılırsa en iyi tekrar sayısı hesaplanır. Elle artırıp "
                    "fazla tekrarın başarıyı nasıl düşürdüğünü görebilirsiniz."
                ),
            },
        }

    def validate(self, raw_input: dict[str, Any]) -> ProblemSpec:
        items = raw_input.get("items") or DEFAULT_ITEMS
        if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
            raise ValidationError("Liste öğeleri metin dizisi olmalıdır.")
        items = [i.strip() for i in items if i.strip()]
        if not 2 <= len(items) <= 8:
            raise ValidationError("Liste 2 ile 8 arasında öğe içermelidir.")
        if len(set(items)) != len(items):
            raise ValidationError("Liste öğeleri birbirinden farklı olmalıdır.")

        target = raw_input.get("target")
        if target is None:
            target = items[0]
        if target not in items:
            raise ValidationError(f"Aranan öğe listede yok: {target}")

        n_qubits = max(1, math.ceil(math.log2(len(items))))
        if n_qubits > MAX_QUBITS:
            raise ValidationError(
                f"Bu sürüm en fazla {2 ** MAX_QUBITS} öğe destekler. Daha büyük listeler "
                "çok kontrollü kapıların ayrıştırılmasını gerektirir."
            )

        n_states = 2 ** n_qubits
        optimal = self._optimal_iterations(n_states, 1)
        iterations = raw_input.get("iterations")
        iterations = optimal if iterations in (None, "") else int(iterations)
        if not 0 <= iterations <= 8:
            raise ValidationError("Tekrar sayısı 0 ile 8 arasında olmalıdır.")

        target_index = items.index(target)
        return ProblemSpec(
            problem_id=self.id,
            params={
                "items": items,
                "target": target,
                "target_index": target_index,
                "n_qubits": n_qubits,
                "n_states": n_states,
                "iterations": iterations,
                "optimal_iterations": optimal,
            },
            notes=[
                f"{len(items)} öğe, {n_qubits} kubit ile {n_states} adres olarak kodlandı.",
                f"Aranan öğe '{target}', {target_index} numaralı adreste.",
                f"En iyi tekrar sayısı {optimal}, seçilen {iterations}.",
            ],
        )

    @staticmethod
    def _optimal_iterations(n_states: int, n_marked: int) -> int:
        """En iyi tekrar sayısı: pi bölü 4 çarpı karekök (N bölü M)."""
        if n_marked <= 0 or n_marked >= n_states:
            return 0
        return max(1, int(round(math.pi / 4 * math.sqrt(n_states / n_marked) - 0.5)))

    def routing_hints(self, spec: ProblemSpec) -> RoutingHints:
        p = spec.params
        n_states = p["n_states"]
        classical_avg = (len(p["items"]) + 1) / 2
        return RoutingHints(
            n_qubits=p["n_qubits"],
            shots=1024,
            encoding=f"adres kodlaması: {len(p['items'])} öğe, {p['n_qubits']} kubitlik ikili adres",
            strategy=f"genlik yükseltme, {p['iterations']} tekrar",
            confidence_target=0.9,
            reasoning=[
                f"{len(p['items'])} öğe için {p['n_qubits']} kubit yeterli, çünkü "
                f"{p['n_qubits']} kubit {n_states} farklı adres taşır.",
                f"En iyi tekrar sayısı {p['optimal_iterations']} olarak hesaplandı: "
                f"pi bölü 4 çarpı karekök {n_states}. Bu sayı aşılırsa başarı düşer, "
                "çünkü genlik hedefi geçip geri dönmeye başlar.",
                "Atış sayısı 1024 seçildi. Grover olasılıksal bir algoritmadır; doğru "
                "cevap en yüksek olasılıklı sonuçtur ama tek atışla garanti değildir.",
                f"Klasik ortalama {classical_avg:.1f} deneme gerekirdi; kuantum "
                f"{p['iterations']} tekrarda sonuca varıyor.",
            ],
            rejected_alternatives=[
                "Klasik doğrusal tarama: bu boyutta çok daha hızlı ve basit. Grover'ın "
                "kazancı ancak liste milyonlara çıkınca anlam kazanır.",
                "Listeyi önce sıralayıp ikili arama yapmak: sıralama maliyeti aramadan "
                "pahalıdır ve problem sırasız liste olarak tanımlanmıştır.",
            ],
        )

    def build_circuit(self, spec: ProblemSpec, n_qubits: int) -> Circuit:
        p = spec.params
        target_index = p["target_index"]
        iterations = p["iterations"]

        circuit = Circuit(n_qubits=n_qubits, name="grover")

        circuit.barrier_label("Tüm adresleri eşit olasılıkla hazırla")
        for q in range(n_qubits):
            circuit.h(q)

        for i in range(iterations):
            circuit.barrier_label(f"Tekrar {i + 1}: oracle, aranan adresin işaretini çevirir")
            self._apply_oracle(circuit, target_index, n_qubits)
            circuit.barrier_label(f"Tekrar {i + 1}: yayıcı, işaretli genliği büyütür")
            self._apply_diffuser(circuit, n_qubits)

        circuit.measure_all()
        return circuit

    @classmethod
    def _apply_oracle(cls, circuit: Circuit, target_index: int, n_qubits: int) -> None:
        """Aranan adresin genliğinin işaretini çevirir."""
        pattern = format(target_index, f"0{n_qubits}b")
        # Adresin 0 olan bitlerini geçici olarak 1 yap ki hepsi 1 olsun.
        for q, bit in enumerate(pattern):
            if bit == "0":
                circuit.x(q)
        cls._multi_controlled_z(circuit, n_qubits)
        for q, bit in enumerate(pattern):
            if bit == "0":
                circuit.x(q)

    @classmethod
    def _apply_diffuser(cls, circuit: Circuit, n_qubits: int) -> None:
        """Ortalamaya göre yansıtma: Grover'ın ikinci yarısı."""
        for q in range(n_qubits):
            circuit.h(q)
        for q in range(n_qubits):
            circuit.x(q)
        cls._multi_controlled_z(circuit, n_qubits)
        for q in range(n_qubits):
            circuit.x(q)
        for q in range(n_qubits):
            circuit.h(q)

    @staticmethod
    def _multi_controlled_z(circuit: Circuit, n_qubits: int) -> None:
        """Tüm kubitler 1 iken işareti çeviren kapı."""
        if n_qubits == 1:
            circuit.z(0)
        elif n_qubits == 2:
            circuit.cz(0, 1)
        elif n_qubits == 3:
            circuit.ccz(0, 1, 2)
        else:
            raise ValueError(
                f"{n_qubits} kubitlik çok kontrollü Z kapısı bu sürümde ayrıştırılmıyor."
            )

    def decode(self, raw: RawResult, spec: ProblemSpec) -> Decoded:
        p = spec.params
        items = p["items"]
        outcome, count = self.top_outcome(raw.counts)
        index = int(outcome, 2)
        confidence = self.confidence_of(raw.counts, outcome)
        total = sum(raw.counts.values())

        found = items[index] if index < len(items) else None
        ranking = [
            {
                "bitstring": bits,
                "index": int(bits, 2),
                "item": items[int(bits, 2)] if int(bits, 2) < len(items) else None,
                "count": c,
                "share": round(c / total, 4),
            }
            for bits, c in sorted(raw.counts.items(), key=lambda kv: -kv[1])
        ]

        explanation = [
            f"En çok gözlenen adres '{outcome}', yani {index} numara. "
            f"{total} atışın {count} tanesi bu adresi gösterdi.",
            f"Bu adrese karşılık gelen öğe: {found if found else 'liste dışı adres'}.",
        ]
        if found is None:
            explanation.append(
                "Liste öğe sayısı ikinin kuvveti olmadığı için bazı adresler boştur. "
                "Grover boş adresi işaretlemez ama gürültü onu öne çıkarabilir."
            )
        if p["iterations"] > p["optimal_iterations"]:
            explanation.append(
                f"Tekrar sayısı en iyi değerin ({p['optimal_iterations']}) üzerinde. "
                "Fazla tekrar genliği hedefin ötesine taşır ve başarı düşer. "
                "Bu, Grover'ın en çok şaşırtan özelliğidir: daha çok çalışmak zarar verebilir."
            )

        return Decoded(
            answer=found,
            answer_label=f"Bulunan öğe: {found}" if found else "Geçersiz adres",
            confidence=confidence,
            explanation=explanation,
            details={
                "found_item": found,
                "found_index": index,
                "bitstring": outcome,
                "ranking": ranking[:8],
                "iterations": p["iterations"],
                "optimal_iterations": p["optimal_iterations"],
            },
        )

    def merge(self, decoded: Decoded, spec: ProblemSpec) -> FinalResult:
        p = spec.params
        items = p["items"]
        target = p["target"]
        found = decoded.details["found_item"]
        correct = found == target

        classical_avg = (len(items) + 1) / 2
        quantum_steps = max(p["iterations"], 1)
        speedup = round(classical_avg / quantum_steps, 2) if quantum_steps else 0.0

        return FinalResult(
            answer=found,
            answer_label=decoded.answer_label,
            confidence=decoded.confidence,
            verified=correct,
            verification_note=(
                f"Klasik doğrulama: bulunan öğe '{found}' listede tek bir karşılaştırmayla "
                "kontrol edildi ve aranan öğeyle eşleşti. Grover'ın doğası gereği bu adım "
                "şarttır: algoritma en olası cevabı verir, kesin cevabı değil."
                if correct
                else f"Klasik doğrulama başarısız: bulunan '{found}', aranan '{target}' değil. "
                "Doğru davranış, devreyi tekrar çalıştırmaktır. Tek bir klasik karşılaştırma "
                "hatalı cevabı anında yakaladığı için bu güvenlidir."
            ),
            classical_usage=(
                f"Klasik program, kuantumdan gelen adresi listeye uyguladı ve tek bir "
                f"karşılaştırma ile doğruladı. Ortalama {classical_avg:.1f} klasik deneme "
                f"yerine {quantum_steps} kuantum tekrarı ve 1 klasik doğrulama harcandı."
            ),
            details={
                "found_item": found,
                "target": target,
                "found_index": decoded.details["found_index"],
                "target_index": p["target_index"],
                "items": items,
                "iterations": p["iterations"],
                "optimal_iterations": p["optimal_iterations"],
                "classical_average_steps": classical_avg,
                "quantum_steps": quantum_steps,
                "speedup_factor": speedup,
                "ranking": decoded.details["ranking"],
            },
        )
