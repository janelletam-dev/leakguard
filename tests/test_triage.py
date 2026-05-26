"""Day-1 triage_node tests. Drives triage off raw_content loaded from the fixtures
(no server needed — triage is pure regex over state)."""

from pathlib import Path

from nodes.triage import triage_node

PASTES = Path(__file__).resolve().parent.parent / "mock_server" / "pastes"


def _content(name: str) -> str:
    return (PASTES / name).read_text(encoding="utf-8")


def test_fixture_001_leak_is_dirty():
    state = {"raw_content": _content("mock-paste-001.html")}
    triage_node(state)
    assert state["is_triaged_clean"] is False
    assert any(h["pattern"] == "aws_access_key" for h in state["regex_hits"])


def test_fixture_002_tutorial_still_matches():
    # The AKIA...EXAMPLE placeholder still matches the regex — correct behaviour.
    # The Judge catches this false positive later (Flow 3), not triage.
    state = {"raw_content": _content("mock-paste-002.html")}
    triage_node(state)
    assert state["is_triaged_clean"] is False


def test_clean_paste_has_no_hits():
    state = {"raw_content": "Just some plain English text about gardening and the weather."}
    triage_node(state)
    assert state["is_triaged_clean"] is True
    assert state["regex_hits"] == []


def test_empty_and_none_are_clean():
    for raw in ("", None):
        state = {"raw_content": raw}
        triage_node(state)
        assert state["is_triaged_clean"] is True
        assert state["regex_hits"] == []
