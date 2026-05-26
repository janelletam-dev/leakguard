"""Discovery node — Bright Data SERP API (DISC-01..05).

Runs scheduled Google dork queries (`site:[paste-domain] "[keyword]"`) and collects
candidate URLs, deduped against a persistent processed-URLs store.

VALIDATED INTEGRATION NOTE (2026-05-25):
    The SERP zone default is Raw HTML, so `format: "json"` alone returns a raw-HTML
    envelope (status_code/headers/body, 0 organic). To get parsed organic results you
    MUST append `brd_json=1` to the Google URL and read r.json()["organic"]. The hack
    pack's search_google_parsed() does NOT do this. Confirmed: returns 10 organic
    Pastebin links for `site:pastebin.com "test"`.
"""

from __future__ import annotations

import os
from urllib.parse import urlencode

import requests

from state import LeakGuardState

BRIGHTDATA_ENDPOINT = "https://api.brightdata.com/request"
PASTE_DOMAINS = ["pastebin.com", "paste.ee", "ghostbin.com", "dpaste.org"]


def serp_search(query: str, num_results: int = 10) -> list[dict]:
    """Return parsed organic results for a Google dork query.

    Uses brd_json=1 so Bright Data parses the SERP regardless of zone default.
    """
    search_url = "https://www.google.com/search?" + urlencode(
        {"q": query, "num": num_results, "brd_json": 1}
    )
    resp = requests.post(
        BRIGHTDATA_ENDPOINT,
        headers={
            "Authorization": f"Bearer {os.environ['BRIGHTDATA_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={"zone": os.environ["BRIGHTDATA_SERP_ZONE"], "url": search_url, "format": "raw"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("organic", [])


def discovery_node(state: LeakGuardState) -> LeakGuardState:
    """Build dork queries from the keyword watchlist, collect + dedupe candidate URLs.

    TODO:
      - cross paste domains x keywords, cap queries per cycle (DISC-05)
      - drop URLs already in the processed-URLs store (DISC-03)
      - respect the Bright Data budget guardrail at 80% of cap (NFR-06)
    """
    # MOCK (Day-2 graph wiring): real SERP discovery via serp_search() is deferred to the
    # Bright Data integration; today the graph runs against seeded mock paste URLs.
    print(f"[discovery] (mock) passthrough; seeded url={state.get('url')!r}")
    return state
