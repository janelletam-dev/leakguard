# Triage tuning notes

Observations parked for the Day-3 regex tuning + eval round (PRD Open Question #2).
Patterns are intentionally left as-is until then.

- **mock-paste-001** — the `email` pattern matches `kQ9mLp2wRtVz@db-prod-01.acme.com`, which is actually the *password* segment of the postgres connection string (`postgres://svc_payments:<password>@host`), not a real email address. False-ish hit; goes into the Day-3 eval set to refine the email pattern (e.g. exclude connection-string userinfo).
  - **Do NOT just tighten `email`.** That match is a false positive for the *label* but a true positive for "a credential is exposed" — `kQ9mLp2wRtVz` is the tail of `DB_PASS=Xy7$kQ9mLp2wRtVz`. The `email` pattern is currently the **only** thing catching that password: `password_kv` matches a literal `password=` (misses `DB_PASS=`), and nothing matches connection-string userinfo (`://user:pass@host`). Day-3 order: **add a DB-password / connection-string pattern first, then tighten `email`** — otherwise the "cleanup" silently drops a real leaked password.

- **Fixture eval hygiene** — the `mock-paste-001/002` HTML comments originally stated the expected outcome ("should score high and fire an alert" / "the Judge should reject it ~3/10"). The LLM nodes read the full paste, so those comments leak the answer to the Judge. Seeded eval pastes must carry no outcome hints — scrub give-away comments before any Judge eval. (Done for the two demo fixtures; purpose documented in `mock_server/README.md` instead.)

## Engineering lessons

- **Falsy-zero in threshold checks.** `(total or default) < threshold` silently coerces a real `0` to `default` — in Python `0 or 99 == 99`. Hit this in a one-off verification print (the Judge scored `0` and it displayed FAIL instead of PASS). Harmless there, but when building the eval harness or any dashboard score/threshold utility, compare the value directly (`score < threshold`) and handle `None` explicitly — never `or`-default a number.

## Eval-set notes (Day 3)

- **Swap the watchlist domain for the seeded set.** `acme.com` is a recognised example/RFC domain, and the Judge correctly flags it as suspicious — which muddies the Target Authenticity axis during calibration. Use a realistic, ungoogleable fake corporate domain in the 20-paste eval set (e.g. `arrowstride.io`, `meridiancore.net`). Leave the **demo** fixtures on `acme.com` as-is: "the Judge verified the leak 9/10 even while flagging the domain as suspicious" is the stronger story.

- **Recall gaps surfaced by the seeded-set triage dry-run (free, pre-Judge).** Real leaks the current patterns miss or only catch by accident — Day-3 pattern work, ordered:
  - **Add PEM private-key block** (`-----BEGIN [A-Z ]*PRIVATE KEY-----`) — `seed-08` (RSA key) gets zero hits and exits as clean. A leaked private key sailing through is a serious miss.
  - **Twilio (`seed-10`) — check the FIXTURE before the regex.** `seed-10` gets zero hits, but its SID isn't valid Twilio format (real = `AC` + 32 **hex**; the fixture used a mixed-case, non-hex, wrong-length string). detect-secrets misses it too — which points at an unrealistic fixture, not a true funnel gap. Thursday: fix the fixture to a real Twilio shape, re-test, *then* decide if an `AC[0-9a-f]{32}` + 32-hex-token pattern is even needed. (Contrast `seed-08`: detect-secrets DOES flag its private key, so that one is a real triage gap — add the PEM pattern.)
  - **Add GitHub PAT** (`ghp_[A-Za-z0-9]{36}`) — `seed-02` only trips because the `token@github.com` URL looks like an email; a bare `GH_TOKEN=ghp_…` would be missed.
  - `seed-05` (DB password) and `seed-09` (GCP key) likewise only trip via the `email` fragment — ties to the existing "don't just tighten `email`" note. Formalize dedicated patterns so coverage isn't incidental.
  - With current patterns, seeded-set recall caps at ~8/10 (seed-08, seed-10 missed). Add these patterns *before* tuning precision, or the recall number is misleading.
