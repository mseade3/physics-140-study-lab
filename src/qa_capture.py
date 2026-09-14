"""Capture full-page screenshots of each Study Lab page for design QA."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa_shots"
BASE = "http://localhost:8501"
PAGES = [
    "Command Center",
    "Coverage",
    "Library",
    "Packet Catalog",
    "Progress Tracker",
    "Force Lab",
    "Cursor Rules",
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2500)

        for name in PAGES:
            # Streamlit sidebar radio labels
            locator = page.get_by_text(name, exact=True)
            if locator.count() == 0:
                print("MISSING", name)
                continue
            locator.first.click()
            page.wait_for_timeout(1800)
            slug = name.lower().replace(" ", "_")
            path = OUT / f"{slug}.png"
            page.screenshot(path=str(path), full_page=True)
            print("saved", path.name)

        browser.close()


if __name__ == "__main__":
    main()
