# ADR 0001 — Two LLMs (Analyst + Judge) instead of one

**Status:** Accepted · **Date:** 2026-05-27

## Context

Credential-leak detection on the open web has a recall/precision tension that a single
classifier handles badly:

- Tune it for **recall** and it over-alerts — every `AKIA…` string, every `password=`,
  every tutorial placeholder fires. A SOC team drowns and starts ignoring the channel.
- Tune it for **precision** and it misses the real, messy leaks — the panicked `.env`
  dump that doesn't look like a textbook example.

Most competitors run one classifier and live with whichever failure mode hurts less.

## Decision

Split the judgement into two Claude Sonnet 4.6 stages with different jobs, temperatures,
and prompts:

- **Analyst** (temp 0.3, recall-pure): flags anything credential- or identifier-shaped,
  *including* suspected placeholders and tutorial values. Its only job is to catch
  everything; it never rules anything out for "looking fake."
- **Judge** (temp 0, three-axis rubric: Target Authenticity 0–3, Secret Entropy 0–4,
  Exposure Context 0–3): enforces precision and prunes. Only a total ≥ 8 fires an alert.

## Consequences

- **+** Self-auditing: the Judge's reasoning is the audit trail for every accept/reject.
- **+** Recall and precision tune independently — the failure modes don't fight in one prompt.
- **+** The "false-positive-caught" story: the Analyst flags the AWS-docs placeholder, the
  Judge rejects it on legitimate grounds. Two genuinely different signals.
- **−** ~2× the LLM cost and latency per paste (~$0.02, ~20s — well inside NFR targets).
- **Risk:** if the Analyst prompt ever drifts toward precision (e.g. "skip placeholders"),
  the Judge becomes redundant and the design collapses into *one LLM with an extra step*.
  The Analyst prompt is therefore deliberately recall-pure, and that constraint is load-bearing.
