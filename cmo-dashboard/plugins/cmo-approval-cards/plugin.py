from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


PROFILE_DIR = Path(__file__).resolve().parents[2]
if str(PROFILE_DIR) not in sys.path:
    sys.path.insert(0, str(PROFILE_DIR))

from cmo_runtime.approval_cards import ApprovalCardError, DiscordApprovalReplyHandler


def _configured_approver() -> str:
    configured = [
        item.strip()
        for item in os.getenv("DISCORD_ALLOWED_USERS", "").split(",")
        if item.strip()
    ]
    if len(configured) != 1:
        raise ApprovalCardError("approval replies require exactly one DISCORD_ALLOWED_USERS entry")
    return configured[0]


def _pre_gateway_dispatch(event: Any, **_: Any) -> dict[str, str] | None:
    handler = DiscordApprovalReplyHandler(PROFILE_DIR, approver_id=_configured_approver())
    return handler.handle(event)


def register(ctx: Any) -> None:
    ctx.register_hook("pre_gateway_dispatch", _pre_gateway_dispatch)
