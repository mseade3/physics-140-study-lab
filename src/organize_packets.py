"""
Organize local Problem Roulette / practice-exam PDFs already in practice_exams/.

No network access. Operates only on files you place in the folder.

Usage (from project root):
    python -m src.organize_packets
    python -m src.organize_packets --apply
    python -m src.organize_packets --apply --move-into-topics
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PRACTICE_DIR = ROOT / "practice_exams"
DATA_DIR = ROOT / "data"
CATALOG_JSON = DATA_DIR / "packet_catalog.json"
CATALOG_CSV = DATA_DIR / "packet_catalog.csv"

# Filename / text hints → topic folder slug
TOPIC_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("01_kinematics", re.compile(r"kinematic|projectile|1[Dd]|2[Dd]|motion", re.I)),
    ("02_newtons_laws", re.compile(r"newton|fbd|force|dynamics", re.I)),
    ("03_friction_incline", re.compile(r"friction|incline|ramp|\bmu\b|μ", re.I)),
    ("04_work_energy", re.compile(r"work|energy|potential|kinetic|conserv", re.I)),
    ("05_momentum", re.compile(r"momentum|collision|impulse|rocket", re.I)),
    ("06_rotation", re.compile(r"rotat|torque|angular|inertia|moment of", re.I)),
    ("07_midterm", re.compile(r"midterm|mt\s*\d|exam\s*\d", re.I)),
    ("08_final", re.compile(r"final|cumulative", re.I)),
    ("09_problem_roulette", re.compile(r"roulette|pr[_-]?\d|problem.?set", re.I)),
]


@dataclass
class PacketRecord:
    original_name: str
    current_path: str
    suggested_name: str
    topic: str
    size_bytes: int
    page_count: int | None
    sha256_12: str
    text_preview: str
    renamed: bool
    moved: bool


def sha256_12(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def pdf_meta(path: Path) -> tuple[int | None, str]:
    if PdfReader is None:
        return None, ""
    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        chunks: list[str] = []
        for page in reader.pages[:3]:
            text = page.extract_text() or ""
            chunks.append(text)
        preview = re.sub(r"\s+", " ", " ".join(chunks)).strip()[:400]
        return pages, preview
    except Exception:
        return None, ""


def slugify(name: str) -> str:
    stem = Path(name).stem
    stem = stem.replace(" ", "_")
    stem = re.sub(r"[^\w\-.]+", "_", stem, flags=re.UNICODE)
    stem = re.sub(r"_+", "_", stem).strip("._-").lower()
    return stem or "packet"


def infer_topic(filename: str, preview: str) -> str:
    blob = f"{filename} {preview}"
    for topic, pattern in TOPIC_RULES:
        if pattern.search(blob):
            return topic
    return "00_unsorted"


def suggested_filename(path: Path, topic: str, digest: str) -> str:
    base = slugify(path.name)
    # Avoid double-appending digest
    if digest in base:
        return f"{base}.pdf"
    return f"{base}__{digest}.pdf"


def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 2
    while True:
        candidate = dest.with_name(f"{stem}_{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def iter_pdfs(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.pdf") if p.is_file())


def organize(
    apply: bool = False,
    move_into_topics: bool = False,
    practice_dir: Path = PRACTICE_DIR,
) -> list[PacketRecord]:
    practice_dir.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    records: list[PacketRecord] = []
    for path in iter_pdfs(practice_dir):
        digest = sha256_12(path)
        pages, preview = pdf_meta(path)
        topic = infer_topic(path.name, preview)
        new_name = suggested_filename(path, topic, digest)

        target_dir = practice_dir / topic if move_into_topics else path.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = unique_dest(target_dir / new_name)

        renamed = False
        moved = False
        final_path = path

        needs_rename = path.name != new_name or path.resolve() != dest.resolve()
        if apply and needs_rename:
            # If only casing/path differs within same folder without topic move
            if path.resolve() != dest.resolve():
                shutil.move(str(path), str(dest))
                final_path = dest
                renamed = path.name != dest.name
                moved = path.parent.resolve() != dest.parent.resolve()
            else:
                final_path = path
        elif not apply:
            final_path = dest if needs_rename else path

        records.append(
            PacketRecord(
                original_name=path.name,
                current_path=str(final_path.relative_to(ROOT))
                if apply
                else str(path.relative_to(ROOT)),
                suggested_name=str(dest.relative_to(ROOT)),
                topic=topic,
                size_bytes=path.stat().st_size if path.exists() else final_path.stat().st_size,
                page_count=pages,
                sha256_12=digest,
                text_preview=preview,
                renamed=renamed,
                moved=moved,
            )
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "practice_dir": str(practice_dir.relative_to(ROOT)),
        "apply": apply,
        "move_into_topics": move_into_topics,
        "packet_count": len(records),
        "packets": [asdict(r) for r in records],
    }
    CATALOG_JSON.write_text(json.dumps(payload, indent=2))
    with CATALOG_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "original_name",
                "current_path",
                "suggested_name",
                "topic",
                "size_bytes",
                "page_count",
                "sha256_12",
                "renamed",
                "moved",
            ],
        )
        writer.writeheader()
        for r in records:
            row = asdict(r)
            row.pop("text_preview", None)
            writer.writerow(row)

    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index and optionally rename/sort local practice_exams PDFs."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply renames (and topic moves if requested). Default is dry-run.",
    )
    parser.add_argument(
        "--move-into-topics",
        action="store_true",
        help="Place files under practice_exams/<topic>/ when applying.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=PRACTICE_DIR,
        help="Override practice exams directory.",
    )
    args = parser.parse_args()

    records = organize(
        apply=args.apply,
        move_into_topics=args.move_into_topics,
        practice_dir=args.dir.resolve(),
    )

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[{mode}] {len(records)} PDF(s) under {args.dir}")
    if not records:
        print("Drop Problem Roulette / practice PDFs into practice_exams/ and re-run.")
    for r in records:
        flag = ""
        if r.renamed or r.moved:
            flag = " *updated*"
        elif not args.apply and r.original_name != Path(r.suggested_name).name:
            flag = " → would rename/move"
        print(f"  - {r.original_name}  [{r.topic}]{flag}")
        if not args.apply:
            print(f"      suggested: {r.suggested_name}")
    print(f"Catalog: {CATALOG_JSON.relative_to(ROOT)}")
    print(f"CSV:     {CATALOG_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
