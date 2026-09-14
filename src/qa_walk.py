"""Smoke-walk each Streamlit sidebar page; assert key copy is present."""

from __future__ import annotations

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8501"
PAGES = {
    "Command Center": ["Exam calendar", "Grade weights", "Help Room", "Next exam"],
    "Syllabus": ["Materials", "Mastering Physics", "Letter scale", "melnichuk16001", "OQGL"],
    "Coverage": ["Lecture slides", "Practice exams", "covered through page"],
    "Library": ["Lecture slides", "Practice exams"],
    "Packet Catalog": ["Refresh dry-run catalog", "Cataloged PDFs"],
    "Grades": ["Course components", "Projected", "Exam 1", "i>clicker"],
    "Force Lab": ["Vector FBD", "Live free-body diagram", "Number of forces"],
    "Cursor Rules": ["Active .cursorrules", "Physics 140 Expert Mode"],
}


def main() -> None:
    fails: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)

        for name, needles in PAGES.items():
            loc = page.get_by_text(name, exact=True)
            if loc.count() == 0:
                fails.append(f"{name}: nav missing")
                continue
            loc.first.click()
            page.wait_for_timeout(1600)
            body = page.inner_text("body")
            for needle in needles:
                if needle not in body:
                    fails.append(f"{name}: missing '{needle}'")
            print(f"[UI] {name}: checked {len(needles)} markers")

        browser.close()

    if fails:
        print("UI FAILURES:")
        for f in fails:
            print(" -", f)
        raise SystemExit(1)
    print("UI walk: all pages OK")


if __name__ == "__main__":
    main()
