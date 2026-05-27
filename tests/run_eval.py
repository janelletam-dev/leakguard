"""Seeded eval runner (PRD section 10).

Scores the 20 seeded fixtures through triage -> analyst -> judge and reports precision /
recall against tests/seeded_pastes/manifest.yaml. Reads fixtures directly (no discovery /
extraction / Slack), so it exercises the *decision* path, not the network.

Run (after `source .env`):  python tests/run_eval.py
Cost: ~2 real Claude calls per fixture that passes triage. Does NOT post to Slack.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from nodes.analyst import analyst_node       # noqa: E402
from nodes.judge import judge_node           # noqa: E402
from nodes.triage import triage_node         # noqa: E402

PASTES = ROOT / "tests" / "seeded_pastes"


def decide(content: str) -> dict:
    """Run a fixture through triage -> analyst -> judge; return whether it would alert."""
    state = {"url": "seed://eval", "raw_content": content}
    triage_node(state)
    if state.get("is_triaged_clean"):
        return {"alerted": False, "stage": "triage-clean", "score": None}
    analyst_node(state)
    judge_node(state)
    verdict = state.get("judge_verdict") or {}
    return {"alerted": bool(verdict.get("is_verified")), "stage": "judged",
            "score": verdict.get("total_score")}


def main() -> int:
    seeds = yaml.safe_load((PASTES / "manifest.yaml").read_text())["seeds"]
    tp = fp = tn = fn = 0
    print(f"{'id':<9} {'expect':<7} {'got':<6} {'score':<6} {'stage':<13} result")
    for entry in seeds:
        content = (PASTES / f"{entry['id']}.html").read_text(encoding="utf-8")
        expect = entry["expect_alert"]
        r = decide(content)
        got = r["alerted"]
        if expect and got:
            tp += 1
        elif expect and not got:
            fn += 1
        elif not expect and got:
            fp += 1
        else:
            tn += 1
        print(f"{entry['id']:<9} {str(expect):<7} {str(got):<6} {str(r['score']):<6} "
              f"{r['stage']:<13} {'PASS' if got == expect else 'FAIL'}")

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    print(f"\nTP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"precision={precision:.0%}  recall={recall:.0%}  "
          f"false-positive rate={fpr:.0%}  accuracy={(tp + tn) / len(seeds):.0%}")
    print("target: precision >= 80%, false-positive rate < 5%")
    return 0 if precision >= 0.8 and fpr < 0.05 else 1


if __name__ == "__main__":
    raise SystemExit(main())
