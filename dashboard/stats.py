"""Pure read-side logic for the dashboard — no Streamlit, so it's unit-testable (DASH-04).

Reads the shared audit_log.jsonl the pipeline writes; never reads anything else.
"""

from __future__ import annotations

import json
from pathlib import Path

AUDIT_LOG = Path(__file__).resolve().parent.parent / "audit_log.jsonl"


def load_records(path: Path | None = None) -> list[dict]:
    """Read the audit log, tolerating a half-written trailing line (the pipeline may be mid-write)."""
    path = path or AUDIT_LOG
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # skip a partial last line rather than crash (DASH edge case)
    return records


def summarize(records: list[dict]) -> dict:
    """DASH-02 summary counts for the current run."""
    return {
        "scanned": len(records),
        "flagged": sum(1 for r in records if r.get("regex_hit_patterns")),
        "verified": sum(1 for r in records if r.get("decision") == "verified"),
        "false_positives_caught": sum(1 for r in records if r.get("decision") == "rejected"),
    }


def verified_leaks(records: list[dict]) -> list[dict]:
    """Verified-leak records, newest first (DASH-03)."""
    return [r for r in records if r.get("decision") == "verified"][::-1]
