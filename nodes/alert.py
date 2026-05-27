"""Alert node — Slack incoming webhook (ALRT-01..04).

Fires only for verified leaks (routed here by the conditional edge, ORCH-04). Redacts the
credential before sending — first 4 + last 4 chars only (ALRT-03 / NFR-04).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import requests

from state import LeakGuardState


def redact(secret: str) -> str:
    """Show first 4 and last 4 chars only (ALRT-03 / NFR-04)."""
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}{'*' * (len(secret) - 8)}{secret[-4:]}"


def build_payload(state: LeakGuardState) -> dict:
    """Slack message: source URL, redacted credential, severity, reasoning, timestamp (ALRT-01)."""
    verdict = state.get("judge_verdict") or {}
    hits = state.get("regex_hits") or []
    top = hits[0] if hits else {}
    cred = top.get("match", "")
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    text = (
        ":rotating_light: *LeakGuard — verified credential exposure*\n"
        f"*Source:* {state.get('url', 'n/a')}\n"
        f"*Credential:* `{redact(cred) if cred else '(none)'}` ({top.get('pattern', 'n/a')})\n"
        f"*Severity:* {verdict.get('total_score', '?')}/10\n"
        f"*Reasoning:* {verdict.get('audit_reasoning', '')}\n"
        f"*Detected:* {ts}"
    )
    return {"text": text}


def alert_node(state: LeakGuardState) -> LeakGuardState:
    """POST a redacted Slack alert for a verified leak."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")
    payload = build_payload(state)
    try:
        resp = requests.post(webhook, json=payload, timeout=10)
        resp.raise_for_status()
        state["decision"] = "verified"
        print(f"[alert] Slack alert sent (HTTP {resp.status_code})")
    except requests.RequestException as exc:
        # TODO ALRT-04 hardening: local queue + retry so a verified alert is never lost.
        state["decision"] = "alert-failed"
        state["error"] = f"slack-post-failed: {type(exc).__name__}"
        print(f"[alert] Slack POST failed: {type(exc).__name__}")
    return state
