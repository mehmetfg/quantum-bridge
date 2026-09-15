"""Klasik ön işleme: girdiyi doğrula ve iç biçime çevir.

Bu adım ucuz görünür ama kritiktir. Gerçek donanımda hatalı bir iş
göndermek kuyrukta beklemek, çalışma süresi harcamak ve çoğu zaman ücret
ödemek demektir. Doğrulama bu yüzden en başta, en ucuz yerde yapılır.
"""

from __future__ import annotations

from typing import Any

from ..problems.base import Problem, ProblemSpec, ValidationError


def prepare(problem: Problem, raw_input: dict[str, Any]) -> tuple[ProblemSpec, list[str]]:
    """Kullanıcı girdisini doğrulanmış problem tanımına çevirir."""
    merged = dict(problem.default_input)
    merged.update({k: v for k, v in (raw_input or {}).items() if v is not None})

    spec = problem.validate(merged)

    details = [
        f"Problem: {problem.title}",
        f"Girdi doğrulandı: {_summarize(spec.params)}",
        *spec.notes,
    ]
    return spec, details


def _summarize(params: dict[str, Any]) -> str:
    """Parametreleri kısa ve okunabilir bir satıra indirir."""
    parts = []
    for key, value in params.items():
        if isinstance(value, list):
            shown = ", ".join(str(v) for v in value[:4])
            suffix = "..." if len(value) > 4 else ""
            parts.append(f"{key}=[{shown}{suffix}]")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts)


__all__ = ["prepare", "ValidationError"]
