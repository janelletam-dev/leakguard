"""Dashboard read-side tests (pure, no Streamlit)."""

import json

from dashboard.stats import load_records, summarize, verified_leaks

_RECORDS = [
    {"url": "u1", "decision": "clean", "regex_hit_patterns": []},
    {"url": "u2", "decision": "rejected", "regex_hit_patterns": ["aws_access_key"]},
    {"url": "u3", "decision": "verified", "regex_hit_patterns": ["aws_access_key"],
     "redacted_credential": "[…L3VN, len=20]",
     "judge_verdict": {"total_score": 9, "audit_reasoning": "real leak", "is_verified": True}},
]


def test_summarize_counts():
    assert summarize(_RECORDS) == {
        "scanned": 3, "flagged": 2, "verified": 1, "false_positives_caught": 1,
    }


def test_verified_leaks_only():
    leaks = verified_leaks(_RECORDS)
    assert len(leaks) == 1 and leaks[0]["url"] == "u3"


def test_load_records_tolerates_partial_last_line(tmp_path):
    p = tmp_path / "audit_log.jsonl"
    p.write_text(json.dumps({"url": "ok", "decision": "verified"}) + "\n" + '{"url": "half-writt',
                 encoding="utf-8")
    recs = load_records(p)
    assert len(recs) == 1 and recs[0]["url"] == "ok"  # half-written tail skipped, no crash


def test_load_records_falls_back_to_demo_snapshot(tmp_path, monkeypatch):
    """Deploy path: real log absent → dashboard reads the committed demo snapshot."""
    from dashboard import stats

    fake_real = tmp_path / "missing_audit_log.jsonl"
    fake_demo = tmp_path / "demo_audit_log.jsonl"
    fake_demo.write_text(
        json.dumps({"url": "snap", "decision": "verified"}) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(stats, "AUDIT_LOG", fake_real)
    monkeypatch.setattr(stats, "DEMO_AUDIT_LOG", fake_demo)

    assert stats.is_demo_mode() is True
    recs = stats.load_records()
    assert len(recs) == 1 and recs[0]["url"] == "snap"
