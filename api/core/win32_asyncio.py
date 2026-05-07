from __future__ import annotations

import asyncio
import sys


def ensure_proactor_event_loop() -> None:
    """
    Aligne le comportement Windows sur GoupixDex.
    Sur Windows, ProactorEventLoop évite des soucis avec subprocess + reload.
    """
    if sys.platform != "win32":
        return
    try:
        policy = asyncio.get_event_loop_policy()
        if not isinstance(policy, asyncio.WindowsProactorEventLoopPolicy):  # type: ignore[attr-defined]
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())  # type: ignore[attr-defined]
    except Exception:
        # Fallback silencieux : uvicorn peut encore fonctionner avec asyncio loop.
        return

