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
