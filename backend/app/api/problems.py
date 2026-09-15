"""Problem uç noktaları."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core.models import ProblemInfo
from ..problems.registry import get_problem, list_problems

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("", response_model=list[ProblemInfo])
async def get_problems() -> list[ProblemInfo]:
    """Kayıtlı tüm problemlerin tanıtım kartları."""
    return [p.info() for p in list_problems()]


@router.get("/{problem_id}", response_model=ProblemInfo)
async def get_problem_detail(problem_id: str) -> ProblemInfo:
    """Tek bir problemin ayrıntısı."""
    try:
        return get_problem(problem_id).info()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
