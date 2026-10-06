"""`make screenshots`: the live page in a real browser, for docs/demo/ (light theme only).

    uv run --with playwright python scripts/screenshots.py [--url https://…]

Waits for David to be ready (a cold start shows "Preparando a David…" first, also captured), then
taps one example per direction. 1920×1080 (projector) and 1280×800 (laptop).
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parents[1] / "docs" / "demo"


def page_url() -> str:
    out = subprocess.run(["gcloud", "run", "services", "describe", "genlingo", "--region", "us-central1",
                          "--project", "ai-experiments-487722", "--format", "value(status.url)"], capture_output=True, text=True)
    if out.returncode or not out.stdout.strip():
        sys.exit("no page URL")
    return out.stdout.strip()


async def shoot(url: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080}, color_scheme="light")
        t0 = time.time()
        await page.goto(url)
        await page.wait_for_timeout(20_000)
        if await page.locator(".net.wait").count():  # a cold start: capture the waiting screen
            await page.screenshot(path=OUT / "01-preparando-a-david.png")
        await page.wait_for_selector("#go:not([disabled])", timeout=600_000)
        print(f"David listo {time.time() - t0:.0f} s después de abrir la página")
        for name, direction in (("02-comparar-genz-a-papas", "genz_to_parent"), ("03-comparar-papas-a-genz", "parent_to_genz")):
            await page.locator(f"#ex-{direction} .ex").first.click()
            await page.wait_for_timeout(300)
            await page.wait_for_function("() => !document.querySelector('.side .answer.wait')", timeout=120_000)
            await page.wait_for_timeout(700)
            await page.screenshot(path=OUT / f"{name}.png")
        await page.set_viewport_size({"width": 1280, "height": 800})
        await page.wait_for_timeout(500)
        await page.screenshot(path=OUT / "04-laptop-1280.png", full_page=True)
        await browser.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="")
    asyncio.run(shoot(ap.parse_args().url or page_url()))
    print(f"capturas -> {OUT}")


if __name__ == "__main__":
    main()
