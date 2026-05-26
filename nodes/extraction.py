"""Extraction node — fetch raw paste content (EXTR-01, EXTR-05).

Day 1: pure `requests` GET against the local mock server. No Bright Data yet.
Day 2 (EXTR-01 / EXTR-03): swap the GET for the validated Web Unlocker call
(POST https://api.brightdata.com/request, zone=$BRIGHTDATA_UNLOCKER_ZONE,
format="raw" — same auth pattern as nodes/discovery.py) and add exponential-backoff
retries.
"""

from __future__ import annotations

from datetime import datetime, timezone

import requests

from state import LeakGuardState

MAX_BYTES = 10 * 1024   # EXTR-05: truncate to first 10KB
TIMEOUT_SECONDS = 10


def _log(url: str, status, bytes_fetched: int, truncated: bool) -> None:
    """Emit one structured log line per call."""
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(
        f"[extraction] ts={ts} url={url} status={status} "
        f"bytes={bytes_fetched} truncated={truncated}"
    )


def extraction_node(state: LeakGuardState) -> LeakGuardState:
    """Fetch state['url']; populate raw_content on 200, else error (raw_content left None)."""
    url = state["url"]
    state["raw_content"] = None
    state["truncated"] = False

    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        # Catch only RequestException so unexpected bugs surface loudly (no bare except).
        state["error"] = type(exc).__name__
        _log(url, "EXC", 0, False)
        return state

    bytes_fetched = len(resp.content)

    if resp.status_code != 200:
        state["error"] = f"HTTP {resp.status_code}"
        _log(url, resp.status_code, bytes_fetched, False)
        return state

    content = resp.text
    truncated = False
    if len(content.encode("utf-8")) > MAX_BYTES:
        content = content.encode("utf-8")[:MAX_BYTES].decode("utf-8", "ignore")
        truncated = True

    state["raw_content"] = content
    state["truncated"] = truncated
    _log(url, resp.status_code, bytes_fetched, truncated)
    return state
