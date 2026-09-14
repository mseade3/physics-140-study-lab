"""Render PDF pages to PNG so study/quiz can use diagrams, not only text."""

from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / "data" / "page_images"


def _pdf_key(pdf_path: Path) -> str:
    st = pdf_path.stat()
    raw = f"{pdf_path.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def cache_dir_for(pdf_path: Path) -> Path:
    d = CACHE_ROOT / _pdf_key(Path(pdf_path))
    d.mkdir(parents=True, exist_ok=True)
    meta = d / "source.txt"
    if not meta.exists():
        meta.write_text(str(Path(pdf_path).resolve()))
    return d


def render_page(
    pdf_path: Path | str,
    page_1indexed: int,
    *,
    zoom: float = 1.7,
    force: bool = False,
) -> Path:
    """
    Rasterize a single 1-indexed page to PNG. Cached under data/page_images/.
    """
    import pymupdf

    pdf_path = Path(pdf_path)
    out_dir = cache_dir_for(pdf_path)
    out = out_dir / f"page_{page_1indexed:03d}.png"
    if out.exists() and not force:
        return out

    doc = pymupdf.open(str(pdf_path))
    try:
        idx = page_1indexed - 1
        if idx < 0 or idx >= doc.page_count:
            raise ValueError(f"Page {page_1indexed} out of range (1–{doc.page_count})")
        page = doc.load_page(idx)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        pix.save(str(out))
    finally:
        doc.close()
    return out


def render_range(
    pdf_path: Path | str,
    through_page: int,
    *,
    zoom: float = 1.7,
    progress_cb=None,
) -> list[Path]:
    """Render pages 1..through_page inclusive; return PNG paths in order."""
    import pymupdf

    pdf_path = Path(pdf_path)
    doc = pymupdf.open(str(pdf_path))
    try:
        n = doc.page_count
        through = max(0, min(int(through_page), n))
        out_dir = cache_dir_for(pdf_path)
        paths: list[Path] = []
        for page_no in range(1, through + 1):
            out = out_dir / f"page_{page_no:03d}.png"
            if not out.exists():
                page = doc.load_page(page_no - 1)
                pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
                pix.save(str(out))
            paths.append(out)
            if progress_cb:
                progress_cb(page_no, through)
    finally:
        doc.close()
    return paths


def image_for_page(pdf_path: Path | str, page_1indexed: int) -> Path | None:
    pdf_path = Path(pdf_path)
    candidate = cache_dir_for(pdf_path) / f"page_{page_1indexed:03d}.png"
    if candidate.exists():
        return candidate
    try:
        return render_page(pdf_path, page_1indexed)
    except Exception:
        return None
