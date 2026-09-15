"""Devre ara temsili (Circuit IR - Intermediate Representation).

Bir kuantum devresi burada sade bir veri yapisidir: kac kubit var, sirayla
hangi kapilar uygulaniyor, hangi kubitler olculuyor.

Bu temsil bilerek arka uctan (backend) bagimsizdir. Ayni devre nesnesi
yerel simulatore de, ileride Qiskit uzerinden gercek donanima da verilebilir.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .gates import ALL_GATE_NAMES, CONTROLLED_GATES, GATE_DESCRIPTIONS


@dataclass(frozen=True)
class Operation:
    """Devredeki tek bir islem: bir kapinin belirli kubitlere uygulanmasi.

    qubits listesinin sirasi onemlidir: kontrollu kapilarda once kontrol
    kubitleri, en sonda hedef kubit gelir. Ornek: cx(kontrol, hedef).
    """

    name: str
    qubits: tuple[int, ...]
    params: tuple[float, ...] = ()
    label: str | None = None

    def __post_init__(self) -> None:
        key = self.name.lower()
        if key not in ALL_GATE_NAMES:
            raise ValueError(f"Bilinmeyen kapı: {self.name}")
        if not self.qubits:
            raise ValueError(f"'{self.name}' kapısı en az bir kubit ister.")
        if len(set(self.qubits)) != len(self.qubits):
            raise ValueError(f"'{self.name}' kapısında aynı kubit birden fazla kez verildi.")
        if key in CONTROLLED_GATES:
            _, n_controls = CONTROLLED_GATES[key]
            if len(self.qubits) != n_controls + 1:
                raise ValueError(
                    f"'{self.name}' kapısı {n_controls + 1} kubit bekler, "
                    f"{len(self.qubits)} verildi."
                )
        elif key == "swap" and len(self.qubits) != 2:
            raise ValueError("'swap' kapısı tam olarak 2 kubit bekler.")

    @property
    def description(self) -> str:
        return GATE_DESCRIPTIONS.get(self.name.lower(), "")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "qubits": list(self.qubits),
            "params": list(self.params),
            "label": self.label,
            "description": self.description,
        }


@dataclass
class Circuit:
    """Kuantum devresi: kubit sayisi, islem listesi ve olculecek kubitler."""

    n_qubits: int
    operations: list[Operation] = field(default_factory=list)
    measured_qubits: list[int] = field(default_factory=list)
    name: str = "circuit"

    def __post_init__(self) -> None:
        if self.n_qubits < 1:
            raise ValueError("Devre en az 1 kubit içermelidir.")

    # Devre kurma yardimcilari ------------------------------------------------

    def _check(self, *qubits: int) -> None:
        for q in qubits:
            if not 0 <= q < self.n_qubits:
                raise ValueError(
                    f"Kubit indeksi aralık dışında: {q} (0 ile {self.n_qubits - 1} arası olmalı)"
                )

    def add(self, name: str, *qubits: int, params: tuple[float, ...] = (), label: str | None = None) -> Circuit:
        self._check(*qubits)
        self.operations.append(Operation(name=name, qubits=tuple(qubits), params=params, label=label))
        return self

    def h(self, q: int) -> Circuit:
        return self.add("h", q)

    def x(self, q: int) -> Circuit:
        return self.add("x", q)

    def y(self, q: int) -> Circuit:
        return self.add("y", q)

    def z(self, q: int) -> Circuit:
        return self.add("z", q)

    def s(self, q: int) -> Circuit:
        return self.add("s", q)

    def t(self, q: int) -> Circuit:
        return self.add("t", q)

    def rx(self, theta: float, q: int) -> Circuit:
        return self.add("rx", q, params=(theta,))

    def ry(self, theta: float, q: int) -> Circuit:
        return self.add("ry", q, params=(theta,))

    def rz(self, theta: float, q: int) -> Circuit:
        return self.add("rz", q, params=(theta,))

    def cx(self, control: int, target: int) -> Circuit:
        return self.add("cx", control, target)

    def cz(self, control: int, target: int) -> Circuit:
        return self.add("cz", control, target)

    def ccx(self, c1: int, c2: int, target: int) -> Circuit:
        return self.add("ccx", c1, c2, target)

    def ccz(self, c1: int, c2: int, target: int) -> Circuit:
        return self.add("ccz", c1, c2, target)

    def swap(self, a: int, b: int) -> Circuit:
        return self.add("swap", a, b)

    def barrier_label(self, text: str) -> Circuit:
        """Gorsel ayirac: devrenin mantiksal bolumlerini arayuzde adlandirir.

        Kapi degildir, duruma dokunmaz; sadece cizim ve anlatim icindir.
        """
        self.operations.append(Operation(name="id", qubits=(0,), label=text))
        return self

    def measure(self, *qubits: int) -> Circuit:
        """Verilen kubitleri olcum listesine ekler."""
        self._check(*qubits)
        for q in qubits:
            if q not in self.measured_qubits:
                self.measured_qubits.append(q)
        return self

    def measure_all(self) -> Circuit:
        return self.measure(*range(self.n_qubits))

    # Metrikler ---------------------------------------------------------------

    @property
    def gate_count(self) -> int:
        return len(self.operations)

    @property
    def two_qubit_gate_count(self) -> int:
        """Iki ve daha cok kubitli kapi sayisi.

        Gercek donanimda hata oraninin en buyuk kaynagi bu kapilardir,
        bu yuzden ayrica sayilir.
        """
        return sum(1 for op in self.operations if len(op.qubits) > 1)

    @property
    def depth(self) -> int:
        """Devre derinligi: paralel calisabilen kapi katmanlarinin sayisi.

        Ayni anda farkli kubitlere uygulanan kapilar tek katman sayilir.
        Derinlik, devrenin donanimda ne kadar sureceginin olcusudur ve
        dekoherans (decoherence) suresiyle karsilastirilir.
        """
        layer_of_qubit = [0] * self.n_qubits
        for op in self.operations:
            if op.label is not None and op.name == "id":
                continue  # gorsel ayirac, derinlige sayilmaz
            current = max(layer_of_qubit[q] for q in op.qubits) + 1
            for q in op.qubits:
                layer_of_qubit[q] = current
        return max(layer_of_qubit) if layer_of_qubit else 0

    def copy(self) -> Circuit:
        return Circuit(
            n_qubits=self.n_qubits,
            operations=list(self.operations),
            measured_qubits=list(self.measured_qubits),
            name=self.name,
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "n_qubits": self.n_qubits,
            "operations": [op.to_dict() for op in self.operations],
            "measured_qubits": list(self.measured_qubits),
            "metrics": {
                "gate_count": self.gate_count,
                "two_qubit_gate_count": self.two_qubit_gate_count,
                "depth": self.depth,
            },
        }
