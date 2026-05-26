"""Smoke tests for the scaffold. Expand into the seeded 20-paste precision set
(10 real-looking leaks, 10 tutorial decoys) — Success Metrics, PRD section 10.
"""

from nodes.alert import redact
from nodes.triage import PATTERNS


def test_redact_shows_first_and_last_four():
    assert redact("AKIAZ7K9QW2MX4P1L3VN") == "AKIA************L3VN"
    assert redact("short") == "*****"


def test_aws_pattern_matches_real_but_not_garbage():
    assert PATTERNS["aws_access_key"].search("AKIAZ7K9QW2MX4P1L3VN")
    assert not PATTERNS["aws_access_key"].search("AKIA-too-short")


# TODO: load mock_server/pastes/*.html and assert the funnel verifies 001, rejects 002.
