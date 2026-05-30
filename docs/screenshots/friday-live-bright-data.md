# Live Bright Data SERP — captured evidence

Supervised one-shot runs via `scripts/live_serp.py`, which calls the validated
`nodes.discovery.serp_search()` directly (parsed SERP through Bright Data, not the
graph). Both runs executed with `LANGSMITH_TRACING=false` per the real-data safety
rule — no live paste content was traced. Zone: `leakguard_serpapi`.

Captured: 2026-05-30.

## Run 1 — controlled fixture marker (healthy / no-exposure state)

```
[live-serp] ts=2026-05-30T10:25:50+00:00
[live-serp] zone=leakguard_serpapi langsmith_tracing=false
[live-serp] query='site:pastebin.com "leakguard-test-fixture-29may"'
[live-serp] got 0 organic result(s)
[live-serp] no organic results — demo-able as 'no exposures found, system healthy'
```

Demonstrates the negative path: the integration is live and the parse succeeds,
the watchlist marker simply isn't exposed → "system healthy."

## Run 2 — broad query (live discovery returning candidate URLs)

```
[live-serp] ts=2026-05-30T10:26:11+00:00
[live-serp] zone=leakguard_serpapi langsmith_tracing=false
[live-serp] query='site:pastebin.com "test"'
[live-serp] got 10 organic result(s)
  [1]  https://pastebin.com/8uHLznpz                      Test Apex Triggers
  [2]  https://pastebin.com/eTvq8NNJ                      test - Pastebin.com
  [3]  https://pastebin.com/nGTmYB8s?source=public_pastes Test - Pastebin.com
  [4]  https://pastebin.com/1Ax09GTp                      Test automation logic
  [5]  https://pastebin.com/WFAvim8s                      Test - Pastebin.com
  [6]  https://pastebin.com/LHCtkv1D                      test - Pastebin.com
  [7]  https://pastebin.com/6AXWzH5Y                      Test scheduling logic
  [8]  https://pastebin.com/aBm3LcaW                      Test - Pastebin.com
  [9]  https://pastebin.com/1ifLGuxg                      Test 29 - Pastebin.com
  [10] https://pastebin.com/1h9eanjK                      TEST - Pastebin.com
```

Demonstrates the discovery path: Bright Data returns 10 parsed organic Pastebin
links — the candidate URLs the pipeline would then extract → triage → judge.

## Validation note

Parsed organic results require `brd_json=1` appended to the Google URL (the SERP
zone defaults to Raw HTML, so `format: "json"` alone returns a raw-HTML envelope
with 0 organic). Confirmed working: `serp_search()` reads `r.json()["organic"]`.
