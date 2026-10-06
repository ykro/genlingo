"""`make check`: the live page end to end, as the browser uses it.

Opens the page, wakes David (and says how long it took), then translates every example on both sides
and checks that David still gets every slang term right and that Goliath still misses at least one.
Exit code = number of problems.

    uv run --project duel python scripts/check_page.py [--url https://…]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

import httpx


def page_url() -> str:
    out = subprocess.run(["gcloud", "run", "services", "describe", "genlingo", "--region", "us-central1",
                          "--project", "ai-experiments-487722", "--format", "value(status.url)"],
                         capture_output=True, text=True)
    if out.returncode or not out.stdout.strip():
        sys.exit(f"no page URL: {out.stderr.strip()[:200]}")
    return out.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="")
    url = (ap.parse_args().url or page_url()).rstrip("/")
    problems = 0
    with httpx.Client(base_url=url, timeout=900) as http:
        page = http.get("/")
        print(f"page {url}: {page.status_code}")
        problems += page.status_code != 200
        t0 = time.time()
        st = http.post("/api/david/wake").json()
        print(f"David: {st['phase']} after {time.time() - t0:.0f} s")
        if st["phase"] != "ready":
            print(f"  !! {st.get('error')}")
            return problems + 1
        for ex in http.get("/api/examples").json():
            body = {"phrase": ex["text"], "direction": ex["direction"], "example_id": ex["id"]}
            d = http.post("/api/translate/david", json=body).json()
            g = http.post("/api/translate/goliath", json=body).json()
            d_ok = d.get("status") == "ok" and all(t["ok"] for t in d.get("terms", [])) and d.get("terms")
            g_miss = g.get("status") == "ok" and not all(t["ok"] for t in g.get("terms", []))
            flag = "ok" if d_ok and g_miss else "!!"
            problems += flag != "ok"
            print(f"{flag} {ex['text']}\n   David   {d.get('latency_ms')} ms  {d.get('text')}"
                  f"\n   Goliath {g.get('latency_ms')} ms  {g.get('text') or g.get('error')}")
    print("OK" if not problems else f"{problems} problema(s)")
    return problems


if __name__ == "__main__":
    sys.exit(main())
