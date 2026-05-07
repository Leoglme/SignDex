"""Démarre l'API comme GoupixDex (reload + loop Windows safe)."""

from __future__ import annotations

import os
import sys

import uvicorn

from core.win32_asyncio import ensure_proactor_event_loop


if __name__ == "__main__":
    # Avant que uvicorn configure la loop.
    ensure_proactor_event_loop()
    loop = "asyncio" if sys.platform == "win32" else "auto"
    # Même port hôte que docker-compose (`API_PORT`, défaut 8010 → mapping vers :8000 dans le conteneur).
    port = int(os.environ.get("PORT", os.environ.get("API_PORT", "8010")))
    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=port,
        reload=True,
        loop=loop,
    )

