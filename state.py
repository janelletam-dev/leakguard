"""Typed pipeline state shared across all LangGraph nodes (ORCH-02).

Each node receives and returns a LeakGuardState. No implicit globals.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class JudgeVerdict(TypedDict):
    """Strict JSON contract returned by the Judge node (ANLY-03)."""

    total_score: int          # 0-10, sum of the three rubric axes
    is_verified: bool         # True only when the leak is a real exposure
    audit_reasoning: str      # human-readable justification for the score
    analyst_feedback: str     # note back to the Analyst for tuning


class LeakGuardState(TypedDict, total=False):
    """State carried through Discovery -> Extraction -> Triage -> Analyst -> Judge -> Alert."""

    # --- Discovery (DISC) ---
    keywords: list[str]            # watchlist variants loaded from keywords.yaml
    candidate_urls: list[str]      # organic URLs returned by the SERP dorks

    # --- Per-paste processing ---
    url: str                       # the paste currently being processed
    raw_content: Optional[str]     # raw HTML/text from Web Unlocker
    truncated: bool                # True if content was cut to 10KB (EXTR-05)
    regex_hits: list[str]          # matched spans from the triage pre-filter (TRGE-03)

    # --- Analysis (ANLY) ---
    analyst_output: Optional[str]  # recall-tuned Analyst reasoning
    judge_verdict: Optional[JudgeVerdict]

    # --- Decision / audit (NFR-05) ---
    decision: str                  # 'verified' | 'rejected' | 'clean' | 'error'
    error: Optional[str]           # node failure detail, if any (ORCH-03)
    timestamp: str                 # ISO-8601, set when the record is written

    # --- Bookkeeping ---
    meta: dict[str, Any]           # cost tracking, retry counts, dedupe hashes, etc.
    
    #optional
    is_triaged_clean: Optional[bool]
    analyst_flagged: Optional[bool]
    analyst_reasoning: Optional[str]
