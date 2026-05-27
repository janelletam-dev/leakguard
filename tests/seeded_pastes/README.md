# Seeded eval set (20 pastes)

The calibration ground truth for LeakGuard's precision/recall (PRD section 10): **10 real
leaks** (should fire a verified alert) and **10 decoys** (should not). All credentials are
**synthetic** — fabricated, format-correct, not real secrets.

- Fixtures are **blind**: `seed-01.html` … `seed-20.html` carry no hint of their expected
  outcome, because the LLM nodes read the paste content. Ground truth lives only in
  `manifest.yaml`.
- The decoys are chosen to **trip recall but fail precision** — docs placeholders, test keys,
  template/`${{ secrets }}` references, masked keys, a revoked key — so they exercise the
  Judge, not just the regex.
- `seed-05` plants the known regex gap (a DB password only inside a connection string).

Run the eval (after `source .env`, costs real Claude calls, no Slack):

```bash
python tests/run_eval.py
```
