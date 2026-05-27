"""Alert node tests. The Slack POST is monkeypatched — no real webhook call, no message sent."""

import requests

import nodes.alert as alert_mod
from nodes.alert import alert_node, build_payload

_HIT = {"pattern": "aws_access_key", "match": "AKIAZ7K9QW2MX4P1L3VN", "span": [0, 20]}
_STATE = {
    "url": "http://localhost:8080/paste/001",
    "regex_hits": [_HIT],
    "judge_verdict": {"total_score": 9, "audit_reasoning": "real leak", "is_verified": True},
}


def test_payload_redacts_and_includes_fields():
    text = build_payload(_STATE)["text"]
    assert "L3VN" in text and "len=20" in text        # tail + length shown
    assert "AKIA" not in text                          # fixed prefix never shown
    assert "AKIAZ7K9QW2MX4P1L3VN" not in text         # full secret never leaves the box
    assert "9/10" in text
    assert "real leak" in text
    assert "paste/001" in text


def test_alert_node_posts_and_sets_decision(monkeypatch):
    sent = {}

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            pass

    def fake_post(url, json, timeout):
        sent["url"], sent["json"] = url, json
        return FakeResp()

    monkeypatch.setattr(alert_mod.requests, "post", fake_post)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")
    state = dict(_STATE)
    alert_node(state)
    assert state["decision"] == "verified"
    assert sent["url"] == "https://hooks.slack.com/services/test"
    assert "AKIAZ7K9QW2MX4P1L3VN" not in sent["json"]["text"]


def test_alert_node_handles_post_failure(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("boom")

    monkeypatch.setattr(alert_mod.requests, "post", fake_post)
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")
    state = dict(_STATE)
    alert_node(state)
    assert state["decision"] == "alert-failed"
    assert "slack-post-failed" in state["error"]


def test_reasoning_secrets_are_scrubbed():
    # The Judge quoted two secrets verbatim: one is a regex hit, one (the DB password) is not.
    state = {
        "url": "http://localhost:8080/paste/001",
        "raw_content": "AWS_ACCESS_KEY_ID=AKIAZ7K9QW2MX4P1L3VN\nDB_PASS=Xy7$kQ9mLp2wRtVz",
        "regex_hits": [{"pattern": "aws_access_key", "match": "AKIAZ7K9QW2MX4P1L3VN", "span": [0, 20]}],
        "judge_verdict": {
            "total_score": 10,
            "audit_reasoning": "AWS key 'AKIAZ7K9QW2MX4P1L3VN' and DB password 'Xy7$kQ9mLp2wRtVz' are both high-entropy.",
        },
    }
    text = build_payload(state)["text"]
    assert "AKIAZ7K9QW2MX4P1L3VN" not in text   # regex-hit secret scrubbed
    assert "Xy7$kQ9mLp2wRtVz" not in text       # high-entropy secret triage missed — also scrubbed
    assert "L3VN" in text and "RtVz" in text     # redacted tails still present
