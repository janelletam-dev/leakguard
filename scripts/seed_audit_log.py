"""Drive the 22 seeded fixtures through triage -> analyst -> judge -> write_record,
producing an audit_log.jsonl populated for the Streamlit Cloud demo snapshot.

Used to populate the dashboard with realistic records for the Devpost submission's
hosted dashboard URL. The decision chain is identical to tests/run_eval.py; the
difference is this script *also* writes one redacted audit record per fixture via
audit.writer.write_record(), so the dashboard has real data to display.

Usage (run from repo root):
    > audit_log.jsonl                # truncate first if you want a clean snapshot
    python scripts/seed_audit_log.py

Cost: ~22 fixtures x (analyst + judge) ~ $0.20-0.40 in Anthropic API.
Does NOT post to Slack and does NOT hit Bright Data — pure fixture replay.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from audit.writer import write_record         # noqa: E402
from nodes.analyst import analyst_node        # noqa: E402
from nodes.judge import judge_node            # noqa: E402
from nodes.triage import triage_node          # noqa: E402

PASTES = ROOT / "tests" / "seeded_pastes"


def main() -> int:
    load_dotenv()
    seeds = yaml.safe_load((PASTES / "manifest.yaml").read_text())["seeds"]
    print(f"Driving {len(seeds)} fixtures through triage -> analyst -> judge -> audit.")

    for entry in seeds:
        seed_id = entry["id"]
        content = (PASTES / f"{seed_id}.html").read_text(encoding="utf-8")
        # Seed url uses a sentinel so the dashboard cards make it obvious these are
        # fixture-driven, not live captures. The mock_server URLs would lie.
        state = {"url": f"seed://{seed_id}", "raw_content": content}

        triage_node(state)
        if not state.get("is_triaged_clean"):
            analyst_node(state)
            judge_node(state)

        # audit.writer._decision() derives final disposition (clean / verified /
        # rejected) from state automatically — no need to set decision explicitly.
        write_record(state)

        verdict = state.get("judge_verdict") or {}
        score = verdict.get("total_score")
        if state.get("is_triaged_clean"):
            stage = "triage-clean"
        elif verdict.get("is_verified"):
            stage = "VERIFIED"
        else:
            stage = "rejected"
        print(f"  {seed_id:<9} -> {stage:<13} score={score}")

    print("\nDone. Check audit_log.jsonl and the dashboard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
