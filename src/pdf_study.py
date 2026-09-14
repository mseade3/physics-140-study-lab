"""Extract lecture-slide text up through a covered page for study/quiz use."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class PageText:
    page: int  # 1-indexed
    text: str

    @property
    def title_guess(self) -> str:
        lines = [ln.strip() for ln in self.text.splitlines() if ln.strip()]
        return lines[0] if lines else f"Page {self.page}"


def _clean(text: str) -> str:
    text = text.replace("\uf072", "").replace("\uf050", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


@lru_cache(maxsize=32)
def extract_pages(path_str: str, through_page: int) -> tuple[PageText, ...]:
    """Return cleaned text for pages 1..through_page inclusive."""
    from pypdf import PdfReader

    path = Path(path_str)
    reader = PdfReader(str(path))
    n = len(reader.pages)
    through = max(0, min(int(through_page), n))
    out: list[PageText] = []
    for i in range(through):
        raw = reader.pages[i].extract_text() or ""
        cleaned = _clean(raw)
        if cleaned:
            out.append(PageText(page=i + 1, text=cleaned))
    return tuple(out)


def combined_corpus(pages: tuple[PageText, ...] | list[PageText]) -> str:
    parts = [f"[Slide p.{p.page}] {p.text}" for p in pages]
    return "\n\n".join(parts)


def page_index(pages: tuple[PageText, ...] | list[PageText]) -> dict[int, str]:
    return {p.page: p.text for p in pages}


def summarize_coverage(pages: tuple[PageText, ...] | list[PageText]) -> dict:
    titles = [p.title_guess for p in pages[:8]]
    word_count = sum(len(p.text.split()) for p in pages)
    return {
        "page_count": len(pages),
        "word_count": word_count,
        "sample_titles": titles,
    }
