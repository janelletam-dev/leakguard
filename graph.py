"""LangGraph state machine wiring (ORCH-01).

Pipeline:
    discovery -> extraction -> triage -> (clean? exit)
              -> analyst -> judge -> (verified? alert : exit)

Conditional after triage (TRGE-02): if is_triaged_clean, end; else proceed to analyst.
Conditional after judge (ORCH-04): if the verdict is_verified, route to alert; else end.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from nodes.alert import alert_node
from nodes.analyst import analyst_node
from nodes.discovery import discovery_node
from nodes.extraction import extraction_node
from nodes.judge import judge_node
from nodes.triage import triage_node
from state import LeakGuardState


def route_after_triage(state: LeakGuardState) -> str:
    """Clean pastes exit; pastes with regex hits continue to the Analyst (TRGE-02)."""
    if state.get("is_triaged_clean") is True:
        return "end"
    return "analyst"


def route_after_judge(state: LeakGuardState) -> str:
    """Verified leaks route to the alert node; everything else ends silently (ORCH-04)."""
    verdict = state.get("judge_verdict") or {}
    return "alert" if verdict.get("is_verified") else "end"


def build_graph():
    """Assemble and compile the LeakGuard pipeline as a LangGraph StateGraph."""
    graph = StateGraph(LeakGuardState)

    graph.add_node("discovery", discovery_node)
    graph.add_node("extraction", extraction_node)
    graph.add_node("triage", triage_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("judge", judge_node)
    graph.add_node("alert", alert_node)

    graph.set_entry_point("discovery")
    graph.add_edge("discovery", "extraction")
    graph.add_edge("extraction", "triage")
    graph.add_conditional_edges("triage", route_after_triage, {"analyst": "analyst", "end": END})
    graph.add_edge("analyst", "judge")
    graph.add_conditional_edges("judge", route_after_judge, {"alert": "alert", "end": END})
    graph.add_edge("alert", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    final = app.invoke({"url": "http://localhost:8080/paste/001", "keywords": ["acme", "acme.com"]})
    print("decision:", final.get("decision"))
