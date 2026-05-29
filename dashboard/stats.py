"""Pure read-side logic for the dashboard — no Streamlit, so it's unit-testable (DASH-04).

Reads the shared audit_log.jsonl the pipeline writes. When that file is absent
(the Streamlit Cloud deploy path, where no agent runs), falls back to the
committed demo snapshot at dashboard/demo_audit_log.jsonl so judges see a
representative dashboard state instead of an empty one.

Regenerate the demo snapshot after a real run:
    cp audit_log.jsonl dashboard/demo_audit_log.jsonl
"""

from __future__ import annotations

import json
from pathlib import Path

AUDIT_LOG = Path(__file__).resolve().parent.parent / "audit_log.jsonl"
DEMO_AUDIT_LOG = Path(__file__).resolve().parent / "demo_audit_log.jsonl"


def _resolve_log_path() -> tuple[Path, bool]:
    """Return (path, is_demo). Demo mode = real log absent, falling back to snapshot."""
    if AUDIT_LOG.exists():
        return AUDIT_LOG, False
    return DEMO_AUDIT_LOG, True


def is_demo_mode() -> bool:
    """True when the dashboard is reading the committed demo snapshot, not a live log.

    The app uses this to decide whether to render the "demo snapshot" banner —
    the honest disclosure that the agent does not run on this instance.
    """
    return _resolve_log_path()[1]


def load_records(path: Path | None = None) -> list[dict]:
    """Read the audit log, tolerating a half-written trailing line (the pipeline may be mid-write).

    When no path is given, falls back to the committed demo snapshot if the real
    log is missing (Streamlit Cloud deploy path — see module docstring).
    """
    if path is None:
        path, _ = _resolve_log_path()
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
