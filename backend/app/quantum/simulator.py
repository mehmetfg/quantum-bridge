"""Durum vektoru simulatoru (state-vector simulator).

n kubitlik bir sistemin durumu, 2**n adet karmasik sayidan (genlik, amplitude)
olusan bir vektordur. Her genligin karesinin buyuklugu, o sonucu olcme
olasiligini verir.

Bu yuzden simulasyon maliyeti kubit sayisiyla ustel buyur: 10 kubit 1024
genlik, 30 kubit bir milyardan fazla genlik demektir. Kuantum bilgisayarin
varlik sebebi tam olarak budur.

Bit sirasi (endianness) kurali: kubit 0 en soldaki bittir.
Ornek: 3 kubitte "011" dizgisi q0=0, q1=1, q2=1 demektir.
Bu secim, arayuzdeki devre ciziminin yukaridan asagiya sirasiyla
olcum dizgisinin soldan saga sirasini ayni tutar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .circuit import Circuit
from .gates import CONTROLLED_GATES, gate_matrix


@dataclass
class Snapshot:
    """Devrenin belirli bir adimindaki durumun fotografi (egitim icin)."""

    step: int
    after_gate: str
    qubits: list[int]
    probabilities: dict[str, float]
    note: str = ""


@dataclass
class SimulationResult:
    """Simulasyon ciktisi."""

    counts: dict[str, int]
    shots: int
    statevector: list[complex] | None = None
    probabilities: dict[str, float] = field(default_factory=dict)
    snapshots: list[Snapshot] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


class StateVectorSimulator:
    """Kucuk devreler icin tam (exact) durum vektoru simulatoru."""

    #: Bellek koruma siniri. 2**24 genlik yaklasik 256 MB eder.
    MAX_QUBITS = 14

    def __init__(self, max_qubits: int | None = None) -> None:
        self.max_qubits = max_qubits or self.MAX_QUBITS

    # Ic islemler -------------------------------------------------------------

    @staticmethod
    def _apply_single(state: np.ndarray, matrix: np.ndarray, qubit: int) -> np.ndarray:
        """Tek kubitlik kapiyi ilgili eksene uygular."""
        state = np.tensordot(matrix, state, axes=([1], [qubit]))
        return np.moveaxis(state, 0, qubit)

    @staticmethod
    def _apply_controlled(
        state: np.ndarray, matrix: np.ndarray, controls: tuple[int, ...], target: int
    ) -> np.ndarray:
        """Kontrollu kapi: sadece tum kontrol kubitleri 1 olan alt-uzaya uygular.

        Bu, dolanikligin (entanglement) dogdugu yerdir. Kontrol kubiti
        superpozisyondaysa, hedef kubit "hem cevrilmis hem cevrilmemis"
        olur ve iki kubit artik birbirinden bagimsiz tarif edilemez.
        """
        index: list[object] = [slice(None)] * state.ndim
        for c in controls:
            index[c] = 1
        sub = state[tuple(index)]

        # Kontrol eksenleri dustugu icin hedefin yeni konumunu hesapla.
        shifted_target = target - sum(1 for c in controls if c < target)
        sub = np.tensordot(matrix, sub, axes=([1], [shifted_target]))
        sub = np.moveaxis(sub, 0, shifted_target)

        state = state.copy()
        state[tuple(index)] = sub
        return state

    # Genel arayuz ------------------------------------------------------------

    def simulate_state(
        self, circuit: Circuit, collect_snapshots: bool = False
    ) -> tuple[np.ndarray, list[Snapshot]]:
        """Devreyi calistirir ve son durum vektorunu dondurur (olcum yapmadan)."""
        n = circuit.n_qubits
        if n > self.max_qubits:
            raise ValueError(
                f"Bu simülatör en fazla {self.max_qubits} kubit destekler, {n} istendi. "
                "Daha büyüğü için gerçek donanım veya tensör ağı simülatörü gerekir."
            )

        state = np.zeros((2,) * n, dtype=complex)
        state[(0,) * n] = 1.0  # baslangic durumu |00...0>

        snapshots: list[Snapshot] = []
        for step, op in enumerate(circuit.operations):
            key = op.name.lower()

            if op.label is not None and key == "id":
                if collect_snapshots:
                    snapshots.append(
                        Snapshot(
                            step=step,
                            after_gate="bölüm",
                            qubits=[],
                            probabilities=self._probabilities(state, n),
                            note=op.label,
                        )
                    )
                continue

            if key == "swap":
                a, b = op.qubits
                state = np.swapaxes(state, a, b)
            elif key in CONTROLLED_GATES:
                base_gate, n_controls = CONTROLLED_GATES[key]
                matrix = gate_matrix(base_gate)
                controls = op.qubits[:n_controls]
                target = op.qubits[n_controls]
                state = self._apply_controlled(state, matrix, controls, target)
            else:
                matrix = gate_matrix(key, list(op.params))
                state = self._apply_single(state, matrix, op.qubits[0])

            if collect_snapshots and n <= 5:
                snapshots.append(
                    Snapshot(
                        step=step,
                        after_gate=op.name,
                        qubits=list(op.qubits),
                        probabilities=self._probabilities(state, n),
                        note=op.description,
                    )
                )

        return state, snapshots

    @staticmethod
    def _probabilities(state: np.ndarray, n: int) -> dict[str, float]:
        flat = state.reshape(-1)
        probs = np.abs(flat) ** 2
        return {
            format(i, f"0{n}b"): round(float(p), 6)
            for i, p in enumerate(probs)
            if p > 1e-9
        }

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        seed: int | None = None,
        collect_snapshots: bool = False,
        return_statevector: bool = True,
    ) -> SimulationResult:
        """Devreyi calistirir ve `shots` kadar olcum ornegi toplar.

        Tek bir olcum, olasilik dagiliminin tek bir ornegidir. Dagilimi
        gorebilmek icin ayni devreyi bircok kez calistirmak gerekir;
        her tekrara "shot" (atis) denir.
        """
        n = circuit.n_qubits
        state, snapshots = self.simulate_state(circuit, collect_snapshots=collect_snapshots)
        flat = state.reshape(-1)
        probs = np.abs(flat) ** 2
        probs = probs / probs.sum()  # sayisal yuvarlama hatalarini duzelt

        measured = circuit.measured_qubits or list(range(n))
        rng = np.random.default_rng(seed)
        samples = rng.choice(len(probs), size=shots, p=probs)

        counts: dict[str, int] = {}
        # Her tam durum indeksini, sadece olculen kubitlere ait dizgiye indirger.
        full_strings = [format(i, f"0{n}b") for i in range(len(probs))]
        reduced = ["".join(full_strings[i][q] for q in measured) for i in range(len(probs))]
        for index in samples:
            key = reduced[index]
            counts[key] = counts.get(key, 0) + 1

        # Teorik dagilim (marjinal olasiliklar): gozlemi karsilastirmak icin.
        theoretical: dict[str, float] = {}
        for i, p in enumerate(probs):
            if p > 1e-12:
                theoretical[reduced[i]] = theoretical.get(reduced[i], 0.0) + float(p)

        return SimulationResult(
            counts=dict(sorted(counts.items(), key=lambda kv: -kv[1])),
            shots=shots,
            statevector=[complex(a) for a in flat] if (return_statevector and n <= 6) else None,
            probabilities={k: round(v, 6) for k, v in sorted(theoretical.items(), key=lambda kv: -kv[1])},
            snapshots=snapshots,
            meta={
                "measured_qubits": measured,
                "state_dimension": int(len(probs)),
                "seed": seed,
                "bit_order": "kubit 0 en soldaki bit",
            },
        )
