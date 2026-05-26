"""LangGraph state machine wiring (ORCH-01).

Pipeline: Discovery -> Extraction -> Triage -> Analyst -> Judge -> [conditional] Alert.
The conditional edge from Judge routes to alert_node only when is_verified is True (ORCH-04);
otherwise the run ends silently for that paste.
"""

from __future__ import annotations

from state import LeakGuardState


def route_after_judge(state: LeakGuardState) -> str:
    """Conditional edge: alert only on a verified leak (ORCH-04)."""
    verdict = state.get("judge_verdict")
    if verdict and verdict.get("is_verified"):
        return "alert"
    return "end"


def build_graph():
    """Assemble and compile the LangGraph StateGraph.

    TODO:
      - from langgraph.graph import StateGraph, END
      - register discovery/extraction/triage/analyst/judge/alert nodes
      - add_edge through the funnel; add_conditional_edges("judge", route_after_judge)
      - return graph.compile()
    """
    raise NotImplementedError("Wire up the LangGraph StateGraph here.")


if __name__ == "__main__":
    # TODO: simple scheduler loop — run a cycle, then time.sleep(900) (DISC-02).
    raise NotImplementedError("Entry point for the scheduled pipeline run.")
