# LeakGuard Agent — Product Requirements Document

| Field    | Value                                   |
|----------|-----------------------------------------|
| Project  | LeakGuard Agent                         |
| Version  | 0.2                                     |
| Date     | 25 May 2026                             |
| Author   | Janelle D. Tamayo (Creative Stallion)   |
| Status   | Draft (Hackathon scope)                 |
| Submission Deadline | 31 May 2026 (Web Data UNLOCKED) |
| Sponsor Track | Track 3: Security & Compliance     |
| Changelog | v0.2: Rewrote Section 1 around AI-builder thesis. Added solo-builder as second primary user. Rebuilt Section 7 around three demo surfaces. Added Section 12 (Pitch and Positioning). Promoted Streamlit dashboard from stretch to planned surface. |

---

## 1. Overview / Problem Statement

In April 2026, during a hackathon build, personal data including my email and travel information ended up in a public GitHub repository. I did not put it there. It arrived through the normal flow of AI-assisted development. Configuration files passed between me and AI coding tools. Snippets pasted into prompts. Screenshots shared in collaboration channels. The exposure was small but the mechanism was not. Multiply one builder by every developer now shipping with Cursor, Claude, Copilot, or any AI coding assistant, and the pattern becomes a category.

AI-assisted development creates exposure surfaces that legacy security tools were not built to watch. GitGuardian watches GitHub. SIEMs watch internal traffic. Nobody is watching the surfaces where AI builders actually leak: public paste sites, screenshot mirrors, Discord pastes, forum debugging threads, and AI tool transcripts shared in public for help.

LeakGuard is an autonomous agent that patrols those surfaces for credentials and personal data tied to a specific organisation or individual. It runs a three-stage triage funnel ending with a verified Slack alert, usually before the exposed credential has been indexed by Google.

The bet: as AI-assisted development becomes the default, this exposure category grows fast. The teams who have a tool for it before the breach are the ones who win the market.

---

## 2. Goals and Non-Goals

**Goals (v1, hackathon scope):**
- Detect verified credential leaks across at least four public paste sites (Pastebin, paste.ee, ghostbin, dpaste).
- Hit better than 80% precision after the Judge node on a seeded test set of 20 pastes.
- Stay under the $250 Bright Data credit cap across the full demo run.
- Ship a 2-3 minute demo that uses three deliberate surfaces (terminal, Slack, Streamlit dashboard) and lands a real-time verified alert on stage.
- Use at least two Bright Data products (SERP API + Web Unlocker) to satisfy sponsor requirements.
- The demo voiceover names the AI-builder threat model and the personal origin story that motivated the build.

**Non-Goals (v1):**
- A React or Next.js frontend. Streamlit is the dashboard layer. No HTML, CSS, or JavaScript will be written.
- Coverage of GitHub, GitLab, or any structured source. GitGuardian already owns that lane.
- Automated remediation. LeakGuard alerts. It does not rotate keys, lock accounts, or take down pastes.
- Multi-tenant SaaS. One configured identity for the hackathon (one org or one builder).
- Historical archive search. Only fresh paste monitoring going forward.
- A live-key validator step. Legally and ethically out of scope for a hackathon submission.

---

## 3. Target Users

**Primary user A: SOC analyst at a mid-size company (250-2000 employees).**
Lives in their SIEM most of the day. Drowns in alerts. Has been burned by false positives, so they ignore tools that cry wolf. Technically strong but time-poor. Needs alerts that come with reasoning, not just a flagged URL. Manages roughly 50-200 active investigations a week.

**Primary user B: Solo AI builder or small founding team (1-5 people).**
Ships fast. Uses Cursor, Claude, Copilot, and any other AI tool that gets them to working code quicker. Pastes config files into prompts when debugging. Shares screenshots in Discord and on Twitter. Has no SOC team, no security engineer, often no security review at all. Has probably already exposed something they do not know about. This is the user the next version of LeakGuard likely serves first, and it is the user the founder of LeakGuard already is.

**Secondary user: Security Engineer or CISO.**
Wants quarterly evidence of external exposure for board reporting. Needs a structured log of every flag, every Judge decision, every alert fired and rejected. Cares about ROI on tooling, not feature counts.

**Scale assumption for v1:** the agent monitors one target identity (an organisation or an individual builder) with roughly 10-20 keyword variants. Variants include company name, internal subdomains, product codenames, personal email, and LinkedIn handle. Processes about 50-200 candidate pastes per day across all monitored sites.

---

## 4. Jobs to Be Done

| ID    | Job (When / I want to / So I can)                                                                                                                                  | Priority |
|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| JTBD-01 | When a developer pastes a snippet containing production credentials, I want a verified alert within 5 minutes, so I can rotate the keys before an attacker finds them. | P0       |
| JTBD-02 | When the agent flags a candidate, I want a clear severity score with audit reasoning, so I can decide in under 30 seconds whether to escalate.                       | P0       |
| JTBD-03 | When I review the weekly log, I want every flag, score, and decision recorded, so I can prove to my CISO or to myself that the tool is catching real threats.        | P0       |
| JTBD-04 | When a paste contains a placeholder key like AKIA…EXAMPLE, I want the system to quietly reject it, so my Slack channel does not get spammed with tutorial code.       | P0       |
| JTBD-05 | When I am a solo AI builder with no security team, I want to monitor my own email, LinkedIn handle, and project names, so I find out about exposures before anyone weaponises them. | P0 |
| JTBD-06 | When the same leak gets reposted across multiple paste sites, I want one alert, not five, so I am not chasing the same incident in parallel.                          | P1       |
| JTBD-07 | When I add a new product codename or personal identifier to monitor, I want it picked up on the next scheduled scan, so I do not need to redeploy anything.           | P1       |
| JTBD-08 | When my SIEM detects a brute-force attempt, I want to cross-reference our public exposure log, so I can correlate the incident faster.                                | P2       |

---

## 5. Functional Requirements

### Discovery (DISC) — Bright Data SERP API

- **DISC-01** Run scheduled Google Dork queries via Bright Data SERP API. Default pattern: `site:[paste-domain] "[target-keyword]"` across the keyword list.
- **DISC-02** Default schedule is every 15 minutes. Configurable per environment.
- **DISC-03** Deduplicate URLs against a persistent processed-URLs store. A URL is processed at most once.
- **DISC-04** Maintain a YAML keyword list with organisation names, internal subdomains, product codenames, and personal identifiers (email, LinkedIn handle). Hot-reload on file change.
- **DISC-05** Cap SERP queries per cycle. If the cap is hit, the cycle ends and logs the overflow.

### Extraction (EXTR) — Bright Data Web Unlocker

- **EXTR-01** Use Bright Data Web Unlocker to fetch raw paste content. No direct HTTP fallback.
- **EXTR-02** Support Pastebin, paste.ee, ghostbin, dpaste, and one forum target (Reddit r/sysadmin as a stretch).
- **EXTR-03** Handle rate limits with exponential backoff. Maximum three retries per URL before logging the failure.
- **EXTR-04** Cache fetched paste content locally for 24 hours, keyed by URL hash, to avoid duplicate Bright Data charges.
- **EXTR-05** Truncate any paste over 10KB to the first 10KB before passing downstream. Log the truncation.

### Triage (TRGE) — Local regex pre-filter

- **TRGE-01** Run a regex pattern set against fetched content. Patterns cover AWS keys (AKIA prefix + 16-character body), JWT structure, Stripe live keys (sk_live_), Slack webhook URLs, generic `password=`, `db_host=`, `api_key=`, and email-like strings matching the personal identifier watchlist.
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

### Dashboard (DASH) — Streamlit page

- **DASH-01** A Streamlit page renders the current state of the audit log.
- **DASH-02** Summary card at the top displays counts for the current run: pastes scanned, candidates flagged after triage, verified leaks, false positives caught (Analyst flagged, Judge rejected).
- **DASH-03** Verified leak list displays each leak as a card. Card shows source URL, redacted credential, Judge score, audit reasoning, and timestamp.
- **DASH-04** The dashboard reads from the same JSON audit log the pipeline writes. No separate database, no API layer.
- **DASH-05** Page refresh interval is 5 seconds. The dashboard does not stream events in real time. It reads the most recent state of the log on each refresh.
- **DASH-06** The dashboard runs as a separate Streamlit process. The pipeline and the dashboard share only the audit log file.

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
- **NFR-07 Demo resilience:** The Streamlit dashboard is a presentation surface, not a critical path. If the dashboard fails on stage, the terminal demo and the Slack alert still carry the pitch.

---

## 7. User Flows

### Flow 1: Verified leak (happy path)

1. Scheduled SERP query runs against `site:pastebin.com "[target-keyword]"`.
2. Bright Data SERP API returns 50 candidate URLs.
3. Deduplication drops the URLs that have already been processed.
4. Web Unlocker fetches the new pastes.
5. Regex triage drops the pastes with zero hits.
6. Analyst flags candidates as containing what look like real credentials.
7. Judge scores each candidate. Only scores of 8 and above pass.
8. Pipeline fires a Slack alert and writes the verified leak to the audit log.
9. The Streamlit dashboard reflects the new verified leak on its next refresh.

### Flow 2: The on-stage demo (the 2-minute pitch moment)

Three surfaces, three deliberate roles. Each one shows the judges a different part of the thesis.

1. **The Claude desktop screenshot (the threat).** Slide one of the deck shows a sanitised screenshot of a real AI coding session with a config file pasted into the prompt. Voiceover names the AI-builder threat model and the personal origin story. This frames the problem before any code runs.
2. **The terminal (the engine).** Switch to the terminal. Run the pipeline against 50 mock paste URLs served from the local mock server. Terminal logs stream the funnel narrowing: 50 ingested, 47 discarded by regex, 3 sent to Analyst, 1 verified by Judge. This proves the backend is real.
3. **The Slack channel (the workflow proof).** A Slack alert fires the moment the Judge verifies the leak. The notification is visible on screen. This proves the system fits into how teams already work.
4. **The Streamlit dashboard (the shipped artifact).** Switch to the browser. The dashboard reads from the audit log the pipeline just wrote. The verified leak appears as a card with the redacted credential, the Judge score, the audit reasoning, and the source URL. This proves the system ships beyond a script.

Total demo run is under 2 minutes. The terminal is the engine. The Slack alert is the integration story. The Streamlit dashboard is the credibility artifact. The Claude desktop screenshot is the threat narrative.

### Flow 3: False positive caught (the audit story)

1. Web Unlocker fetches a paste that is actually a tutorial titled "How to set up AWS CLI."
2. Regex triage flags it because the tutorial uses the literal example string `AKIAIOSFODNN7EXAMPLE`.
3. Analyst flags it as containing what could be an AWS key (recall mode).
4. Judge scores 3/10. Reasoning: "Secret matches a known AWS documentation placeholder. Surrounding text reads as tutorial content, not panicked debugging."
5. No alert fires. The rejection is logged with full Judge reasoning. The dashboard shows the false positive in the "caught" count, which is the line you read out loud during the demo to prove the system audits itself.

---

## 8. Design and Technical Constraints

**Language and runtime:** Python 3.11.

**Core dependencies:**
- `langgraph` for orchestration.
- `anthropic` SDK for Claude Sonnet calls (Analyst and Judge).
- `requests` for Bright Data SERP API and Web Unlocker calls.
- `streamlit` for the dashboard layer.
- `python-dotenv` for environment variables.
- `pydantic` for typed state and Judge JSON validation.
- `pytest` for the seeded test set.

**Sponsor infrastructure (mandatory for the track):**
- Bright Data SERP API for discovery.
- Bright Data Web Unlocker for extraction.

**LLM:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) for both Analyst and Judge nodes. Same model, different system prompts, different temperatures. Analyst runs warmer for recall. Judge runs at temperature 0 for deterministic scoring.

**Dashboard:** Streamlit, running as a separate process. Reads from the same JSON audit log the pipeline writes. No backend API, no database, no auth. The dashboard is a view layer, not an application.

**Alerting:** Slack incoming webhook URL stored in `.env`.

**Deployment:** Local terminal for the hackathon. No hosting, no cron, no Docker. Scheduling is a simple Python loop with `time.sleep(900)` between cycles. Post-hackathon, the natural target is a small container on Fly.io or Railway, with the Streamlit dashboard hosted on Streamlit Community Cloud.

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
├── dashboard/
│   └── app.py            (Streamlit page)
├── state.py
├── graph.py
├── mock_server/
│   └── pastes/           (HTML files for safe demo)
├── audit_log.jsonl       (shared between pipeline and dashboard)
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
| Paste contains a regex hit but is empty after fetching.               | Log as extraction-failed. Do not pass an empty payload to Claude.                                            |
| Two SERP queries return the same URL in one cycle.                    | First processed, second skipped via the dedupe store.                                                        |
| Analyst flags but Judge scores below threshold.                       | Log both outputs to the audit record. No Slack alert. This is the false-positive-caught case.                |
| Streamlit dashboard fails to load during the demo.                    | Continue the demo using terminal logs and Slack alert. The dashboard is not on the critical path.            |
| Audit log file locked by the pipeline while the dashboard tries to read. | Dashboard retries once after 500ms. If still locked, dashboard shows the previous state with a "refreshing" indicator. |

---

## 10. Success Metrics

**Hackathon demo metrics (must hit before submission):**
- Precision after Judge: at least 80% on a seeded set of 20 pastes (10 real-looking leaks, 10 tutorial decoys).
- False positive rate after Judge: under 5% on the same set.
- End-to-end latency from discovery to Slack: under 5 minutes for any tested paste.
- Cost per processed paste: under $0.50, averaged across the demo run.
- Live demo: catch 1 verified leak out of 50 mock candidates on stage in under 2 minutes.
- The Streamlit dashboard renders without errors during the full 2-minute demo run.

**Judging criteria mapping (from Web Data UNLOCKED rubric):**
- *Technology and model integration:* Two Bright Data products integrated. Claude Sonnet used twice in a non-trivial Analyst-and-Judge pattern. Streamlit dashboard as a view layer over a shared audit log.
- *Presentation:* Three deliberate demo surfaces (terminal, Slack, dashboard). 5-slide pitch deck pre-built. Personal origin story named in the voiceover.
- *Business impact:* Addresses the AI-builder exposure category, which is growing as AI-assisted development becomes default. Budget-aware architecture an enterprise would actually deploy.
- *Uniqueness:* Two-LLM Analyst-and-Judge pattern is genuinely novel for the leak detection space. Category framing (AI-builder exposure surfaces) is differentiated from existing tools.

**Post-hackathon metrics (v2 onward):**
- Mean time from leak posting to verified alert.
- Cost per verified true positive (not per processed paste).
- Self-monitoring beta: number of solo AI builders using LeakGuard to watch their own identifiers.

---

## 11. Open Questions

1. **Judge model choice.** Sonnet at temperature 0 is the current default. Worth A/B testing Opus on the same seeded set to see if the precision lift is worth the cost increase. Decision needed before final demo rehearsal.

2. **Regex aggressiveness.** Tighter patterns mean lower Bright Data spend and lower recall. Looser patterns catch more but burn more credit on tutorial pastes. The current set is medium-tight. Tuning will need a second round with the seeded test set.

3. **Stretch: live key validation.** A third node could test whether a flagged AWS key is still active using STS GetCallerIdentity. This is genuinely useful but legally murky. Out of scope for the hackathon submission. Worth flagging in the pitch as a v2 capability with appropriate guardrails.

4. **Stretch: analyst feedback loop.** Slack alert payload could include "investigate" and "false positive" buttons that feed back into the audit log and gradually retrain the Judge rubric. Out of scope for v1.

5. **Post-hackathon positioning.** Standalone product, feature acquisition target, or Bright Data Startup Program project. Decision depends on judges' reaction and whether the project gets fast-tracked.

---

## 12. Pitch and Positioning

This section is not part of the technical spec. It holds the language and framing that make the technical work legible to judges, investors, and customers. Update this section as the pitch evolves and copy from it when writing the deck or LinkedIn posts.

### The thesis (one sentence)

AI-assisted development creates exposure surfaces that legacy security tools were not built to watch, and LeakGuard is the monitor for the surfaces AI builders actually create.

### Roadmap direction (decided)

Self-monitoring for solo AI builders is the committed v2 wedge: builders watch their own identifiers (email, LinkedIn handle, project names) before we sell to enterprise SOC teams. The personal origin story supports it, and detection-at-scale (Bright Data) stays the enterprise layer the wedge funnels into. (Previously an open question — now a stated direction.)

### The category claim

This is not "a better GitGuardian." GitGuardian solved the GitHub problem. The next exposure category is paste sites, screenshot mirrors, Discord pastes, forum debugging threads, and AI tool transcripts shared in public. Different surface, different scrapers, different threat model. LeakGuard owns this category.

### The personal origin story (medium intensity)

During a recent hackathon build, personal details including my email and travel information ended up in a public GitHub repository through the normal flow of AI-assisted development. I am a builder. I use Cursor and Claude every day. If this happens to me while I am paying attention, it happens to every developer shipping fast with AI tools. I built LeakGuard because the tool I needed did not exist.

Use this on slide one or two. Keep the delivery factual. Resist the urge to dramatise. The story works because it is ordinary, not because it is shocking.

### The credibility position

I am a designer who became a vibe coder who is becoming a founder. I built this in six days, solo, with Bright Data infrastructure, LangGraph orchestration, and a two-LLM Analyst-and-Judge architecture. The shipping is the credential.

### The demo voiceover (suggested opening)

"Last month, I pasted real configuration values into an AI prompt while debugging a build. Within a week, my email and travel details were sitting in a public GitHub repository. I did not put them there. The normal flow of AI-assisted development put them there. AI builders create new exposure surfaces every day. Existing security tools were not built to watch those surfaces. LeakGuard is."

### What not to say

- "Claude leaked my credentials." It did not. The human workflow did. Keep the framing on the workflow, not the tool.
- "This will replace GitGuardian." It will not. It complements it. Different category.
- "AI is dangerous." It is not. It is a new surface area with new exposure patterns. Stay calm, stay specific.

### Track alignment

This project fits Track 3 (Security & Compliance) by design. It also lightly touches Track 1 (the dashboard could surface competitor or brand exposure for GTM teams) and Track 2 (the same engine could monitor for financial leak signals). The hackathon submission stays focused on Track 3. The cross-track potential goes on the roadmap slide.

### Five-slide deck outline (mapped to this PRD)

1. **The threat that moved.** Personal origin story (Section 12). Screenshot of the AI coding session. Name the AI-builder exposure category.
2. **Where existing tools cannot reach.** GitGuardian watches GitHub. SIEMs watch internal traffic. Nobody watches paste sites, screenshot mirrors, or Discord pastes at the source-coverage and bypass capability an enterprise needs.
3. **LeakGuard's triage funnel.** SERP API narrows the web. Web Unlocker guarantees access. Regex strips noise. Two-LLM Analyst-and-Judge catches the real leak with a confidence score.
4. **Live demo.** Three surfaces, two minutes. Terminal logs, Slack alert, Streamlit dashboard. 50 mock URLs in. 1 verified leak out.
5. **Why this wins the track.** Track 3 is Security & Compliance. The architecture is cost-aware. The Judge pattern self-audits. The category framing is bigger than the demo. Roadmap shows the self-monitoring wedge for solo AI builders.
