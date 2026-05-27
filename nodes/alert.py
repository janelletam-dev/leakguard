"""Alert node — Slack incoming webhook (ALRT-01..04).

Fires only for verified leaks (routed here by the conditional edge, ORCH-04). Redacts every
credential before sending — both the headline field and any secret the Judge happened to quote
in its reasoning (NFR-04 / ALRT-03). Defense in depth: the Judge prompt is told not to quote
secrets, and this node scrubs them anyway in case the prompt fails (prompts are not contracts).
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone

import requests

from state import LeakGuardState

# Secret-ish run: alnum plus the punctuation common in keys / passwords / connection strings.
_SECRETISH = re.compile(r"[A-Za-z0-9$/+_=.\-]{8,}")


def redact(secret: str) -> str:
    """Mask a secret for display (ALRT-03 / NFR-04). Never reveal the head — for many keys it's
    a fixed prefix (e.g. AKIA) and carries no entropy. Show only a short tail for identifiability
    plus the length; fully mask anything too short to reveal a tail safely."""
    n = len(secret)
    if n < 8:
        return f"[redacted, len={n}]"
    return f"[…{secret[-4:]}, len={n}]"


def _high_entropy(token: str) -> bool:
    """Mixed case + at least one digit — the shape of a real secret, not a normal word."""
    return (any(c.islower() for c in token)
            and any(c.isupper() for c in token)
            and any(c.isdigit() for c in token))


def scrub_secrets(text: str, state: LeakGuardState) -> str:
    """Redact any real secret that slipped into outgoing text (NFR-04).

    Covers (a) every regex-triage match, and (b) any 8+ char high-entropy token that appears in
    both the text and the raw paste — catching secrets triage missed but the Judge quoted.
    """
    raw = state.get("raw_content") or ""
    secrets = {h["match"] for h in (state.get("regex_hits") or []) if h.get("match")}
    secrets |= {tok for tok in _SECRETISH.findall(text) if _high_entropy(tok) and tok in raw}
    for secret in sorted(secrets, key=len, reverse=True):  # longest first, avoids partial overlaps
        text = text.replace(secret, redact(secret))
    return text


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
    return {"text": scrub_secrets(text, state)}  # final defense-in-depth pass (NFR-04)


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
