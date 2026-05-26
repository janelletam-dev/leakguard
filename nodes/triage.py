"""Triage node — local regex pre-filter (TRGE-01..04).

Cheap, fast (<50ms/paste) filter. Zero hits -> exit as scanned-clean. Any hit ->
pass to the Analyst with the matched span. No LLM, no network.
"""

from __future__ import annotations

import re
import time
from collections import Counter
from datetime import datetime, timezone

from state import LeakGuardState

TRIAGE_BUDGET_MS = 50.0  # TRGE-04

# TRGE-01 pattern set. Tune aggressiveness against the seeded set (Open Question #2).
PATTERNS: dict[str, re.Pattern] = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
    "stripe_live": re.compile(r"sk_live_[0-9a-zA-Z]{24,}"),
    "slack_webhook": re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"),
    "password_kv": re.compile(r"(?i)password\s*=\s*\S+"),
    "db_host_kv": re.compile(r"(?i)db_host\s*=\s*\S+"),
    "api_key_kv": re.compile(r"(?i)api_key\s*=\s*\S+"),
    # Personal-identifier watchlist (v0.2): email-like strings (DISC-04 / TRGE-01).
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def _log(pattern_count: int, counts: Counter, duration_ms: float) -> None:
    """Emit one structured log line per call (TRGE-04 budget is TRIAGE_BUDGET_MS)."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = ", ".join(f"{name}:{n}" for name, n in counts.items()) or "-"
    over = " OVER_BUDGET" if duration_ms > TRIAGE_BUDGET_MS else ""
    print(
        f"[triage] ts={ts} pattern_count={pattern_count} "
        f"duration_ms={duration_ms:.3f} hits={summary}{over}"
    )


def triage_node(state: LeakGuardState) -> LeakGuardState:
    """Run PATTERNS over raw_content; record hits and whether the paste is clean.

    Zero hits  -> is_triaged_clean = True, regex_hits = [] (TRGE-02; exits the pipeline).
    1+ hits    -> is_triaged_clean = False, regex_hits = [{pattern, match, span}] (TRGE-03).
    """
    start = time.perf_counter()
    content = state.get("raw_content")

    if not content:  # None or empty: nothing to scan, treat as clean
        state["regex_hits"] = []
        state["is_triaged_clean"] = True
        _log(0, Counter(), (time.perf_counter() - start) * 1000.0)
        return state

    hits: list[dict] = []
    for name, pattern in PATTERNS.items():
        for m in pattern.finditer(content):
            hits.append({"pattern": name, "match": m.group(0), "span": [m.start(), m.end()]})

    duration_ms = (time.perf_counter() - start) * 1000.0
    counts = Counter(h["pattern"] for h in hits)

    state["regex_hits"] = hits
    state["is_triaged_clean"] = len(hits) == 0
    _log(len(counts), counts, duration_ms)
    return state
