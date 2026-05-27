# ADR 0003 — Defense-in-depth redaction of alert payloads

**Status:** Accepted · **Date:** 2026-05-27

## Context

The first live Slack alert redacted the headline `Credential` field correctly (first four +
last four characters). But the Judge's `audit_reasoning` — which describes *why* it scored a
leak — quoted the credentials verbatim (the full AWS access key and the DB password), and
`alert_node` forwarded that reasoning into the Slack payload unscrubbed.

So the alert leaked the very secrets it was reporting. For a tool whose entire thesis is
"AI builders create exposure surfaces and LeakGuard watches them," an alert channel that is
itself an exposure surface is a credibility-ending bug — a reviewer reading the redacted
headline and then the verbatim secret two lines down stops trusting the tool.

## Decision

Two independent layers, because **prompts are not contracts** — an instruction reduces the
common case but cannot guarantee the model never quotes a secret:

1. **Prompt (source):** the Judge is instructed never to reproduce a secret verbatim —
   refer to each credential by type and location ("the AWS key", "the DB password").
2. **Code (guarantee):** before sending, `alert_node` scrubs the entire payload. It redacts
   every regex-triage match **plus** any 8+ character high-entropy token (mixed case and a
   digit) that appears in both the payload and the raw paste — catching secrets that triage
   missed but the Judge surfaced (e.g. a DB password only caught indirectly).

## Consequences

- **+** A secret never leaves the box even if the prompt layer fails — the code scrub is the
  hard guarantee, the prompt is the cheap common-case reduction.
- **+** Verified: the post-fix alert contains no verbatim secret (checked programmatically
  and by eye).
- **−** Small risk of over-redacting a benign high-entropy token that coincidentally appears
  in the raw paste — acceptable trade for a security tool.
- **Principle:** redact at the boundary, not at the source you control. Treat every outbound
  channel as untrusted with respect to secrets.
