"""Streamlit dashboard (DASH-01..06) — read-only view over the shared audit log (DASH-04).

Run:  streamlit run dashboard/app.py
Reads only audit_log.jsonl; refreshes every few seconds (DASH-05). Presentation surface,
not a critical path (NFR-07).
"""

import html
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

from dashboard.stats import is_demo_mode, load_records, summarize, verified_leaks

REFRESH_SECONDS = 5

load_dotenv()
st.set_page_config(page_title="LeakGuard", page_icon="🛡️", layout="wide")

# Restrained demo polish — alert-red accent on verified-leak cards, a severity chip, a
# monospace credential treatment, and a subtle pulsing live-refresh dot. No deps, no JS.
st.markdown(
    """
    <style>
      .lg-tagline {
        color: #5f6368;
        font-size: 0.95rem;
        margin: -8px 0 14px 0;
      }
      .lg-live-dot {
        display: inline-block;
        width: 8px; height: 8px; border-radius: 50%;
        background: #1a73e8;
        margin-right: 8px;
        animation: lg-pulse 1.4s infinite;
        vertical-align: middle;
      }
      @keyframes lg-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%      { opacity: 0.35; transform: scale(0.85); }
      }
      .lg-leak-card {
        border-left: 4px solid #d93025;
        background: #fef7f6;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 12px;
        line-height: 1.55;
      }
      .lg-cred {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 1.02rem;
        background: #fff;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #f3d3cf;
        color: #202124;
      }
      .lg-patterns { color: #5f6368; font-size: 0.92rem; }
      .lg-severity {
        display: inline-block;
        background: #d93025;
        color: #fff;
        font-weight: 600;
        padding: 2px 9px;
        border-radius: 999px;
        font-size: 0.82rem;
        margin-left: 8px;
        vertical-align: middle;
      }
      .lg-meta {
        color: #5f6368;
        font-size: 0.86rem;
        margin-top: 6px;
      }
      .lg-reasoning {
        margin-top: 10px;
        color: #202124;
      }
      .lg-demo-banner {
        background: #fff7e6;
        border-left: 4px solid #f59e0b;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 14px;
        color: #5b4209;
        font-size: 0.92rem;
      }
      .lg-demo-banner strong { color: #92400e; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ LeakGuard — live exposure monitor")
st.markdown(
    '<div class="lg-tagline">'
    '<span class="lg-live-dot"></span>'
    "watching the paste surface · two-LLM Analyst → Judge · redacted at every boundary"
    "</div>",
    unsafe_allow_html=True,
)

# Honest disclosure when this dashboard is the Streamlit Cloud deploy reading the
# committed snapshot — the agent does not run live there, and we say so on the page.
if is_demo_mode():
    st.markdown(
        '<div class="lg-demo-banner">'
        "<strong>Demo snapshot.</strong> Captured from a real LeakGuard run. "
        "The agent does not run live on this hosted instance — visiting this "
        "page does not consume Bright Data credits. To run the pipeline against "
        "live targets, clone the repo and run it locally."
        "</div>",
        unsafe_allow_html=True,
    )

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
    st.info("LeakGuard is watching. No verified leaks right now — the page refreshes every few seconds.")

for r in leaks:
    verdict = r.get("judge_verdict") or {}
    cred = html.escape(r.get("redacted_credential") or "(credential)")
    patterns = html.escape(", ".join(r.get("regex_hit_patterns") or []) or "n/a")
    severity = verdict.get("total_score", "?")
    url = html.escape(r.get("url") or "")
    ts = html.escape(r.get("timestamp") or "")
    reasoning = html.escape(verdict.get("audit_reasoning", ""))
    st.markdown(
        f'<div class="lg-leak-card">'
        f'<div><span class="lg-cred">{cred}</span> '
        f'<span class="lg-patterns">· {patterns}</span>'
        f'<span class="lg-severity">{severity}/10</span></div>'
        f'<div class="lg-meta">{url} · {ts}</div>'
        f'<div class="lg-reasoning">{reasoning}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

time.sleep(REFRESH_SECONDS)
st.rerun()
