# Triage tuning notes

Observations parked for the Day-3 regex tuning + eval round (PRD Open Question #2).
Patterns are intentionally left as-is until then.

- **mock-paste-001** — the `email` pattern matches `kQ9mLp2wRtVz@db-prod-01.acme.com`, which is actually the *password* segment of the postgres connection string (`postgres://svc_payments:<password>@host`), not a real email address. False-ish hit; goes into the Day-3 eval set to refine the email pattern (e.g. exclude connection-string userinfo).
