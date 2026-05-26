# Day 1 — extraction → triage, real terminal output (2026-05-25)

Deck material for Day 5. Real output from the live `extraction_node` → `triage_node`
run against the mock server fixtures. The "false-positive-caught" story, proven in code
**before any LLM exists** — triage flags both; the Judge is what will separate them.

## The funnel, two fixtures

| Fixture | `is_triaged_clean` | regex hits |
|---------|--------------------|------------|
| `/paste/001` (real-looking leak) | `False` | `aws_access_key`, `stripe_live`, `db_host_kv`, `email` |
| `/paste/002` (AWS tutorial decoy) | `False` | `aws_access_key` — the `AKIA…EXAMPLE` placeholder |

Both pass triage (recall by design). On Day 2 the Judge verifies 001 and rejects 002 as a
documentation placeholder. That is the self-auditing story for slide 5.

## Raw terminal log

```
################  /paste/001  ################
[extraction] ts=2026-05-25T19:26:43+00:00 url=http://localhost:8080/paste/001 status=200 bytes=848 truncated=False
[triage] ts=2026-05-25T19:26:43+00:00 pattern_count=4 duration_ms=0.041 hits=aws_access_key:1, stripe_live:1, db_host_kv:1, email:1
is_triaged_clean: False
regex_hits:
  aws_access_key  AKIAZ7K9QW2MX4P1L3VN            span [554, 574]
  stripe_live     sk_live_51Hb9xQ2eZvKfL8mNpRtYwUiOaSdFgHjKlZxCvBnM  span [669, 718]
  db_host_kv      DB_HOST=db-prod-01.acme.com     span [462, 489]
  email           kQ9mLp2wRtVz@db-prod-01.acme.com  span [778, 810]   (false-ish; see triage_tuning_notes)

################  /paste/002  ################
[extraction] ts=2026-05-25T19:26:43+00:00 url=http://localhost:8080/paste/002 status=200 bytes=747 truncated=False
[triage] ts=2026-05-25T19:26:43+00:00 pattern_count=1 duration_ms=0.034 hits=aws_access_key:1
is_triaged_clean: False
regex_hits:
  aws_access_key  AKIAIOSFODNN7EXAMPLE            span [485, 505]
```

> All credentials above are synthetic values from the demo fixtures. Triage completes in
> ~0.04ms/paste — three orders of magnitude under the 50ms TRGE-04 budget.
