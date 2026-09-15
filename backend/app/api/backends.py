"""Kuantum arka uçları ve aşama tanımları için uç noktalar."""

from __future__ import annotations

from fastapi import APIRouter

from ..core.models import STAGE_LABELS, STAGE_ORDER
from ..quantum.backends.registry import DEFAULT_BACKEND_ID, list_backends

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/backends")
async def get_backends() -> dict:
    """Arka uçların listesi.

    Henüz bağlanmamış arka uçlar da listede tutulur. Bu kasıtlıdır:
    projenin nereye gittiğini göstermek, listeyi kısa tutmaktan değerlidir.
    """
    return {
        "default": DEFAULT_BACKEND_ID,
        "backends": [b.to_dict() for b in list_backends()],
    }


@router.get("/stages")
async def get_stages() -> list[dict]:
    """Boru hattının altı aşamasının tanımı.

    Arayüz bu listeyi, iş başlamadan önce de adımları gösterebilmek için kullanır.
    """
    return [
        {
            "stage": stage.value,
            "order": index + 1,
            **STAGE_LABELS[stage],
        }
        for index, stage in enumerate(STAGE_ORDER)
    ]
