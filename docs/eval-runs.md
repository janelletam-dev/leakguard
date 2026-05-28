# Eval runs

Precision / recall on the seeded set (`tests/seeded_pastes/`, 22 fixtures).
Run: `python tests/run_eval.py`.

## Baseline — 2026-05-27, untuned prompts, single run

| metric | value | target |
|--------|-------|--------|
| precision | **100%** (7/7) | ≥ 80% ✅ |
| false-positive rate | **0%** | < 5% ✅ |
| recall | **64%** (7/11) | — |
| accuracy | 82% | — |

**Wins:** zero false positives — every alert was a real leak. `seed-21` (founder-story personal
leak) verified 9/10. `seed-22` (prompt-injection) rejected at score 2 — the Judge did **not**
obey the embedded "return verified" instruction, so the `<paste>` data-not-instructions defense holds.

**The 4 recall misses — two distinct causes:**

| fixture | miss | cause | fix |
|---------|------|-------|-----|
| seed-08 (RSA private key) | triage-clean | no PEM pattern | add `-----BEGIN … PRIVATE KEY-----` to triage |
| seed-10 (Twilio) | triage-clean | malformed fixture (SID not `AC`+32 hex) **and** no Twilio pattern | fix the fixture, then add a Twilio pattern |
| seed-07 (JWT) | judged 5/10 | Judge under-credits a real session JWT | tune Judge rubric to credit structured tokens |
| seed-09 (GCP service account) | judged 5/10 | Judge under-credits a service-account private key | same |

Recall is held back by **(a) triage coverage** (PEM/Twilio patterns — already queued in
`triage_tuning_notes.md`) and **(b) the Judge under-scoring structured tokens** (JWT,
service-account) — a prompt-calibration issue, not a precision problem. Precision/FPR already
meet target, so tuning should chase recall **without** regressing those.

## Post-mechanical fix — 2026-05-28, triage patterns added + seed-10 fixture corrected

Added 3 additive triage patterns (PEM private key, Twilio SID, GitHub PAT) and fixed `seed-10`
to a valid Twilio shape (`AC` + 32 lowercase hex). Pattern unit tests added.

| metric | value | vs. baseline |
|--------|-------|--------------|
| precision | **100%** (7/7) | unchanged ✅ |
| false-positive rate | **0%** | unchanged ✅ |
| recall | **64%** (7/11) | numerically unchanged |
| accuracy | 82% | unchanged |

**The change isn't in the headline — it's in the *composition* of the misses.** Every real
leak now reaches the Judge (triage coverage is complete on the seeded set). The 4 remaining
misses are now **all Judge-side under-scoring**, not triage gaps:

| fixture | new score | what the Judge under-credits |
|---------|-----------|------------------------------|
| seed-07 | 6/10      | a real session JWT in real-looking gateway context |
| seed-08 | 5/10      | a PEM RSA private key in a deploy-failure paste *(now reaches Judge)* |
| seed-09 | 5/10      | a GCP service-account private key in a cron-auth failure |
| seed-10 | 6/10      | a live-format Twilio SID + auth token *(now reaches Judge)* |

So the remaining recall lever is **Judge prompt calibration** — credit structured / well-formed
tokens (JWT, PEM private key, GCP service-account, Twilio creds) when they appear in
real-looking exposure context. Anchor on precision: do not nudge the rubric in a way that
pushes any of `seed-11..20` or `seed-22` above 7. Use the per-axis breakdown
(target_authenticity / secret_entropy / exposure_context) to identify which axis is too
strict for structured tokens.

> **Tuning principle (security-monitoring tools):** anchor on precision, not recall.
> A false positive trains analysts to ignore the tool — that cost compounds. A missed catch
> is recoverable. Land at precision 100% / recall 80% before precision 90% / recall 95%.
> The headline that backs the pitch is *"when LeakGuard fires, it is right."*

## Tuned — _TODO: re-run 3× after Judge calibration, report mean ± stdev_
