"""Analyst node — Claude Sonnet, recall-tuned (ANLY-01).

First of the two LLM stages. Reads the paste and flags anything credential- or
identifier-shaped (recall — see prompts/analyst_system.md). Writes analyst_flagged (bool)
and analyst_reasoning (str). Precision is the Judge's job, not the Analyst's.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
from langsmith.wrappers import wrap_anthropic
from pydantic import BaseModel, ValidationError

from state import LeakGuardState

MODEL = "claude-sonnet-4-6"
TEMPERATURE = 0.3          # warmer than the Judge — tuned for recall (ANLY-01)
MAX_TOKENS = 1024
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "analyst_system.md"


class AnalystOutput(BaseModel):
    analyst_flagged: bool
    analyst_reasoning: str


def _strip_json(text: str) -> str:
    """Return the JSON object from a model reply, tolerating ```json fences / stray prose."""
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end != -1 else text


def _call_claude(system_prompt: str, user_msg: str) -> str:
    """Single Claude call; returns raw text. Isolated so tests can monkeypatch it."""
    base = anthropic.Anthropic()
    # LangSmith stores the full prompt — which here includes raw paste content and any
    # credentials in it. Trace only when explicitly enabled, and only against synthetic
    # fixtures, never real paste data (NFR-04). LANGSMITH_TRACING=false is the real off-switch
    # (it also stops LangGraph node-state tracing); this wrap is belt-and-suspenders.
    client = wrap_anthropic(base) if os.environ.get("LANGSMITH_TRACING") == "true" else base
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


def analyst_node(state: LeakGuardState) -> LeakGuardState:
    """Recall pass: flag anything credential-shaped; write analyst_flagged + analyst_reasoning."""
    content = state.get("raw_content") or ""
    hits = state.get("regex_hits") or []
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    user_msg = (
        f"Regex triage flagged these spans:\n{json.dumps(hits, indent=2)}\n\n"
        f"Full paste content:\n{content}"
    )

    raw = _call_claude(system_prompt, user_msg)
    try:
        parsed = AnalystOutput.model_validate_json(_strip_json(raw))
        state["analyst_flagged"] = parsed.analyst_flagged
        state["analyst_reasoning"] = parsed.analyst_reasoning
    except (ValidationError, ValueError) as exc:
        # Recall-safe: never drop a possible leak on a parse failure — flag, and flag the failure.
        state["analyst_flagged"] = True
        state["analyst_reasoning"] = f"analyst output unparseable ({type(exc).__name__}); flagged by default"

    print(f"[analyst] flagged={state['analyst_flagged']}")
    return state
