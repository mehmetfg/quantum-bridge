"""FastAPI uygulaması: Quantum Bridge arka ucu."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import backends, jobs, problems
from .api.auth import auth_status

DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]


def _allowed_origins() -> list[str]:
    extra = os.environ.get("QB_ALLOWED_ORIGINS", "")
    origins = list(DEFAULT_ORIGINS)
    origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


app = FastAPI(
    title="Quantum Bridge",
    version=__version__,
    description=(
        "Klasik bilgisayar, yapay zeka yönlendirici ve kuantum bilgisayar arasındaki "
        "köprünün eğitim amaçlı simülasyonu. Bir iş altı aşamadan geçer; yalnızca "
        "dördüncüsü kuantum tarafında çalışır."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router)
app.include_router(jobs.router)
app.include_router(backends.router)


@app.get("/api/health", tags=["system"])
async def health() -> dict:
    """Sağlık kontrolü."""
    return {"status": "ok", "version": __version__}


@app.get("/api/auth/status", tags=["system"])
async def get_auth_status() -> dict:
    """Giriş durumu.

    Şu an doğrudan giriş açık. Arayüz bu uç noktaya bakarak giriş ekranı
    gösterip göstermeyeceğine karar verir, böylece giriş özelliği
    eklendiğinde arayüz kodu değişmez.
    """
    return auth_status()
