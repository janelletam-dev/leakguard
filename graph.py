"""LangGraph state machine wiring (ORCH-01).

Pipeline (every path ends at `audit`, which writes one redacted record per paste, NFR-05):

    discovery -> extraction -> triage --clean----------------------> audit -> END
                                      \\--hits--> analyst -> judge --verified--> alert -> audit -> END
                                                                  \\--rejected----------> audit -> END
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from audit.writer import audit_node
from nodes.alert import alert_node
from nodes.analyst import analyst_node
from nodes.discovery import discovery_node
from nodes.extraction import extraction_node
from nodes.judge import judge_node
from nodes.triage import triage_node
from state import LeakGuardState

REQUIRED_ENV = [
    "ANTHROPIC_API_KEY", "BRIGHTDATA_API_KEY", "BRIGHTDATA_UNLOCKER_ZONE",
    "BRIGHTDATA_SERP_ZONE", "SLACK_WEBHOOK_URL",
]


def validate_env() -> None:
    """Fail fast with a clear message if a required key is missing (not mid-pipeline).

    Called from the entry point, never at import, so tests and the eval runner can import
    build_graph without every key present.
    """
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise SystemExit(
            f"Missing required env vars: {missing}\n"
            "Copy .env.example to .env and fill them in (or `source .env`)."
        )


def route_after_triage(state: LeakGuardState) -> str:
    """Clean pastes go straight to audit (scanned-clean); pastes with hits go to the Analyst (TRGE-02)."""
    if state.get("is_triaged_clean") is True:
        return "audit"
    return "analyst"


def route_after_judge(state: LeakGuardState) -> str:
    """Verified leaks route to alert; everything else goes straight to audit (ORCH-04)."""
    verdict = state.get("judge_verdict") or {}
    return "alert" if verdict.get("is_verified") else "audit"


def build_graph():
    """Assemble and compile the LeakGuard pipeline as a LangGraph StateGraph."""
    graph = StateGraph(LeakGuardState)

    graph.add_node("discovery", discovery_node)
    graph.add_node("extraction", extraction_node)
    graph.add_node("triage", triage_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("judge", judge_node)
    graph.add_node("alert", alert_node)
    graph.add_node("audit", audit_node)

    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "extraction")
    graph.add_edge("extraction", "triage")
    graph.add_conditional_edges("triage", route_after_triage, {"analyst": "analyst", "audit": "audit"})
    graph.add_edge("analyst", "judge")
    graph.add_conditional_edges("judge", route_after_judge, {"alert": "alert", "audit": "audit"})
    graph.add_edge("alert", "audit")
    graph.add_edge("audit", END)

    return graph.compile()


if __name__ == "__main__":
    load_dotenv()
    validate_env()
    app = build_graph()
    final = app.invoke({"url": "http://localhost:8080/paste/001", "keywords": ["acme", "acme.com"]})
    print("decision:", final.get("decision"))
