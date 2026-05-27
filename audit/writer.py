"""Audit log writer (NFR-05).

One JSON record per processed paste, appended atomically to audit_log.jsonl (gitignored).
Redaction is applied a SECOND time here, over the serialized record (defense in depth) — no
raw credential reaches the log even if one slipped into the Analyst/Judge reasoning. The
shared file is the only contract between the pipeline and the Streamlit dashboard (DASH-04).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from nodes.alert import redact, scrub_secrets
from state import LeakGuardState

ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = ROOT / "audit_log.jsonl"
PROMPT_DIR = ROOT / "prompts"


def _prompt_hashes() -> dict:
    """sha256[:8] of each prompt file, so a record is traceable to the prompt version that made it."""
    out = {}
    for name in ("analyst_system.md", "judge_system.md"):
        path = PROMPT_DIR / name
        if path.exists():
            out[name] = hashlib.sha256(path.read_bytes()).hexdigest()[:8]
    return out


def _decision(state: LeakGuardState) -> str:
    """Final disposition for the record, derived if a node didn't set it explicitly."""
    if state.get("decision"):
        return state["decision"]
    if state.get("is_triaged_clean"):
        return "clean"
    verdict = state.get("judge_verdict") or {}
    if verdict:
        return "verified" if verdict.get("is_verified") else "rejected"
    return "error" if state.get("error") else "unknown"


def build_record(state: LeakGuardState) -> dict:
    """Audit record — pattern NAMES + a REDACTED credential snippet; raw_content is never logged."""
    verdict = state.get("judge_verdict") or {}
    hits = state.get("regex_hits") or []
    top = hits[0] if hits else {}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "url": state.get("url"),
        "decision": _decision(state),
        "regex_hit_patterns": sorted(
            {h.get("pattern") for h in hits if h.get("pattern")}
        ),
        "redacted_credential": redact(top["match"]) if top.get("match") else None,
        "analyst_flagged": state.get("analyst_flagged"),
        "analyst_reasoning": state.get("analyst_reasoning"),
        "judge_verdict": verdict or None,
        "prompt_hashes": _prompt_hashes(),
        "error": state.get("error"),
    }


def write_record(state: LeakGuardState) -> None:
    """Append one redacted JSON record for this paste. Atomic: flush + fsync."""
    line = json.dumps(build_record(state), default=str)
    line = scrub_secrets(line, state)  # defense in depth: no raw credential in the log (NFR-04)
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def audit_node(state: LeakGuardState) -> LeakGuardState:
    """Terminal node: every paste path routes here so each gets exactly one audit record."""
    write_record(state)
    return state
