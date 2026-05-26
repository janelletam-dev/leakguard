"""Judge node — Claude Sonnet, temperature 0, strict rubric (ANLY-02..04).

Scores each Analyst-flagged candidate on a three-axis rubric and returns strict JSON
(JudgeVerdict). Only total_score >= 8 AND is_verified triggers an alert (ANLY-04).
Loads its system prompt from prompts/judge_system.md.
"""

from __future__ import annotations

from state import LeakGuardState

MODEL = "claude-sonnet-4-6"
ALERT_THRESHOLD = 8  # configurable (ANLY-04)


def judge_node(state: LeakGuardState) -> LeakGuardState:
    """Score the candidate; populate state['judge_verdict'] (JudgeVerdict).

    TODO:
      - load prompts/judge_system.md (Target Authenticity 0-3, Secret Entropy & Validity
        0-4, Exposure Context 0-3)
      - call Anthropic SDK at temperature 0; validate JSON with pydantic
      - malformed JSON -> retry once stricter, else log Judge failure + skip alert
      - set is_verified = (total_score >= ALERT_THRESHOLD); write both to audit log
    """
    raise NotImplementedError
