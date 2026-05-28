"""Triage_node tests. Drives triage off raw_content loaded from fixtures (no server needed)."""

from pathlib import Path

from nodes.triage import PATTERNS, triage_node

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


def test_new_thursday_patterns_match_realistic_examples():
    """PEM private key, Twilio SID, GitHub PAT — additive patterns from the Thursday round."""
    p = PATTERNS
    # PEM private key — any literal BEGIN ... PRIVATE KEY header (RSA, EC, OpenSSH, plain).
    assert p["pem_private_key"].search("-----BEGIN RSA PRIVATE KEY-----\nMII...")
    assert p["pem_private_key"].search("-----BEGIN PRIVATE KEY-----")
    assert p["pem_private_key"].search("-----BEGIN OPENSSH PRIVATE KEY-----")
    assert not p["pem_private_key"].search("-----BEGIN PUBLIC KEY-----")
    # Twilio Account SID — AC + exactly 32 lowercase hex (uppercase ≠ real Twilio).
    assert p["twilio_sid"].search("AC8a3f7d2b1e9c6a4d5e0b8f1c2a7e9d4b")
    assert not p["twilio_sid"].search("ACShortString")
    assert not p["twilio_sid"].search("AC8A3F7D2B1E9C6A4D5E0B8F1C2A7E9D4B")  # uppercase rejected
    # GitHub token (PAT / OAuth / server) — gh{p,o,s,u,r}_ + 36 alphanumerics.
    assert p["github_token"].search("ghp_abcd1234efgh5678ijkl9012mnop3456qrst")
    assert p["github_token"].search("gho_abcd1234efgh5678ijkl9012mnop3456qrst")
    assert not p["github_token"].search("ghp_short")
    assert not p["github_token"].search("foo_abcd1234efgh5678ijkl9012mnop3456qrst")
