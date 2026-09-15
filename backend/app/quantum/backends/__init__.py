"""Kuantum arka uclari (backends): isin gercekte nerede calistigi.

Bugun: yerel simulator.
Yarin: Qiskit Aer (yerel, gurultulu) ve IBM Quantum Runtime (gercek cip).

Hepsi ayni `QuantumBackend` arayuzunu uygular, bu yuzden boru hattinin
(pipeline) geri kalani hangi arka ucun kullanildigini bilmek zorunda degildir.
"""

from .base import BackendInfo, QuantumBackend, RawResult
from .local_sim import LocalSimulatorBackend
from .registry import get_backend, list_backends

__all__ = [
    "BackendInfo",
    "QuantumBackend",
    "RawResult",
    "LocalSimulatorBackend",
    "get_backend",
    "list_backends",
]
