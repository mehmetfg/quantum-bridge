"""Yerel durum vektoru simulatoru arka ucu."""

from __future__ import annotations

import time
from dataclasses import asdict

from ..circuit import Circuit
from ..noise import NoiseModel
from ..simulator import StateVectorSimulator
from .base import BackendInfo, RawResult


class LocalSimulatorBackend:
    """Bu projenin varsayilan arka ucu: kendi yazdigimiz simulator.

    Kasitli olarak kara kutu degildir. Her kapinin duruma ne yaptigi
    goruntulenebilir, cunku onceligimiz ogrenmektir.
    """

    id = "local-statevector"

    def __init__(self, max_qubits: int = 12) -> None:
        self._simulator = StateVectorSimulator(max_qubits=max_qubits)
        self._max_qubits = max_qubits

    @property
    def info(self) -> BackendInfo:
        return BackendInfo(
            id=self.id,
            name="Yerel durum vektörü simülatörü",
            kind="simulator",
            max_qubits=self._max_qubits,
            available=True,
            description=(
                "Klasik bilgisayarda çalışan tam simülasyon. Genlikler doğrudan "
                "hesaplandığı için sonuç kesindir ve iç durum gözlemlenebilir."
            ),
            supports_statevector=True,
            supports_noise=True,
            notes=[
                f"En fazla {self._max_qubits} kubit. Sınır bellektendir: n kubit, 2 üzeri n genlik demektir.",
                "İdeal modda hiç hata yoktur; gürültü seviyesi seçilerek gerçekçilik eklenebilir.",
                "Gerçek donanımda kuyruk bekleme süresi olur, burada sonuç anındadır.",
            ],
        )

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        seed: int | None = None,
        noise_level: str = "ideal",
        collect_snapshots: bool = False,
    ) -> RawResult:
        started = time.perf_counter()
        result = self._simulator.run(
            circuit,
            shots=shots,
            seed=seed,
            collect_snapshots=collect_snapshots,
        )

        ideal_counts = result.counts
        noise = NoiseModel.preset(noise_level)
        n_bits = len(circuit.measured_qubits or list(range(circuit.n_qubits)))
        counts, noise_meta = noise.apply(
            ideal_counts,
            n_bits=n_bits,
            gate_count=circuit.gate_count,
            seed=seed,
        )

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        meta = dict(result.meta)
        meta.update(
            {
                "noise": noise_meta,
                "noise_level": noise_level,
                "execution_ms": round(elapsed_ms, 3),
                "ideal_counts": ideal_counts if noise_meta.get("applied") else None,
                "queue_note": (
                    "Gerçek donanımda bu aşamada iş bir kuyruğa girer ve sıranın gelmesi "
                    "dakikalar veya saatler alabilir. Simülasyonda beklemek gerekmez."
                ),
            }
        )

        return RawResult(
            counts=counts,
            shots=shots,
            backend_name=self.info.name,
            statevector=result.statevector,
            probabilities=result.probabilities,
            snapshots=[asdict(s) for s in result.snapshots],
            meta=meta,
        )
