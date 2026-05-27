"""Streamlit dashboard (DASH-01..06) — read-only view over the shared audit log (DASH-04).

Run:  streamlit run dashboard/app.py
Reads only audit_log.jsonl; refreshes every few seconds (DASH-05). Presentation surface,
not a critical path (NFR-07).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from dashboard.stats import load_records, summarize, verified_leaks

REFRESH_SECONDS = 5

load_dotenv()
st.set_page_config(page_title="LeakGuard", layout="wide")
st.title("🛡️ LeakGuard — live exposure monitor")

records = load_records()
s = summarize(records)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Pastes scanned", s["scanned"])
c2.metric("Flagged by triage", s["flagged"])
c3.metric("Verified leaks", s["verified"])
c4.metric("False positives caught", s["false_positives_caught"])

st.divider()
leaks = verified_leaks(records)
st.subheader(f"🚨 Verified leaks ({len(leaks)})")
if not leaks:
    st.info("No verified leaks yet — the page refreshes every few seconds.")
for r in leaks:
    verdict = r.get("judge_verdict") or {}
    with st.container(border=True):
        st.markdown(
            f"**`{r.get('redacted_credential') or '(credential)'}`** "
            f"· {', '.join(r.get('regex_hit_patterns') or []) or 'n/a'} "
            f"· severity **{verdict.get('total_score', '?')}/10**"
        )
        st.caption(f"{r.get('url')} — {r.get('timestamp')}")
        st.write(verdict.get("audit_reasoning", ""))

time.sleep(REFRESH_SECONDS)
st.rerun()
