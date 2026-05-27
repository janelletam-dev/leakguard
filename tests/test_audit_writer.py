"""Audit writer tests — valid JSON, no raw credential in the log, prompt-hash versioning."""

import hashlib
import json

import audit.writer as aw
from audit.writer import build_record, write_record


def test_record_is_valid_json_and_redacted(tmp_path, monkeypatch):
    monkeypatch.setattr(aw, "AUDIT_LOG", tmp_path / "audit_log.jsonl")
    state = {
        "url": "http://localhost:8080/paste/001",
        "raw_content": "AWS_ACCESS_KEY_ID=AKIAZ7K9QW2MX4P1L3VN\nDB_PASS=Xy7$kQ9mLp2wRtVz",
        "regex_hits": [{"pattern": "aws_access_key", "match": "AKIAZ7K9QW2MX4P1L3VN", "span": [0, 20]}],
        "analyst_flagged": True,
        # secrets quoted verbatim in reasoning — the writer must scrub them out
        "analyst_reasoning": "found AWS key AKIAZ7K9QW2MX4P1L3VN and DB password Xy7$kQ9mLp2wRtVz",
        "judge_verdict": {"target_authenticity": 3, "secret_entropy": 4, "exposure_context": 3,
                          "total_score": 10, "is_verified": True,
                          "audit_reasoning": "real leak", "analyst_feedback": ""},
        "decision": "verified",
    }
    write_record(state)
    lines = (tmp_path / "audit_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])                                  # (a) valid JSON
    assert "AKIAZ7K9QW2MX4P1L3VN" not in lines[0]               # (b) no raw credential, anywhere
    assert "Xy7$kQ9mLp2wRtVz" not in lines[0]
    assert rec["regex_hit_patterns"] == ["aws_access_key"]      # pattern NAMES only, not matches
    assert rec["redacted_credential"] == "[…L3VN, len=20]"      # redacted snippet, not the raw key
    assert rec["decision"] == "verified"
    assert len(rec["prompt_hashes"]["judge_system.md"]) == 8    # (c) prompt version stamped


def test_prompt_hash_changes_with_file(tmp_path, monkeypatch):
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "analyst_system.md").write_text("v1", encoding="utf-8")
    (d / "judge_system.md").write_text("v1", encoding="utf-8")
    monkeypatch.setattr(aw, "PROMPT_DIR", d)
    h1 = aw._prompt_hashes()["judge_system.md"]
    (d / "judge_system.md").write_text("v2-changed", encoding="utf-8")
    h2 = aw._prompt_hashes()["judge_system.md"]
    assert len(h1) == 8 and h1 != h2
    assert h1 == hashlib.sha256(b"v1").hexdigest()[:8]


def test_clean_paste_logs_scanned_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(aw, "AUDIT_LOG", tmp_path / "audit_log.jsonl")
    write_record({"url": "x", "is_triaged_clean": True, "regex_hits": []})
    rec = json.loads((tmp_path / "audit_log.jsonl").read_text().splitlines()[0])
    assert rec["decision"] == "clean"
    assert rec["regex_hit_patterns"] == []
