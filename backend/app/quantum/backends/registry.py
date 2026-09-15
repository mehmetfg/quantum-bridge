"""Arka uc kayit defteri: hangi arka uclar var, hangisi kullanilabilir."""

from __future__ import annotations

from .base import BackendInfo, QuantumBackend
from .local_sim import LocalSimulatorBackend
from .qiskit_stub import IBMQuantumRuntimeBackend, QiskitAerBackend

_LOCAL = LocalSimulatorBackend()
_AER = QiskitAerBackend()
_IBM = IBMQuantumRuntimeBackend()

_BACKENDS: dict[str, QuantumBackend] = {
    _LOCAL.id: _LOCAL,
    _AER.id: _AER,
    _IBM.id: _IBM,
}

DEFAULT_BACKEND_ID = _LOCAL.id


def list_backends() -> list[BackendInfo]:
    """Tum arka uclarin tanitim kartlarini dondurur (bagli olmayanlar dahil).

    Bagli olmayanlar bilerek listede tutulur: kullaniciya projenin nereye
    gittigini gostermek, listeyi temiz tutmaktan daha degerlidir.
    """
    return [backend.info for backend in _BACKENDS.values()]


def get_backend(backend_id: str | None = None) -> QuantumBackend:
    """Kimlige gore arka ucu dondurur."""
    key = backend_id or DEFAULT_BACKEND_ID
    if key not in _BACKENDS:
        raise KeyError(f"Bilinmeyen arka uç: {key}")
    backend = _BACKENDS[key]
    if not backend.info.available:
        raise RuntimeError(
            f"'{backend.info.name}' arka ucu henüz bağlanmadı. "
            f"Şu an kullanılabilen arka uç: {_LOCAL.info.name}."
        )
    return backend
