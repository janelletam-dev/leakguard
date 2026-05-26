"""Analyst node — Claude Sonnet, recall-tuned (ANLY-01).

Reads the full paste and flags credentials with reasoning. Tuned for recall, not
precision — it is allowed to over-flag; the Judge is what enforces precision.
Runs warmer than the Judge. Loads its system prompt from prompts/analyst_system.md.
"""

from __future__ import annotations

from state import LeakGuardState

MODEL = "claude-sonnet-4-6"


def analyst_node(state: LeakGuardState) -> LeakGuardState:
    """Send paste + regex hits to Claude; store recall-tuned reasoning in state.

    TODO:
      - load prompts/analyst_system.md
      - call Anthropic SDK (warm temperature), handle rate limits w/ backoff
      - write analyst_output to state and to the audit log (ANLY-05)
    """
    # MOCK (Day-2 graph wiring): real Claude recall call lands in step 5.
    print("[analyst] (mock) recall pass over regex_hits")
    state["analyst_flagged"] = bool(state.get("regex_hits"))
    state["analyst_reasoning"] = "MOCK analyst output — real Claude Sonnet call lands in step 5."
    return state
