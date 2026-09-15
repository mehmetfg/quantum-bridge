"""Problem kayıt defteri.

Yeni bir problem eklemek için tek yapılacak şey, Problem sınıfından türetip
buraya kaydetmektir. Boru hattı, arayüz ve yönlendirici hiç değişmez.
"""

from __future__ import annotations

from .base import Problem
from .bell_state import BellStateProblem
from .bernstein_vazirani import BernsteinVaziraniProblem
from .deutsch_jozsa import DeutschJozsaProblem
from .grover_search import GroverSearchProblem
from .random_bits import RandomBitsProblem

_PROBLEMS: list[Problem] = [
    RandomBitsProblem(),
    BellStateProblem(),
    DeutschJozsaProblem(),
    BernsteinVaziraniProblem(),
    GroverSearchProblem(),
]

_BY_ID: dict[str, Problem] = {p.id: p for p in _PROBLEMS}


def list_problems() -> list[Problem]:
    """Kayıtlı tüm problemleri sırasıyla döndürür."""
    return list(_PROBLEMS)


def get_problem(problem_id: str) -> Problem:
    """Kimliğe göre problemi döndürür."""
    if problem_id not in _BY_ID:
        raise KeyError(
            f"Bilinmeyen problem: {problem_id}. "
            f"Kayıtlı problemler: {', '.join(_BY_ID)}"
        )
    return _BY_ID[problem_id]
