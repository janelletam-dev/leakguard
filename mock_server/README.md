# Mock paste server

Serves synthetic paste fixtures on `http://localhost:8080` for safe, credit-free local runs
and demos (Flow 2). All credentials in the fixtures are **fake** — generated for LeakGuard's
own test funnel, not real secrets.

Run: `python mock_server/server.py`

## Fixtures

| Route | File | Purpose | Expected outcome |
|-------|------|---------|------------------|
| `/paste/001` | `pastes/mock-paste-001.html` | Realistic accidental `.env` leak — panicked on-call debugging, real-looking AWS/Stripe/DB credentials, internal subdomain. | Verified leak → fires an alert. |
| `/paste/002` | `pastes/mock-paste-002.html` | Tutorial decoy — uses AWS's well-known docs placeholder key (`AKIAIOSFODNN7EXAMPLE`). | False positive → Triage + Analyst flag it (recall), Judge rejects it. |

> The fixtures deliberately carry **no inline hints** about their expected outcome — that
> would leak the answer to the LLM nodes, which read the full paste. Outcome documentation
> lives here, where the pipeline never sees it.
