"""Live SERP one-shot — run a Bright Data SERP query and print parsed results.

Standalone capture utility for the Friday supervised one-shot, used to populate
docs/screenshots/friday-live-bright-data.md. Does NOT touch the graph: this calls
the validated nodes.discovery.serp_search() directly, prints organic results,
and exits. One BD SERP API call per invocation.

Usage:
    python scripts/live_serp.py 'site:pastebin.com "leakguard-test-fixture-29may"'

Env required: BRIGHTDATA_API_KEY, BRIGHTDATA_SERP_ZONE.
LANGSMITH_TRACING must be `false` for any real-data run (the rule in
leakguard-build-status: tracing off whenever the response could carry real
paste content).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Let `python scripts/live_serp.py …` find the project packages without install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nodes.discovery import serp_search  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/live_serp.py '<google query>'", file=sys.stderr)
        return 2

    query = sys.argv[1]
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    zone = os.environ.get("BRIGHTDATA_SERP_ZONE", "<unset>")
    tracing = os.environ.get("LANGSMITH_TRACING", "unset")

    print(f"[live-serp] ts={ts}")
    print(f"[live-serp] zone={zone} langsmith_tracing={tracing}")
    print(f"[live-serp] query={query!r}")

    results = serp_search(query, num_results=10)
    print(f"[live-serp] got {len(results)} organic result(s)")

    for i, r in enumerate(results, 1):
        link = r.get("link") or r.get("url") or "<no link>"
        title = (r.get("title") or "").strip()[:90]
        print(f"  [{i}] {link}")
        if title:
            print(f"      title: {title}")

    if not results:
        print("[live-serp] no organic results — demo-able as 'no exposures found, system healthy'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
