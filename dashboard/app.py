"""Streamlit dashboard — read-only view over the shared audit log (DASH-01..06).

Runs as a separate process from the pipeline. Shares only audit_log.jsonl. No DB,
no API, no auth. Presentation surface, not critical path (NFR-07).

Run:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

AUDIT_LOG = Path(__file__).resolve().parent.parent / "audit_log.jsonl"
REFRESH_SECONDS = 5  # DASH-05


def load_records() -> list[dict]:
    """Read the most recent state of the JSONL audit log (DASH-04).

    TODO: handle a file lock held by the pipeline — retry once after 500ms, then
    fall back to the previous state with a 'refreshing' indicator (edge case).
    """
    if not AUDIT_LOG.exists():
        return []
    with AUDIT_LOG.open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def main() -> None:
    st.set_page_config(page_title="LeakGuard", layout="wide")
    st.title("LeakGuard — live exposure monitor")
    # TODO DASH-02: summary cards (scanned / flagged / verified / false positives caught)
    # TODO DASH-03: one card per verified leak (URL, redacted credential, score, reasoning, ts)
    # TODO DASH-05: st.autorefresh / rerun every REFRESH_SECONDS
    st.info("Dashboard scaffold — wire up summary cards and the verified-leak list.")


if __name__ == "__main__":
    main()
