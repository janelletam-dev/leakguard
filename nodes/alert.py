"""Alert node — Slack incoming webhook (ALRT-01..04).

Fires only for verified leaks (routed here by the conditional edge, ORCH-04).
Redacts credentials before sending (first 4 + last 4 chars only). Never drops a
verified alert: on webhook failure, queue locally and retry with backoff.
"""

from __future__ import annotations

from state import LeakGuardState


def redact(secret: str) -> str:
    """Show first 4 and last 4 chars only (ALRT-03 / NFR-04)."""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def alert_node(state: LeakGuardState) -> LeakGuardState:
    """Post a redacted Slack alert for a verified leak.

    TODO:
      - build payload: source URL, redacted snippet, score, audit reasoning, timestamp
      - POST to SLACK_WEBHOOK_URL; non-200 -> queue + retry every 30s up to 10min (ALRT-04)
    """
    # MOCK (Day-2 graph wiring): real Slack webhook POST lands in step 7.
    print("[alert] (mock) would POST redacted alert to Slack")
    state["decision"] = "verified"
    return state
