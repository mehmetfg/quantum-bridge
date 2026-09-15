"""Transpiler: devreyi donanima gondermeden once sadelestirir.

Gercek kuantum donaniminda her kapi biraz hata ekler ve her gecen
mikrosaniye durumu bozar (dekoherans, decoherence). Bu yuzden devreyi
kisaltmak dogrudan sonuc kalitesini artirir.

Burada gercek bir transpiler'in dort temel isinden ucunu sembolik olarak
yapiyoruz:

1. Sadelestirme (optimization): birbirini goturen kapilari silmek.
2. Aci birlestirme (rotation merging): ard arda donusleri tek dongude toplamak.
3. Olcum raporu (metrics): derinlik, kapi sayisi, iki kubitlik kapi sayisi.

Dorduncusu, kubit eslemesi (qubit mapping / routing), gercek cipin
baglanti haritasina bagli oldugu icin burada sadece raporlanir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .circuit import Circuit, Operation

#: Kendi tersine esit olan kapilar: iki kez uygulanirsa hicbir sey yapmaz.
SELF_INVERSE = {"h", "x", "y", "z", "cx", "cnot", "cy", "cz", "ccx", "toffoli", "ccz", "swap"}

#: Acilari toplanabilen dondurme kapilari.
MERGEABLE_ROTATIONS = {"rx", "ry", "rz", "p"}

ANGLE_EPSILON = 1e-9


@dataclass
class TranspileReport:
    """Sadelestirme raporu: arayuzde "ne kazandik" olarak gosterilir."""

    passes: list[str] = field(default_factory=list)
    removed_gates: int = 0
    merged_rotations: int = 0
    before: dict = field(default_factory=dict)
    after: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        saved = self.before.get("gate_count", 0) - self.after.get("gate_count", 0)
        ratio = (saved / self.before["gate_count"] * 100) if self.before.get("gate_count") else 0.0
        return {
            "passes": self.passes,
            "removed_gates": self.removed_gates,
            "merged_rotations": self.merged_rotations,
            "before": self.before,
            "after": self.after,
            "saved_gates": saved,
            "saved_percent": round(ratio, 1),
            "notes": self.notes,
        }


def _is_barrier(op: Operation) -> bool:
    return op.label is not None and op.name.lower() == "id"


def _metrics(circuit: Circuit) -> dict:
    return {
        "gate_count": circuit.gate_count,
        "two_qubit_gate_count": circuit.two_qubit_gate_count,
        "depth": circuit.depth,
    }


def transpile(circuit: Circuit) -> tuple[Circuit, TranspileReport]:
    """Devreyi sadelestirir; yeni devreyi ve raporu dondurur.

    Sadelestirme anlamsal olarak guvenlidir: cikan devre, girenle ayni
    durumu uretir. Sadece daha az kapi kullanir.
    """
    report = TranspileReport(before=_metrics(circuit))
    output: list[Operation] = []

    for op in circuit.operations:
        if _is_barrier(op):
            output.append(op)
            continue

        key = op.name.lower()
        # Bu kapinin dokundugu kubitlere en son dokunan islemi bul.
        last_index = None
        for j in range(len(output) - 1, -1, -1):
            prev = output[j]
            if _is_barrier(prev):
                break  # ayirac, sadelestirmeyi durdurur
            if set(prev.qubits) & set(op.qubits):
                last_index = j
                break

        if last_index is not None:
            prev = output[last_index]
            prev_key = prev.name.lower()
            same_target = prev.qubits == op.qubits

            # 1. Birbirini goturen ikili.
            if same_target and prev_key == key and key in SELF_INVERSE:
                output.pop(last_index)
                report.removed_gates += 2
                continue

            # 2. Ayni eksendeki iki donusu tek donuse indir.
            if same_target and prev_key == key and key in MERGEABLE_ROTATIONS:
                total = prev.params[0] + op.params[0]
                output.pop(last_index)
                report.merged_rotations += 1
                if abs(math.remainder(total, 2 * math.pi)) > ANGLE_EPSILON:
                    output.append(Operation(name=op.name, qubits=op.qubits, params=(total,)))
                else:
                    report.removed_gates += 2  # toplam aci sifir, ikisi de gereksiz
                continue

        # 3. Sifir acili donusu bastan at.
        if key in MERGEABLE_ROTATIONS and abs(math.remainder(op.params[0], 2 * math.pi)) < ANGLE_EPSILON:
            report.removed_gates += 1
            continue

        output.append(op)

    optimized = Circuit(
        n_qubits=circuit.n_qubits,
        operations=output,
        measured_qubits=list(circuit.measured_qubits),
        name=f"{circuit.name}_transpiled",
    )

    report.passes = [
        "kendi tersi olan kapıların iptali (self-inverse cancellation)",
        "döndürme açılarını birleştirme (rotation merging)",
        "sıfır açılı döndürmeleri atma (zero-rotation removal)",
    ]
    report.after = _metrics(optimized)
    report.notes = _build_notes(optimized, report)
    return optimized, report


def _build_notes(circuit: Circuit, report: TranspileReport) -> list[str]:
    """Rapora eğitim amaçlı açıklamalar ekler."""
    notes: list[str] = []
    saved = report.before["gate_count"] - report.after["gate_count"]
    if saved > 0:
        notes.append(
            f"{saved} kapı silindi. Gerçek donanımda her silinen kapı, daha az hata demektir."
        )
    else:
        notes.append("Devre zaten sade; silinecek gereksiz kapı bulunmadı.")

    two_q = report.after["two_qubit_gate_count"]
    notes.append(
        f"İki kubitlik kapı sayısı: {two_q}. Bugünün donanımında bu kapıların hata oranı "
        "tek kubitlik kapılardan yaklaşık on kat yüksektir, bu yüzden ayrıca takip edilir."
    )
    notes.append(
        f"Devre derinliği: {report.after['depth']}. Derinlik, devrenin donanımda ne kadar "
        "süreceğinin ölçüsüdür ve kubitin tutarlılığını koruma süresiyle yarışır."
    )
    if circuit.n_qubits <= 5:
        notes.append(
            f"{circuit.n_qubits} kubit, klasik bir bilgisayarda {2 ** circuit.n_qubits} genlik "
            "demektir. Bu boyut kolayca simüle edilir; asıl eşik yaklaşık 50 kubittir."
        )
    return notes


def routing_report(circuit: Circuit, coupling_map: list[tuple[int, int]] | None = None) -> dict:
    """Kubit eslemesi (routing) raporu.

    Gercek cipte her kubit her kubitle komsu degildir. Komsu olmayan iki
    kubit arasinda iki kubitlik kapi calistirmak icin araya SWAP kapilari
    eklenir ve devre uzar. Burada, tam bagli (all-to-all) varsayilan bir
    topoloji ile dogrusal bir zincir topolojisini karsilastirarak bu
    maliyeti sembolik olarak gosteriyoruz.
    """
    n = circuit.n_qubits
    if coupling_map is None:
        # Dogrusal zincir: 0-1, 1-2, 2-3, ...
        coupling_map = [(i, i + 1) for i in range(n - 1)]
    edges = {frozenset(pair) for pair in coupling_map}

    needed_swaps = 0
    distant_pairs: list[list[int]] = []
    for op in circuit.operations:
        if len(op.qubits) == 2 and not _is_barrier(op):
            pair = frozenset(op.qubits)
            if pair not in edges:
                needed_swaps += 1
                distant_pairs.append(sorted(op.qubits))

    return {
        "topology": "doğrusal zincir (linear chain)",
        "coupling_map": [list(pair) for pair in coupling_map],
        "non_adjacent_two_qubit_gates": needed_swaps,
        "distant_pairs": distant_pairs,
        "explanation": (
            "Simülatörde her kubit her kubitle doğrudan etkileşebilir. Gerçek çipte ise "
            "sadece komşu kubitler etkileşir; komşu olmayan çift için araya SWAP kapıları "
            "eklenir. Bu devrede komşu olmayan "
            f"{needed_swaps} adet iki kubitlik kapı var, yani doğrusal bir çipte en az "
            f"{needed_swaps} ek SWAP maliyeti çıkardı."
        ),
    }
