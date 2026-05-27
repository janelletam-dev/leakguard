"""Judge node tests. The Claude call (_call_claude) is monkeypatched — deterministic, no cost.
Real scoring on the fixtures is checked by the live graph re-run at the step-6 checkpoint.
"""

import nodes.judge as judge_mod
from nodes.judge import judge_node


def _fixed(reply):
    return lambda s, u: reply


def test_verifies_high_score(monkeypatch):
    monkeypatch.setattr(judge_mod, "_call_claude", _fixed(
        '{"target_authenticity":3,"secret_entropy":4,"exposure_context":2,'
        '"audit_reasoning":"internal subdomain + live-entropy AWS key in panic context",'
        '"analyst_feedback":"good catch"}'))
    state = {"raw_content": "x", "analyst_reasoning": "y"}
    judge_node(state)
    v = state["judge_verdict"]
    assert v["total_score"] == 9
    assert v["is_verified"] is True
    assert (v["target_authenticity"], v["secret_entropy"], v["exposure_context"]) == (3, 4, 2)


def test_rejects_low_score(monkeypatch):
    monkeypatch.setattr(judge_mod, "_call_claude", _fixed(
        '{"target_authenticity":1,"secret_entropy":0,"exposure_context":0,'
        '"audit_reasoning":"AWS docs placeholder in tutorial context","analyst_feedback":"placeholder"}'))
    state = {"raw_content": "x", "analyst_reasoning": "y"}
    judge_node(state)
    v = state["judge_verdict"]
    assert v["total_score"] == 1
    assert v["is_verified"] is False


def test_threshold_boundary_is_eight(monkeypatch):
    monkeypatch.setattr(judge_mod, "_call_claude", _fixed(
        '{"target_authenticity":3,"secret_entropy":3,"exposure_context":2,'
        '"audit_reasoning":"borderline","analyst_feedback":""}'))
    state = {}
    judge_node(state)
    assert state["judge_verdict"]["total_score"] == 8
    assert state["judge_verdict"]["is_verified"] is True


def test_malformed_json_fails_safe(monkeypatch):
    monkeypatch.setattr(judge_mod, "_call_claude", _fixed("I cannot produce JSON for this"))
    state = {}
    judge_node(state)
    assert state["judge_verdict"]["is_verified"] is False     # never fire on a broken verdict
    assert state.get("error") == "judge-malformed-json"
