"""Judge node — Claude Sonnet, temperature 0, strict three-axis rubric (ANLY-02..04).

Scores each Analyst-flagged candidate on the three-axis rubric (prompts/judge_system.md),
validates the axes with pydantic, and computes total + verdict deterministically in code so
the alert threshold is the single source of truth. Retries once on malformed JSON, then logs
a Judge failure and fails safe (is_verified=False, no alert).
"""

from __future__ import annotations

from pathlib import Path

import anthropic
from langsmith.wrappers import wrap_anthropic
from pydantic import BaseModel, Field, ValidationError

from state import LeakGuardState

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0.0          # deterministic scoring (ANLY-02)
MAX_TOKENS = 1024
ALERT_THRESHOLD = 8        # ANLY-04, configurable
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "judge_system.md"


class JudgeScores(BaseModel):
    target_authenticity: int = Field(ge=0, le=3)
    secret_entropy: int = Field(ge=0, le=4)
    exposure_context: int = Field(ge=0, le=3)
    audit_reasoning: str
    analyst_feedback: str = ""


def _strip_json(text: str) -> str:
    """Return the JSON object from a model reply, tolerating ```json fences / stray prose."""
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end != -1 else text


def _call_claude(system_prompt: str, user_msg: str) -> str:
    """Single Claude call; returns raw text. Isolated so tests can monkeypatch it."""
    client = wrap_anthropic(anthropic.Anthropic())
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


def judge_node(state: LeakGuardState) -> LeakGuardState:
    """Score the candidate; populate state['judge_verdict'] with axes, total, and verdict."""
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_msg = (
        f"Analyst findings:\n{state.get('analyst_reasoning') or '(none)'}\n\n"
        f"Full paste content:\n{state.get('raw_content') or ''}"
    )

    scores: JudgeScores | None = None
    for attempt in range(2):  # one retry on malformed JSON (ANLY edge case)
        sys_p = system_prompt if attempt == 0 else (
            system_prompt + "\n\nYour previous reply was not valid JSON. Return ONLY the JSON object."
        )
        try:
            scores = JudgeScores.model_validate_json(_strip_json(_call_claude(sys_p, user_msg)))
            break
        except (ValidationError, ValueError):
            scores = None

    if scores is None:
        # Malformed twice — log and fail safe. Never fire an alert on a broken verdict.
        state["judge_verdict"] = {
            "total_score": 0,
            "is_verified": False,
            "audit_reasoning": "judge failed to return valid JSON after one retry; alert skipped",
            "analyst_feedback": "",
        }
        state["error"] = "judge-malformed-json"
        print("[judge] FAILED to parse after retry -> failing safe (no alert)")
        return state

    total = scores.target_authenticity + scores.secret_entropy + scores.exposure_context
    is_verified = total >= ALERT_THRESHOLD
    state["judge_verdict"] = {
        "target_authenticity": scores.target_authenticity,
        "secret_entropy": scores.secret_entropy,
        "exposure_context": scores.exposure_context,
        "total_score": total,
        "is_verified": is_verified,
        "audit_reasoning": scores.audit_reasoning,
        "analyst_feedback": scores.analyst_feedback,
    }
    print(f"[judge] axes={scores.target_authenticity}/{scores.secret_entropy}/"
          f"{scores.exposure_context} total={total} verified={is_verified}")
    return state
