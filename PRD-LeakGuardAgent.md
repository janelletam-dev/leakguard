# LeakGuard Agent — Product Requirements Document

| Field    | Value                                   |
|----------|-----------------------------------------|
| Project  | LeakGuard Agent                         |
| Version  | 0.1                                     |
| Date     | 25 May 2026                             |
| Author   | Janelle D. Tamayo (Creative Stallion)   |
| Status   | Draft (Hackathon scope)                 |
| Submission Deadline | 31 May 2026 (Web Data UNLOCKED) |
| Sponsor Track | Track 3: Security & Compliance     |

---

## 1. Overview / Problem Statement

Real production credentials get leaked onto public paste sites every day. Developers paste config files asking for help. Junior engineers feed real API keys into AI coding assistants and the snippets end up screenshotted, reposted, and sitting on Pastebin for anyone to find. Existing tools like GitGuardian watch structured sources such as GitHub. The unstructured public web is largely uncovered, which is exactly where the careless leaks live.

LeakGuard is an autonomous agent that patrols paste sites, forum threads, and gist mirrors for credentials tied to a specific organisation. It runs a three-stage triage funnel that ends with a verified Slack alert, usually before the leaked key has been indexed by Google.

The bet: security teams will pay for the source coverage internal SIEMs cannot reach, and AI agents finally make it economical to monitor the messy public web at scale.

---

## 2. Goals and Non-Goals

**Goals (v1, hackathon scope):**
- Detect verified credential leaks on at least four public paste sites (Pastebin, paste.ee, ghostbin, dpaste).
- Hit better than 80% precision after the Judge node, measured on a seeded test set.
- Stay under the $250 Bright Data credit cap across the full demo run.
- Ship a 2-3 minute terminal-and-Slack demo that lands a real-time verified alert on stage.
- Use at least two Bright Data products (SERP API + Web Unlocker) to satisfy sponsor requirements.

**Non-Goals (v1):**
- A polished web dashboard. The demo is terminal logs plus Slack. No frontend gets built.
- Coverage of GitHub, GitLab, or any structured source. GitGuardian already owns that lane.
- Automated remediation. LeakGuard alerts. It does not rotate keys, lock accounts, or take down pastes.
- Multi-tenant SaaS. One configured org for the hackathon.
- Historical archive search. Only fresh paste monitoring going forward.
- A "test the live key" validator step. Legally and ethically out of scope for a hackathon submission.

---

## 3. Target Users

**Primary user: SOC analyst at a mid-size company (250-2000 employees).**
Lives in their SIEM (Splunk, Elastic, Sentinel) most of the day. Drowns in alerts. Has been burned by false positives, so they ignore tools that cry wolf. Technically strong but time-poor. Needs alerts that come with reasoning, not just a flagged URL. Manages roughly 50-200 active investigations a week.

**Secondary user: Security Engineer or CISO.**
Wants quarterly evidence of external exposure for board reporting. Needs a structured log of every flag, every Judge decision, every alert fired and rejected. Cares about ROI on tooling, not feature counts.

**Scale assumption for v1:** the agent monitors one target organisation with roughly 10-20 keyword variants (company name, internal subdomains, product codenames). Processes about 50-200 candidate pastes per day across all monitored sites.

---

## 4. Jobs to Be Done

| ID    | Job (When / I want to / So I can)                                                                                                                                  | Priority |
|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| JTBD-01 | When a developer pastes a snippet containing production credentials, I want a verified alert within 5 minutes, so I can rotate the keys before an attacker finds them. | P0       |
| JTBD-02 | When the agent flags a candidate, I want a clear severity score with audit reasoning, so I can decide in under 30 seconds whether to escalate.                       | P0       |
| JTBD-03 | When I review the weekly log, I want every flag, score, and decision recorded, so I can prove to my CISO that the tool is catching real threats.                     | P0       |
| JTBD-04 | When a paste contains a placeholder key like AKIA…EXAMPLE, I want the system to quietly reject it, so my Slack channel does not get spammed with tutorial code.       | P0       |
| JTBD-05 | When the same leak gets reposted across multiple paste sites, I want one alert, not five, so my team is not chasing the same incident in parallel.                    | P1       |
| JTBD-06 | When my SIEM detects a brute-force attempt, I want to cross-reference our public exposure log, so I can correlate the incident faster.                                | P2       |
| JTBD-07 | When I add a new product codename to monitor, I want it picked up on the next scheduled scan, so I do not need to redeploy anything.                                  | P1       |

---

## 5. Functional Requirements

### Discovery (DISC) — Bright Data SERP API

- **DISC-01** Run scheduled Google Dork queries via Bright Data SERP API. Default pattern: `site:[paste-domain] "[target-keyword]"` across the keyword list.
- **DISC-02** Default schedule is every 15 minutes. Configurable per environment.
- **DISC-03** Deduplicate URLs against a persistent processed-URLs store. A URL is processed at most once.
- **DISC-04** Maintain a YAML keyword list with company names, internal subdomains, and product codenames. Hot-reload on file change.
- **DISC-05** Cap SERP queries per cycle. If the cap is hit, the cycle ends and logs the overflow.

### Extraction (EXTR) — Bright Data Web Unlocker

- **EXTR-01** Use Bright Data Web Unlocker to fetch raw paste content. No direct HTTP fallback.
- **EXTR-02** Support Pastebin, paste.ee, ghostbin, dpaste, and one forum target (Reddit r/sysadmin as a stretch).
- **EXTR-03** Handle rate limits with exponential backoff. Maximum three retries per URL before logging the failure.
- **EXTR-04** Cache fetched paste content locally for 24 hours, keyed by URL hash, to avoid duplicate Bright Data charges.
- **EXTR-05** Truncate any paste over 10KB to the first 10KB before passing downstream. Log the truncation.

### Triage (TRGE) — Local regex pre-filter

- **TRGE-01** Run a regex pattern set against fetched content. Patterns cover: AWS keys (AKIA prefix + 16-character body), JWT structure, Stripe live keys (sk_live_), Slack webhook URLs, generic `password=`, `db_host=`, `api_key=`.
- **TRGE-02** Pastes with zero regex hits exit the pipeline. They are logged as scanned-clean.
- **TRGE-03** Pastes with at least one regex hit pass to the Analyst node along with the matched span.
- **TRGE-04** The regex pre-filter must complete in under 50ms per paste.

### Analysis (ANLY) — LangGraph two-node LLM evaluation

- **ANLY-01** Analyst node uses Claude Sonnet. It reads the full paste and flags credentials with reasoning. The Analyst is tuned for recall, not precision.
- **ANLY-02** Judge node uses Claude Sonnet with a strict three-axis rubric:
  - Target Authenticity (0-3): real corporate infrastructure such as internal subdomains or real employee emails.
  - Secret Entropy & Validity (0-4): does the credential match live entropy signatures, or is it a placeholder like AKIA…EXAMPLE.
  - Exposure Context (0-3): is the surrounding text conversational and panicked, or is it a tutorial.
- **ANLY-03** The Judge returns strict JSON: `total_score`, `is_verified`, `audit_reasoning`, `analyst_feedback`.
- **ANLY-04** Only `total_score >= 8` and `is_verified: true` triggers an alert. Threshold is configurable.
- **ANLY-05** Both Analyst and Judge outputs are written to the audit log with timestamp, paste URL, and reasoning.

### Alerting (ALRT) — Slack webhook

- **ALRT-01** Verified leaks fire a Slack webhook. Payload includes source URL, redacted credential snippet, severity score, audit reasoning, and timestamp.
- **ALRT-02** Rejected candidates are logged silently. They do not fire a notification but are retrievable from the audit log.
- **ALRT-03** Credentials are redacted before being sent to Slack. Show first four and last four characters only.
- **ALRT-04** If the Slack webhook fails, the alert is queued locally and retried with backoff. A verified alert is never lost.

### Orchestration (ORCH) — LangGraph state machine

- **ORCH-01** LangGraph wires the pipeline as Discovery → Extraction → Triage → Analyst → Judge → Conditional Alert.
- **ORCH-02** Each node receives and returns a typed `LeakGuardState` dictionary. No implicit globals.
- **ORCH-03** A failed node logs the failure and the pipeline continues for the next paste. One bad URL never halts the run.
- **ORCH-04** The conditional edge from Judge routes to `alert_node` only when `is_verified == True`. Otherwise the run ends silently for that paste.

---

## 6. Non-Functional Requirements

- **NFR-01 Latency:** End-to-end time from SERP discovery to Slack alert under 5 minutes for any single paste.
- **NFR-02 Cost:** Average cost per fully processed paste under $0.50, combining Bright Data and Anthropic API usage.
- **NFR-03 Reliability:** The pipeline survives any single-node failure. Failed nodes log and skip rather than crash the run.
- **NFR-04 Security:** No raw credentials in logs. All credentials are redacted before logging or Slack output. Bright Data and Anthropic API keys live in `.env` and never appear in code, logs, or commits.
- **NFR-05 Auditability:** Every flagged candidate has a JSON record with paste URL, regex hit, Analyst output, Judge output, final decision, and timestamp.
- **NFR-06 Budget guardrail:** The agent tracks cumulative Bright Data credit usage. At 80% of the $250 cap, it halts new discovery and logs a warning.

---

## 7. User Flows

### Flow 1: Verified leak (happy path, the demo moment)

1. Scheduled SERP query runs against `site:pastebin.com "acmecorp.internal"`.
2. Bright Data SERP API returns 50 candidate URLs.
3. Deduplication drops 47 URLs that have already been processed.
4. Web Unlocker fetches 3 new pastes successfully.
5. Regex triage flags 2 of the 3 (one has zero hits and exits cleanly).
6. Analyst flags both as containing what look like AWS credentials.
7. Judge scores the first paste 9/10 (real internal subdomain plus high-entropy AWS key). Scores the second 4/10 (placeholder string `AKIAEXAMPLE…`).
8. Pipeline fires a Slack alert for the first paste only. Slack notification appears with redacted key, score, and reasoning.
9. The full audit log shows: 1 verified, 1 rejected (false-positive caught), 1 clean.

### Flow 2: Local mock demo (the hackathon presentation)

1. Local Python HTTP server serves a static HTML paste at `http://localhost:8080/mock-paste-001.html`. Content is a seeded leak with a realistic-looking AWS key and an internal subdomain.
2. The agent runs against the mock URL list instead of live SERP results. This protects the $250 Bright Data budget during rehearsal.
3. Terminal logs show the full funnel narrowing from 50 mock URLs to 3 candidates to 1 verified leak.
4. Slack alert fires live in front of judges.
5. Total demo run takes under 2 minutes.

### Flow 3: False positive caught (the audit story)

1. Web Unlocker fetches a paste that is actually a tutorial titled "How to set up AWS CLI."
2. Regex triage flags it because the tutorial uses the literal example string `AKIAIOSFODNN7EXAMPLE`.
3. Analyst flags it as containing what could be an AWS key (recall mode).
4. Judge scores 3/10. Reasoning: "Secret matches a known AWS documentation placeholder. Surrounding text reads as tutorial content, not panicked debugging."
5. No alert fires. The rejection is logged with full Judge reasoning, which is the line you read out loud during the demo to prove the system audits itself.

---

## 8. Design and Technical Constraints

**Language and runtime:** Python 3.11.

**Core dependencies:**
- `langgraph` for orchestration.
- `anthropic` SDK for Claude Sonnet calls (Analyst and Judge).
- `requests` for Bright Data SERP API and Web Unlocker calls.
- `python-dotenv` for environment variables.
- `pydantic` for typed state and Judge JSON validation.
- `pytest` for the seeded test set.

**Sponsor infrastructure (mandatory for the track):**
- Bright Data SERP API for discovery.
- Bright Data Web Unlocker for extraction.

**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) for both Analyst and Judge nodes. Same model, different system prompts, different temperatures. Analyst runs warmer for recall. Judge runs at temperature 0 for deterministic scoring.

**Alerting:** Slack incoming webhook URL stored in `.env`.

**Deployment:** Local terminal for the hackathon. No hosting, no cron, no Docker. Scheduling is a simple Python loop with `time.sleep(900)` between cycles. Post-hackathon, the natural target is a small container on Vercel Cron or Fly.io.

**Repository structure:**
```
leakguard/
├── nodes/
│   ├── discovery.py
│   ├── extraction.py
│   ├── triage.py
│   ├── analyst.py
│   ├── judge.py
│   └── alert.py
├── prompts/
│   ├── analyst_system.md
│   └── judge_system.md
├── state.py
├── graph.py
├── mock_server/
│   └── pastes/  (HTML files for safe demo)
├── tests/
│   └── seeded_pastes/
├── .env.example
└── README.md
```

---

## 9. Edge Cases and Error Handling

| Scenario                                                              | Expected Behaviour                                                                                          |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Paste deleted between SERP discovery and Web Unlocker fetch.          | Log the 404 and skip. Do not retry.                                                                          |
| Paste larger than 10KB.                                               | Truncate to first 10KB. Log truncation in the audit record.                                                  |
| Same leak reposted to multiple paste sites within the same cycle.     | Hash the cleaned paste content. If the hash matches a verified leak from the past 7 days, suppress the duplicate alert and add the new URL to the existing record. |
| Bright Data credit at 80% of cap.                                     | Halt new discovery. Log a warning. Process pastes already in flight and exit cleanly.                        |
| Claude API rate limit hit.                                            | Exponential backoff up to 60 seconds. After three retries, log and skip the paste.                           |
| Judge returns malformed JSON.                                         | Retry once with a stricter prompt. If still malformed, log as a Judge failure and skip the alert.            |
| Slack webhook returns non-200.                                        | Queue the alert locally. Retry every 30 seconds for up to 10 minutes. Alert is never dropped.                |
| Paste contains a regex hit but is empty after fetching (rate-limited proxy returned empty body). | Log as extraction-failed. Do not pass an empty payload to Claude.                          |
| Two SERP queries return the same URL in one cycle.                    | First processed, second skipped via the dedupe store.                                                        |
| Analyst flags but Judge scores below threshold.                       | Log both outputs to the audit record. No Slack alert. This is the false-positive-caught case.                |

---

## 10. Success Metrics

**Hackathon demo metrics (must hit before submission):**
- Precision after Judge: at least 80% on a seeded set of 20 pastes (10 real-looking leaks, 10 tutorial decoys).
- False positive rate after Judge: under 5% on the same set.
- End-to-end latency from discovery to Slack: under 5 minutes for any tested paste.
- Cost per processed paste: under $0.50, averaged across the demo run.
- Live demo: catch 1 verified leak out of 50 mock candidates on stage in under 2 minutes.

**Judging criteria mapping (from Web Data UNLOCKED rubric):**
- *Technology and model integration:* Two Bright Data products integrated. Claude Sonnet used twice in a non-trivial Analyst-and-Judge pattern.
- *Presentation:* Terminal logs are the visual. Slack alert is the punchline. 5-slide pitch deck pre-built.
- *Business impact:* Addresses a real SOC pain point (Shadow AI leaks) with a budget-aware architecture an enterprise would actually deploy.
- *Uniqueness:* Two-LLM Analyst-and-Judge pattern is genuinely novel for the leak detection space. Most competitors run a single classifier.

**Post-hackathon metrics (v2 onward):**
- Mean time from leak posting to verified alert.
- Cost per verified true positive (not per processed paste).
- Customer-reported true positive rate from beta SOC teams.

---

## 11. Open Questions

1. **Judge model choice.** Sonnet at temperature 0 is the current default. Worth A/B testing Opus on the same seeded set to see if the precision lift is worth the cost increase. Decision needed before final demo rehearsal.

2. **Regex aggressiveness.** Tighter patterns mean lower Bright Data spend and lower recall. Looser patterns catch more but burn more credit on tutorial pastes. The current set is medium-tight. Tuning will need a second round with the seeded test set.

3. **Stretch: live key validation.** A third node could test whether a flagged AWS key is still active using STS GetCallerIdentity. This is genuinely useful but legally murky. Out of scope for the hackathon submission. Worth flagging in the pitch as a v2 capability with appropriate guardrails.

4. **Stretch: analyst feedback loop.** Slack alert payload could include "investigate" and "false positive" buttons that feed back into the audit log and gradually retrain the Judge rubric. Out of scope for v1. Sketch it on the roadmap slide.

5. **Post-hackathon positioning.** Is this a standalone product, a feature for a larger SOC tool to acquire, or a Bright Data Startup Program project? Decision depends on judges' reaction and whether the project gets fast-tracked.

6. **Naming.** "LeakGuard" is clean but slightly generic. Worth a 10-minute brainstorm if there is time before submission. Current shortlist: LeakGuard, PasteWatch, Sentinel-PG, Surfacer.

---

## Appendix: Five-slide pitch deck outline

1. **The threat that moved.** Credentials used to leak from misconfigured S3 buckets. Now they leak because a junior engineer asked an AI assistant for help and pasted a real `.env` into the prompt.
2. **Where existing tools cannot reach.** GitGuardian watches GitHub. SIEMs watch internal traffic. Nobody is watching Pastebin in real time at the source-coverage and bypass capability an enterprise needs.
3. **LeakGuard's triage funnel.** SERP API narrows the web to relevant URLs. Web Unlocker guarantees access. Regex strips out 90% of noise. Two-LLM Analyst-and-Judge catches the real leak with a confidence score.
4. **Live demo.** 50 mock URLs in. 1 verified Slack alert out. 2 minutes on the clock.
5. **Why this wins the track.** Track 3 is Security & Compliance. The architecture is cost-aware. The Judge pattern self-audits, which is exactly what an enterprise SOC team will buy.
