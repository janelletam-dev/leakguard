"""Analyst node tests. The Claude call (_call_claude) is monkeypatched so these are
deterministic and cost nothing — real recall behaviour is checked by the live graph re-run.
"""

from pathlib import Path

import nodes.analyst as analyst_mod
from nodes.analyst import analyst_node

PASTES = Path(__file__).resolve().parent.parent / "mock_server" / "pastes"


def _content(name: str) -> str:
    return (PASTES / name).read_text(encoding="utf-8")


def test_parses_flagged_json(monkeypatch):
    monkeypatch.setattr(
        analyst_mod, "_call_claude",
        lambda s, u: '{"analyst_flagged": true, "analyst_reasoning": "AWS key + internal subdomain, panicked debug context"}',
    )
    state = {"raw_content": _content("mock-paste-001.html"), "regex_hits": []}
    analyst_node(state)
    assert state["analyst_flagged"] is True
    assert "subdomain" in state["analyst_reasoning"]


def test_parses_fenced_json_and_flags_tutorial(monkeypatch):
    # Fixture 002 is a tutorial placeholder — the recall Analyst still flags it (Judge prunes later).
    monkeypatch.setattr(
        analyst_mod, "_call_claude",
        lambda s, u: '```json\n{"analyst_flagged": true, "analyst_reasoning": "AKIA...EXAMPLE docs placeholder, tutorial context; flagged for recall"}\n```',
    )
    state = {"raw_content": _content("mock-paste-002.html"), "regex_hits": []}
    analyst_node(state)
    assert state["analyst_flagged"] is True
    assert state["analyst_reasoning"]


def test_malformed_json_defaults_recall_safe(monkeypatch):
    monkeypatch.setattr(analyst_mod, "_call_claude", lambda s, u: "sorry, I cannot comply")
    state = {"raw_content": "AKIAIOSFODNN7EXAMPLE", "regex_hits": []}
    analyst_node(state)
    assert state["analyst_flagged"] is True          # recall-safe default, never drop a possible leak
    assert "unparseable" in state["analyst_reasoning"]
