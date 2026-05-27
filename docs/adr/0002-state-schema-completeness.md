# ADR 0002 — Every cross-node field must be declared in the state schema

**Status:** Accepted · **Date:** 2026-05-27

## Context

LeakGuard's pipeline is a LangGraph `StateGraph` typed by `LeakGuardState` (a `TypedDict`).
While wiring the graph, nodes wrote fields that were **not declared** in the schema —
`is_triaged_clean` (triage), `analyst_flagged` / `analyst_reasoning` (analyst).

LangGraph only propagates channels that are declared in the state schema. Undeclared keys
are **silently dropped** between nodes — no error, no warning. The effect was subtle and
dangerous: `route_after_triage` read `is_triaged_clean`, but the value never arrived, so it
saw `None` (falsy) and routed every paste to the Analyst. It *appeared* correct because the
test fixture was a real leak (which should proceed anyway) — but a genuinely clean paste
would have mis-routed past the triage exit. A silent routing bug, not a loud crash.

## Decision

Every field that any node writes to the state **must** be declared in `LeakGuardState`.
Added `is_triaged_clean`, `analyst_flagged`, `analyst_reasoning`. The schema is the contract
between nodes; if it isn't in the schema, it does not cross a node boundary.

## Consequences

- **+** Routing is reliable and deterministic; conditional edges see the values nodes write.
- **+** The state schema doubles as documentation of the inter-node contract.
- **−** Contributors must remember to declare any new cross-node field (cheap discipline,
  enforced by code review).
- **Lesson:** in LangGraph an undeclared channel is *silent data loss*, not a failure — the
  worst kind of bug. Verify state propagation by asserting on the values, not just by
  watching the path execute.
