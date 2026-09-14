"""
PHYSICS 140 Study Lab — visual Streamlit dashboard.

Run from project root:
    streamlit run app.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from src.organize_packets import CATALOG_CSV, CATALOG_JSON, organize
from src.pdf_study import extract_pages, summarize_coverage
from src.physics_solver import (
    Force2D,
    acceleration_from_forces,
    force_from_magnitude_angle,
    inclined_plane_accel,
    net_force,
    projectile_trajectory,
)
from src.quiz_engine import QuizItem, build_quiz, grade_cloze
from src.syllabus import (
    ASSESSMENT_UNITS,
    CLASS,
    COURSE,
    EXAMS,
    GRADE_WEIGHTS,
    HELP_ROOM,
    INSTRUCTOR,
    MATERIALS,
    POLICIES,
    SSO,
    TOPICS,
    letter_grade,
    projected_course_percent,
)

ROOT = Path(__file__).resolve().parent
SLIDES_DIR = ROOT / "slides"
PRACTICE_DIR = ROOT / "practice_exams"
DATA_DIR = ROOT / "data"
PROGRESS_PATH = DATA_DIR / "progress.json"
RULES_PATH = ROOT / ".cursorrules"

BLUE = "#00274C"
MAIZE = "#FFCB05"
INK = "#122033"
MUTED = "#5C6B7A"
SURFACE = "#F3F6FA"
PLOT_BG = "#E8EEF5"
ACCENT_LINE = "#0E6E8C"

PAGES = [
    "Command Center",
    "Syllabus",
    "Study",
    "Coverage",
    "Library",
    "Packet Catalog",
    "Grades",
    "Force Lab",
    "Cursor Rules",
]


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=Source+Sans+3:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Source Sans 3', sans-serif;
        }}
        .stApp {{
            background:
                radial-gradient(ellipse 80% 50% at 100% -10%, rgba(255,203,5,0.16), transparent 55%),
                radial-gradient(ellipse 60% 40% at -10% 30%, rgba(0,39,76,0.08), transparent 50%),
                {SURFACE};
        }}
        .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(165deg, {BLUE} 0%, #013a63 48%, #0a4f7c 100%);
            border-right: 1px solid rgba(255,203,5,0.25);
        }}
        [data-testid="stSidebar"] * {{ color: #F5F7FA !important; }}
        [data-testid="stSidebar"] .stRadio label {{
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{
            padding: 0.35rem 0.5rem;
            border-radius: 8px;
        }}
        .hero {{
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(120deg, rgba(255,203,5,0.18), transparent 40%),
                linear-gradient(145deg, {BLUE} 0%, #0b3d66 58%, #146087 100%);
            color: #fff;
            border-radius: 14px;
            padding: 0.95rem 1.35rem 0.95rem;
            margin-bottom: 0.85rem;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .hero::after {{
            content: "";
            position: absolute;
            right: -30px; top: -50px;
            width: 110px; height: 110px;
            border-radius: 50%;
            background: rgba(255,203,5,0.12);
        }}
        .hero h1 {{
            font-family: 'Source Serif 4', serif;
            font-size: 1.55rem;
            margin: 0 0 0.2rem 0;
            letter-spacing: -0.02em;
            color: #fff;
            position: relative;
            z-index: 1;
        }}
        .hero p {{
            margin: 0;
            opacity: 0.92;
            font-size: 0.92rem;
            max-width: 46rem;
            position: relative;
            z-index: 1;
            line-height: 1.35;
        }}
        .hero .brand {{
            display: inline-block;
            background: {MAIZE};
            color: {BLUE};
            font-weight: 700;
            font-size: 0.68rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 0.22rem 0.55rem;
            border-radius: 3px;
            margin-bottom: 0.45rem;
            position: relative;
            z-index: 1;
        }}
        [data-testid="stFileUploader"] section {{
            background: linear-gradient(180deg, #fff 0%, {PLOT_BG} 100%) !important;
            border: 2px dashed rgba(0,39,76,0.35) !important;
            border-radius: 14px !important;
            padding: 0.85rem !important;
        }}
        [data-testid="stFileUploader"] section:hover {{
            border-color: {MAIZE} !important;
            background: #fffef6 !important;
        }}
        [data-testid="stFileUploader"] button {{
            background: {BLUE} !important;
            color: #fff !important;
            border: none !important;
        }}
        [data-testid="stToolbar"] {{ display: none !important; }}
        header[data-testid="stHeader"] {{ background: transparent; }}
        .stat-card {{
            background: rgba(255,255,255,0.92);
            border: 1px solid #d5dee8;
            border-top: 3px solid {MAIZE};
            border-radius: 14px;
            padding: 1rem 1.05rem;
            height: 100%;
            backdrop-filter: blur(6px);
        }}
        .stat-card .label {{
            color: {MUTED};
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            font-weight: 700;
        }}
        .stat-card .value {{
            color: {BLUE};
            font-family: 'Source Serif 4', serif;
            font-size: 1.9rem;
            font-weight: 700;
            line-height: 1.1;
            margin-top: 0.28rem;
        }}
        .stat-card .hint {{
            color: {MUTED};
            font-size: 0.84rem;
            margin-top: 0.35rem;
        }}
        .panel {{
            background: rgba(255,255,255,0.95);
            border: 1px solid #d5dee8;
            border-radius: 16px;
            padding: 1.05rem 1.15rem 1.15rem;
            margin-bottom: 0.95rem;
        }}
        .panel h3 {{
            font-family: 'Source Serif 4', serif;
            color: {BLUE};
            margin: 0 0 0.7rem 0;
            font-size: 1.22rem;
        }}
        .progress-shell {{
            background: #d9e2ec;
            border-radius: 999px;
            height: 10px;
            overflow: hidden;
            margin: 0.45rem 0 0.2rem;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {ACCENT_LINE}, {MAIZE});
            border-radius: 999px;
        }}
        .cov-row {{
            padding: 0.85rem 0;
            border-bottom: 1px solid #e4ebf3;
        }}
        .cov-row:last-child {{ border-bottom: none; }}
        .cov-title {{
            color: {BLUE};
            font-weight: 600;
            font-size: 0.98rem;
        }}
        .cov-meta {{
            color: {MUTED};
            font-size: 0.84rem;
        }}
        .empty-state {{
            background: {PLOT_BG};
            border: 1px dashed #aebcce;
            border-radius: 12px;
            padding: 1.3rem;
            color: {MUTED};
            text-align: center;
        }}
        .topic-chip {{
            display: inline-block;
            background: {BLUE};
            color: #fff;
            border-radius: 999px;
            padding: 0.28rem 0.75rem;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 0.15rem;
            border: 1px solid rgba(0,39,76,0.2);
        }}
        .topic-chip.warn {{
            background: #7a1f1f;
        }}
        .topic-chip.soft {{
            background: {PLOT_BG};
            color: {BLUE};
            border: 1px solid #c9d5e3;
        }}
        .scroll-panel {{
            max-height: 520px;
            overflow-y: auto;
            padding-right: 0.4rem;
            border: 1px solid #d5dee8;
            border-radius: 12px;
            padding: 0.75rem;
            background: rgba(255,255,255,0.9);
        }}
        .rules-preview {{
            background: {PLOT_BG};
            border: 1px solid #c9d5e3;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.78rem;
            color: {INK};
            white-space: pre-wrap;
            line-height: 1.45;
            margin-top: 0.5rem;
        }}
        .sidebar-cite {{
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,203,5,0.35);
            border-radius: 10px;
            padding: 0.65rem 0.7rem;
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.5rem;
        }}
        .workspace-link {{
            display: block;
            padding: 0.45rem 0;
            border-bottom: 1px solid #e4ebf3;
            color: {BLUE};
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .workspace-link:last-child {{ border-bottom: none; }}
        .file-row {{
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.55rem 0.15rem;
            border-bottom: 1px solid #e8edf3;
            font-size: 0.92rem;
        }}
        .file-row:last-child {{ border-bottom: none; }}
        .file-name {{ color: {BLUE}; font-weight: 600; }}
        .file-meta {{ color: {MUTED}; white-space: nowrap; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_dirs() -> None:
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    PRACTICE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_progress() -> dict:
    ensure_dirs()
    default_components = {u["id"]: None for u in ASSESSMENT_UNITS}
    default = {
        "scores": [],
        "topic_confidence": {t: 3 for t in TOPICS},
        "hours_logged": 0.0,
        "notes": "",
        "pdf_coverage": {},
        "components": default_components,
    }
    if not PROGRESS_PATH.exists():
        return default
    with PROGRESS_PATH.open() as f:
        data = json.load(f)
    for k, v in default.items():
        data.setdefault(k, v if not isinstance(v, dict) else dict(v))
    for t in TOPICS:
        data["topic_confidence"].setdefault(t, 3)
    data.setdefault("pdf_coverage", {})
    data.setdefault("components", dict(default_components))
    for cid in default_components:
        data["components"].setdefault(cid, None)
    return data


def save_progress(data: dict) -> None:
    ensure_dirs()
    with PROGRESS_PATH.open("w") as f:
        json.dump(data, f, indent=2)


def list_pdfs(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*.pdf") if p.is_file())


def coverage_key(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def get_coverage(progress: dict, path: Path, total_pages: int) -> int:
    key = coverage_key(path)
    entry = progress.get("pdf_coverage", {}).get(key, {})
    covered = int(entry.get("covered_through", 0))
    return max(0, min(covered, total_pages))


def set_coverage(progress: dict, path: Path, covered: int, total_pages: int) -> None:
    key = coverage_key(path)
    progress.setdefault("pdf_coverage", {})
    progress["pdf_coverage"][key] = {
        "covered_through": int(covered),
        "total_pages": int(total_pages),
        "updated": date.today().isoformat(),
        "kind": "slides" if "slides" in key else "practice",
    }
    save_progress(progress)


def coverage_summary(progress: dict, folder: Path) -> tuple[int, int, float]:
    files = list_pdfs(folder)
    covered_sum = 0
    total_sum = 0
    for p in files:
        pages = pdf_page_count(p) or 0
        if pages <= 0:
            continue
        total_sum += pages
        covered_sum += get_coverage(progress, p, pages)
    pct = (100.0 * covered_sum / total_sum) if total_sum else 0.0
    return covered_sum, total_sum, pct


def save_upload(uploaded, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / uploaded.name
    path.write_bytes(uploaded.getbuffer())
    return path


@st.cache_data(show_spinner=False)
def pdf_page_count(path_str: str) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(path_str).pages)
    except Exception:
        return None


def pages_of(path: Path) -> int:
    return pdf_page_count(str(path.resolve())) or 0


def load_catalog() -> dict:
    if not CATALOG_JSON.exists():
        return {"packet_count": 0, "packets": [], "generated_at": None}
    with CATALOG_JSON.open() as f:
        return json.load(f)


def style_figure(ax) -> None:
    ax.set_facecolor(PLOT_BG)
    ax.grid(True, alpha=0.32, linestyle="--", color="#9aabbc")
    ax.axhline(0, color=BLUE, linewidth=0.8)
    ax.axvline(0, color=BLUE, linewidth=0.8)
    for spine in ax.spines.values():
        spine.set_color("#9aabbc")


def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024**2:.1f} MB"


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="brand">UMich · PHYSICS 140</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, hint: str = "") -> None:
    hint_html = f'<div class="hint">{hint}</div>' if hint else ""
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def progress_bar_html(pct: float) -> str:
    pct = max(0.0, min(100.0, pct))
    return (
        f'<div class="progress-shell"><div class="progress-fill" '
        f'style="width:{pct:.1f}%"></div></div>'
    )


def coverage_figure(progress: dict):
    rows = []
    for folder, label in ((SLIDES_DIR, "Slides"), (PRACTICE_DIR, "Practice")):
        for p in list_pdfs(folder):
            total = pages_of(p)
            if total <= 0:
                continue
            covered = get_coverage(progress, p, total)
            rows.append(
                {
                    "label": f"{label[:3]} · {p.stem.replace('_', ' ')[:22]}",
                    "pct": 100.0 * covered / total,
                    "covered": covered,
                    "total": total,
                }
            )
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r["pct"])
    fig, ax = plt.subplots(figsize=(8, max(2.8, 0.42 * len(rows) + 1.2)))
    style_figure(ax)
    y = np.arange(len(rows))
    ax.barh(y, [r["pct"] for r in rows], color=ACCENT_LINE, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows], fontsize=8.5)
    ax.set_xlim(0, 105)
    ax.set_xlabel("% of pages covered")
    ax.set_title("Curriculum coverage by PDF", color=BLUE, fontweight="bold")
    for i, r in enumerate(rows):
        ax.text(min(r["pct"] + 1.5, 92), i, f"{r['covered']}/{r['total']}", va="center", fontsize=8, color=INK)
    fig.tight_layout()
    return fig


def confidence_figure(progress: dict):
    topics = list(progress["topic_confidence"].keys())
    vals = [progress["topic_confidence"][t] for t in topics]
    colors = [
        "#b42318" if v <= 2 else MAIZE if v == 3 else "#1f7a4c" for v in vals
    ]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    style_figure(ax)
    y = np.arange(len(topics))
    ax.barh(y, vals, color=colors, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(topics, fontsize=9)
    ax.set_xlim(0, 5.5)
    ax.set_xlabel("Confidence (1–5)")
    ax.set_title("Topic readiness", color=BLUE, fontweight="bold")
    fig.tight_layout()
    return fig


def scores_figure(scores: list[dict]):
    df = pd.DataFrame(scores)
    fig, ax = plt.subplots(figsize=(8, 3.1))
    style_figure(ax)
    ax.plot(df["date"], df["score"], marker="o", color=BLUE, linewidth=2.2, markersize=7)
    ax.fill_between(df["date"], df["score"], alpha=0.12, color=ACCENT_LINE)
    ax.axhline(70, color="#b42318", linestyle=":", linewidth=1.2, label="70% line")
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Assessment trajectory", color=BLUE, fontweight="bold")
    ax.legend(frameon=False, loc="lower right")
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


def render_coverage_controls(progress: dict, folder: Path, kind_label: str) -> None:
    files = list_pdfs(folder)
    if not files:
        st.markdown(
            f'<div class="empty-state">No {kind_label} PDFs yet. Upload on the Library page '
            f"or drop files into <code>{folder.name}/</code>.</div>",
            unsafe_allow_html=True,
        )
        return

    for p in files:
        total = pages_of(p)
        if total <= 0:
            st.warning(f"Could not read page count for `{p.name}`")
            continue
        current = get_coverage(progress, p, total)
        pct = 100.0 * current / total
        st.markdown(
            f'<div class="cov-row"><div class="cov-title">{p.relative_to(folder)}</div>'
            f'<div class="cov-meta">{total} pages · {pct:.0f}% covered</div>'
            f"{progress_bar_html(pct)}</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns((3, 1, 1))
        with cols[0]:
            new_val = st.slider(
                f"Covered through page — {p.name}",
                min_value=0,
                max_value=total,
                value=current,
                key=f"cov_{coverage_key(p)}",
                help="Set the last page/slide you have finished in class or study.",
            )
        with cols[1]:
            if st.button("Mark done", key=f"done_{coverage_key(p)}"):
                set_coverage(progress, p, total, total)
                st.rerun()
        with cols[2]:
            if st.button("Reset", key=f"reset_{coverage_key(p)}"):
                set_coverage(progress, p, 0, total)
                st.rerun()
        if new_val != current:
            set_coverage(progress, p, new_val, total)
            st.rerun()


def days_until(iso_date: str) -> int:
    target = date.fromisoformat(iso_date)
    return (target - date.today()).days


def next_exam() -> dict | None:
    upcoming = [e for e in EXAMS if days_until(e["regular_date"]) >= 0]
    return upcoming[0] if upcoming else (EXAMS[-1] if EXAMS else None)


def page_command_center(progress: dict) -> None:
    hero(
        f"{COURSE['code']} Study Lab",
        f"{COURSE['term']} · {INSTRUCTOR['name']} · {CLASS['days']} {CLASS['time']} · {CLASS['room']}",
    )
    st.warning(COURSE["warning"])

    slides = list_pdfs(SLIDES_DIR)
    packets = list_pdfs(PRACTICE_DIR)
    sc, stot, spct = coverage_summary(progress, SLIDES_DIR)
    pc, ptot, ppct = coverage_summary(progress, PRACTICE_DIR)
    comps = progress.get("components", {})
    proj = projected_course_percent(comps)
    nxt = next_exam()
    weak = sorted(progress["topic_confidence"].items(), key=lambda kv: kv[1])[:2]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if nxt:
            d = days_until(nxt["regular_date"])
            hint = f"{nxt['regular_weekday']} {nxt['regular_date']}"
            stat_card(
                "Next exam",
                f"{d}d" if d >= 0 else "done",
                f"{nxt['label']} · {hint}",
            )
        else:
            stat_card("Next exam", "—", "")
    with c2:
        stat_card(
            "Projected grade",
            f"{letter_grade(proj)} · {proj:.0f}%" if proj is not None else "—",
            "from entered components · Grades page",
        )
    with c3:
        stat_card("Slide coverage", f"{spct:.0f}%", f"{sc}/{stot or 0} pp · {len(slides)} PDFs")
    with c4:
        stat_card("Practice coverage", f"{ppct:.0f}%", f"{pc}/{ptot or 0} pp · {len(packets)} PDFs")

    left, right = st.columns((1.15, 1))
    with left:
        st.markdown(
            f"""
            <div class="panel">
              <h3>Exam calendar</h3>
              {"".join(
                  f'<div class="workspace-link"><b>{e["label"]}</b> · {e["regular_weekday"]} {e["regular_date"]} · '
                  f'{e["regular_time"]} · room {e["room"]} · in {days_until(e["regular_date"])}d</div>'
                  for e in EXAMS
              )}
              <div class="cov-meta" style="margin-top:0.5rem">{POLICIES["no_drops_exams_hw"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="panel">
              <h3>Grade weights</h3>
              {"".join(
                  f'<div class="workspace-link">{w["label"]} · <b>{int(w["weight"]*100)}%</b></div>'
                  for w in GRADE_WEIGHTS
              )}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"""
            <div class="panel">
              <h3>Help Room · {HELP_ROOM["location"]}</h3>
              <div class="cov-meta">Starts {HELP_ROOM["starts"]} · office hours daily</div>
              {"".join(f'<div class="workspace-link">{h["day"]} · {h["time"]}</div>' for h in HELP_ROOM["hours"])}
              <div class="workspace-link">Instructor · {INSTRUCTOR["email"]} · {INSTRUCTOR["office"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig = coverage_figure(progress)
        if fig is not None:
            st.pyplot(fig, width="stretch")
            plt.close(fig)
        else:
            st.markdown(
                '<div class="empty-state">Drop lecture/practice PDFs into <code>slides/</code> or '
                "<code>practice_exams/</code>, then set page coverage.</div>",
                unsafe_allow_html=True,
            )
        if weak:
            st.markdown(
                " ".join(f'<span class="topic-chip">Focus: {t} ({v}/5)</span>' for t, v in weak),
                unsafe_allow_html=True,
            )
        if progress.get("notes"):
            st.info(progress["notes"][:280])


def page_syllabus() -> None:
    hero(
        "Syllabus",
        f"{COURSE['code']} ({COURSE['program']}) · {COURSE['term']} · "
        f"Instructor {INSTRUCTOR['name']} ({INSTRUCTOR['preferred']})",
    )
    st.warning(COURSE["warning"])

    a, b = st.columns(2)
    with a:
        st.markdown(
            f"""
            <div class="panel">
              <h3>Class</h3>
              <div class="workspace-link">{CLASS["days"]} · {CLASS["time"]}</div>
              <div class="workspace-link">{CLASS["room"]}</div>
              <div class="workspace-link">{INSTRUCTOR["name"]} · {INSTRUCTOR["email"]}</div>
              <div class="workspace-link">Office · {INSTRUCTOR["office"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="panel">
              <h3>Materials</h3>
              {"".join(
                  f'<div class="workspace-link"><b>{m["name"]}</b><br/><span class="cov-meta">{m["detail"]}</span></div>'
                  for m in MATERIALS
              )}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with b:
        st.markdown(
            f"""
            <div class="panel">
              <h3>Help Room · {HELP_ROOM["location"]}</h3>
              {"".join(f'<div class="workspace-link">{h["day"]} · {h["time"]}</div>' for h in HELP_ROOM["hours"])}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="panel">
              <h3>Physics SSO</h3>
              <div class="workspace-link">{SSO["name"]}</div>
              <div class="workspace-link">{SSO["location"]}</div>
              <div class="workspace-link">{SSO["email"]}</div>
              <div class="workspace-link">{", ".join(SSO["phones"])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="panel"><h3>Exams (Canvas MC quizzes)</h3></div>', unsafe_allow_html=True)
    exam_rows = []
    for e in EXAMS:
        exam_rows.append(
            {
                "Exam": e["label"],
                "Date": f"{e['regular_weekday']} {e['regular_date']}",
                "Time": e["regular_time"],
                "Room": e["room"],
                "Formula aid": e["index_cards"],
                "Alternate": e["alternate"],
                "Days out": days_until(e["regular_date"]),
            }
        )
    st.dataframe(pd.DataFrame(exam_rows), width="stretch", hide_index=True)
    st.caption(POLICIES["formula_aid"])

    w1, w2 = st.columns(2)
    with w1:
        st.markdown('<div class="panel"><h3>Grade contributions</h3></div>', unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame(
                [{"Component": w["label"], "Weight": f"{int(w['weight']*100)}%"} for w in GRADE_WEIGHTS]
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption(POLICIES["no_drops_exams_hw"])
        st.caption(POLICIES["iclicker_drops"])
    with w2:
        st.markdown('<div class="panel"><h3>Letter scale</h3></div>', unsafe_allow_html=True)
        from src.syllabus import GRADE_SCALE

        st.dataframe(
            pd.DataFrame(
                [{"Letter": letter, "Score must be >": f"{lower}%"} for letter, lower in GRADE_SCALE]
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption(POLICIES["curve_note"])

    st.info(POLICIES["rhamuep"])
    st.caption(f"RHAMUEP deadline · {POLICIES['rhamuep_deadline']} · {POLICIES['grade_dispute']}")


def page_study(progress: dict) -> None:
    hero(
        "Study",
        "Quizzes use real slide screenshots (diagrams, arrows, axes) up through the page "
        "you have covered — not text alone.",
    )

    slides = list_pdfs(SLIDES_DIR)
    if not slides:
        st.markdown(
            '<div class="empty-state">No lecture PDFs yet. Upload one under <b>Library</b> '
            "(or drop it into <code>slides/</code>), set coverage, then come back here.</div>",
            unsafe_allow_html=True,
        )
        return

    from src.pdf_render import image_for_page, render_range
    from src.vision_quiz import build_quiz_from_slide_images, vision_available

    names = {p.name: p for p in slides}
    choice = st.selectbox("Lecture PDF", options=list(names.keys()))
    path = names[choice]
    total = pages_of(path)
    if total <= 0:
        st.error("Could not read this PDF’s page count.")
        return

    covered = get_coverage(progress, path, total)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        through = st.number_input(
            "Study through page",
            min_value=1,
            max_value=total,
            value=max(1, covered) if covered > 0 else min(5, total),
            help="Only pages 1…N are rendered and used for the quiz.",
        )
    with c2:
        n_q = st.slider("Questions this session", 4, 15, 8)
    with c3:
        mode = st.selectbox(
            "Quiz mode",
            [
                "Diagrams + hybrid quiz",
                "Vision quiz (needs API key)",
            ],
            help="Hybrid shows slide pictures on every question. Vision asks a model to write diagram-aware items.",
        )
    with c4:
        sync = st.checkbox("Also save as Coverage", value=True)

    st.caption(
        f"`{path.name}` · {total} pages · quiz scope **1–{through}**"
        + (f" · saved coverage {covered}/{total}" if covered else "")
    )

    # Render slide screenshots for the covered range
    render_box = st.empty()
    with st.spinner(f"Rendering slide images for pages 1–{through}…"):
        bar = st.progress(0.0)

        def _cb(done: int, total_n: int) -> None:
            bar.progress(done / max(total_n, 1))

        image_paths = render_range(path, int(through), progress_cb=_cb)
        bar.progress(1.0)
    image_map = {}
    for ip in image_paths:
        # page_003.png -> 3
        try:
            num = int(ip.stem.split("_")[1])
            image_map[num] = str(ip)
        except (IndexError, ValueError):
            continue
    render_box.success(f"Ready · {len(image_paths)} slide screenshot(s) cached")

    pages = extract_pages(str(path.resolve()), int(through))
    summary = summarize_coverage(pages)
    m1, m2, m3 = st.columns(3)
    with m1:
        stat_card("Pages in scope", str(len(image_paths)), f"of {total} in file")
    with m2:
        stat_card("Diagrams ready", str(len(image_map)), "PNG screenshots")
    with m3:
        stat_card("Text words", str(summary["word_count"]), "optional backup signal")

    with st.expander("Preview slide diagrams in scope", expanded=True):
        if not image_paths:
            st.write("No pages rendered.")
        else:
            # show up to 6 thumbs
            show = image_paths[:6]
            cols = st.columns(min(3, len(show)))
            for i, ip in enumerate(show):
                with cols[i % len(cols)]:
                    st.image(str(ip), caption=ip.stem.replace("_", " "), width="stretch")
            if len(image_paths) > 6:
                st.caption(f"…and {len(image_paths) - 6} more page(s) in this quiz scope.")

    if mode.startswith("Vision") and not vision_available():
        st.warning(
            "Vision quiz needs `OPENAI_API_KEY` in your environment "
            "(optional: `OPENAI_VISION_MODEL`, default `gpt-4o-mini`). "
            "Hybrid mode still shows full slide diagrams without a key."
        )

    gen_col, reset_col = st.columns(2)
    start = gen_col.button(
        f"Generate quiz from slide images 1–{through}",
        type="primary",
    )
    if reset_col.button("Reset session"):
        for k in list(st.session_state.keys()):
            if str(k).startswith("study_"):
                st.session_state.pop(k, None)
        st.rerun()

    if start:
        if sync:
            set_coverage(progress, path, int(through), total)
        items: list[QuizItem] = []
        err = None
        if mode.startswith("Vision"):
            try:
                with st.spinner("Asking vision model to read your slide diagrams…"):
                    items = build_quiz_from_slide_images(image_paths, n_questions=int(n_q))
                    # ensure every item has an image
                    for q in items:
                        if not q.image_path:
                            q.image_path = image_map.get(q.source_page, "")
                            if not q.image_path and image_paths:
                                q.image_path = str(image_paths[min(q.source_page - 1, len(image_paths) - 1)])
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                st.error(err)
                st.info("Falling back to hybrid quiz with diagrams attached.")
        if not items:
            items = build_quiz(
                pages,
                n_questions=int(n_q),
                include_teach=True,
                image_map=image_map,
            )
        st.session_state.study_quiz = [q.to_dict() for q in items]
        st.session_state.study_idx = 0
        st.session_state.study_correct = 0
        st.session_state.study_done = False
        st.session_state.study_meta = {
            "file": path.name,
            "through": int(through),
            "total": total,
            "mode": mode,
        }
        st.rerun()

    quiz_raw = st.session_state.get("study_quiz")
    if not quiz_raw:
        st.info("Generate a quiz to begin. Each question shows the source slide diagram.")
        return

    items = [QuizItem.from_dict(d) for d in quiz_raw]
    idx = int(st.session_state.get("study_idx", 0))
    correct = int(st.session_state.get("study_correct", 0))
    meta = st.session_state.get("study_meta", {})

    st.markdown(
        f"**Session:** `{meta.get('file', path.name)}` · pages 1–{meta.get('through', through)} "
        f"· {meta.get('mode', mode)} · Q {min(idx + 1, len(items))}/{len(items)} · score {correct}"
    )
    st.progress(min(idx / max(len(items), 1), 1.0))

    if st.session_state.get("study_done") or idx >= len(items):
        pct = 100.0 * correct / max(len(items), 1)
        st.success(f"Session complete · **{correct}/{len(items)}** ({pct:.0f}%)")
        if pct < 70:
            st.warning("Re-study the diagrams on weak pages, then generate again.")
        if st.button("New quiz with same page range"):
            st.session_state.pop("study_quiz", None)
            st.rerun()
        return

    q = items[idx]
    st.markdown(
        f'<div class="panel"><h3>Q{idx + 1} · {q.kind.upper()} · slide p.{q.source_page}</h3></div>',
        unsafe_allow_html=True,
    )

    # Diagram first — this is the point of the feature
    img = q.image_path
    if not img:
        maybe = image_for_page(path, q.source_page)
        img = str(maybe) if maybe else ""
    left, right = st.columns((1.25, 1))
    with left:
        if img and Path(img).exists():
            st.image(img, caption=f"Slide p.{q.source_page} (diagram)", width="stretch")
        else:
            st.warning("No diagram cached for this page.")
        else:
            st.warning("No diagram cached for this page.")
    with right:
        st.markdown(q.prompt)
        feedback_key = f"study_feedback_{idx}"
        answer_key = f"ans_{q.id}_{idx}"
        feedback = st.session_state.get(feedback_key)

        if q.kind in {"mcq", "tf", "teach"}:
            pick = st.radio("Your answer", q.choices, key=answer_key, disabled=bool(feedback))
        else:
            pick = st.text_area("Your answer", key=answer_key, height=100, disabled=bool(feedback))

        if not feedback and st.button("Check answer", type="primary", key=f"check_{idx}"):
            if q.kind == "cloze":
                good = grade_cloze(str(pick or ""), q.answer)
            else:
                good = pick == q.answer
            st.session_state[feedback_key] = {"good": good, "pick": pick}
            if good:
                st.session_state.study_correct = correct + 1
            st.rerun()

        feedback = st.session_state.get(feedback_key)
        if feedback:
            if feedback["good"]:
                st.success("Correct.")
            else:
                st.error("Not yet.")
                st.markdown(f"**Target answer:** {q.answer}")
            st.markdown(
                f"**Learn from the diagram (p.{q.source_page})**  \n"
                f"{q.explanation}  \n"
                f"_{q.source_excerpt}_"
            )
            if st.button("Next", type="primary", key=f"next_{idx}"):
                st.session_state.pop(feedback_key, None)
                st.session_state.study_idx = idx + 1
                if idx + 1 >= len(items):
                    st.session_state.study_done = True
                st.rerun()


def page_coverage(progress: dict) -> None:
    hero(
        "Coverage",
        "Choose how far you have gotten in each lecture deck and practice packet. "
        "Coverage feeds the Command Center so you always know what is left.",
    )
    sc, stot, spct = coverage_summary(progress, SLIDES_DIR)
    pc, ptot, ppct = coverage_summary(progress, PRACTICE_DIR)
    a, b = st.columns(2)
    with a:
        stat_card("Lectures", f"{spct:.0f}%", f"Through page totals {sc}/{stot or 0}")
    with b:
        stat_card("Practice exams", f"{ppct:.0f}%", f"Through page totals {pc}/{ptot or 0}")

    tab1, tab2 = st.tabs(["Lecture slides", "Practice exams"])
    with tab1:
        st.markdown('<div class="panel"><h3>Slides — covered through page</h3></div>', unsafe_allow_html=True)
        render_coverage_controls(progress, SLIDES_DIR, "lecture")
    with tab2:
        st.markdown('<div class="panel"><h3>Practice — covered through page</h3></div>', unsafe_allow_html=True)
        render_coverage_controls(progress, PRACTICE_DIR, "practice")

    fig = coverage_figure(progress)
    if fig is not None:
        st.pyplot(fig, width="stretch")
        plt.close(fig)


def page_library(progress: dict) -> None:
    hero(
        "Course library",
        "Upload lecture slides and practice packets. Files stay on disk for Cursor "
        "(@slides / @practice_exams). Set page coverage on the Coverage page.",
    )
    left, right = st.columns(2)
    with left:
        st.markdown('<div class="panel"><h3>Lecture slides</h3></div>', unsafe_allow_html=True)
        up = st.file_uploader("Upload lecture PDF", type=["pdf"], key="slides_up")
        if up is not None and st.button("Save to slides/", key="save_slides"):
            path = save_upload(up, SLIDES_DIR)
            total = pages_of(path)
            set_coverage(progress, path, 0, total or 1)
            pdf_page_count.clear()
            st.success(f"Saved `{path.name}` ({total} pages)")
            st.rerun()
        slides = list_pdfs(SLIDES_DIR)
        if not slides:
            st.markdown('<div class="empty-state">No lecture PDFs yet.</div>', unsafe_allow_html=True)
        for p in slides:
            total = pages_of(p)
            covered = get_coverage(progress, p, total) if total else 0
            pct = (100.0 * covered / total) if total else 0
            st.markdown(
                f'<div class="file-row"><span class="file-name">{p.name}</span>'
                f'<span class="file-meta">{covered}/{total} · {pct:.0f}%</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(progress_bar_html(pct), unsafe_allow_html=True)
            st.download_button(
                f"Download {p.name}",
                p.read_bytes(),
                file_name=p.name,
                mime="application/pdf",
                key=f"dl_slide_{p}",
            )

    with right:
        st.markdown('<div class="panel"><h3>Practice exams</h3></div>', unsafe_allow_html=True)
        up2 = st.file_uploader("Upload practice PDF", type=["pdf"], key="practice_up")
        if up2 is not None and st.button("Save to practice_exams/", key="save_practice"):
            path = save_upload(up2, PRACTICE_DIR)
            total = pages_of(path)
            set_coverage(progress, path, 0, total or 1)
            pdf_page_count.clear()
            st.success(f"Saved `{path.name}` ({total} pages)")
            st.rerun()
        packets = list_pdfs(PRACTICE_DIR)
        if not packets:
            st.markdown('<div class="empty-state">No practice PDFs yet.</div>', unsafe_allow_html=True)
        for p in packets:
            total = pages_of(p)
            covered = get_coverage(progress, p, total) if total else 0
            pct = (100.0 * covered / total) if total else 0
            st.markdown(
                f'<div class="file-row"><span class="file-name">{p.name}</span>'
                f'<span class="file-meta">{covered}/{total} · {pct:.0f}%</span></div>',
                unsafe_allow_html=True,
            )
            st.markdown(progress_bar_html(pct), unsafe_allow_html=True)
            st.download_button(
                f"Download {p.name}",
                p.read_bytes(),
                file_name=p.name,
                mime="application/pdf",
                key=f"dl_pr_{p}",
            )


def page_packet_catalog() -> None:
    hero(
        "Packet catalog",
        "Index local practice PDFs, preview topic tags, and optionally rename or "
        "sort into topic folders. Local files only — no scraping.",
    )
    move_topics = st.checkbox("When applying, move files into topic folders", value=False)
    c1, c2, c3 = st.columns(3)
    if c1.button("Refresh dry-run catalog", width="stretch"):
        organize(apply=False, move_into_topics=move_topics)
        st.success("Catalog refreshed.")
        st.rerun()
    if c2.button("Apply rename / sort", type="primary", width="stretch"):
        records = organize(apply=True, move_into_topics=move_topics)
        n = sum(1 for r in records if r.renamed or r.moved)
        st.success(f"Applied changes to {n} file(s).")
        st.rerun()
    if c3.button("Show folder path", width="stretch"):
        st.info(f"Drop PDFs here: `{PRACTICE_DIR}`")

    catalog = load_catalog()
    packets = catalog.get("packets", [])
    m1, m2, m3 = st.columns(3)
    with m1:
        stat_card("Cataloged PDFs", str(catalog.get("packet_count", 0)))
    with m2:
        topics = {p.get("topic", "00_unsorted") for p in packets}
        stat_card("Topic buckets", str(len(topics)) if packets else "0")
    with m3:
        pages = [p.get("page_count") or 0 for p in packets]
        stat_card("Total pages", str(sum(pages)) if packets else "0")

    if not packets:
        st.markdown(
            '<div class="empty-state">No packets indexed yet. Add PDFs under '
            "<code>practice_exams/</code>, then refresh the catalog.</div>",
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(packets)
    show_cols = [c for c in ["original_name", "topic", "page_count", "size_bytes", "suggested_name"] if c in df.columns]
    view = df[show_cols].copy()
    if "size_bytes" in view.columns:
        view["size"] = view["size_bytes"].map(fmt_bytes)
        view = view.drop(columns=["size_bytes"])

    topic_counts = df["topic"].value_counts().sort_index()
    if len(topic_counts) <= 3:
        st.markdown('<div class="panel"><h3>Topic tags</h3></div>', unsafe_allow_html=True)
        chips = " ".join(
            f'<span class="topic-chip">{topic} · {count}</span>'
            for topic, count in topic_counts.items()
        )
        st.markdown(chips or '<div class="empty-state">No topics yet.</div>', unsafe_allow_html=True)
    else:
        fig, ax = plt.subplots(figsize=(8, 3))
        style_figure(ax)
        ax.bar(topic_counts.index.astype(str), topic_counts.values, color=BLUE)
        ax.set_ylabel("PDFs")
        ax.set_title("Packets by inferred topic", color=BLUE, fontweight="bold")
        plt.xticks(rotation=25, ha="right")
        fig.tight_layout()
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    st.dataframe(view, width="stretch", hide_index=True)

    if CATALOG_CSV.exists():
        st.download_button(
            "Download catalog CSV",
            CATALOG_CSV.read_bytes(),
            file_name="packet_catalog.csv",
            mime="text/csv",
        )


def page_progress(progress: dict) -> None:
    hero(
        "Grades",
        "Enter Exam 1–4, Mastering Physics, and i>clicker averages. Weights follow the "
        "CSP syllabus (20% / 16% / 4×16%). No exams or HW dropped.",
    )
    comps = progress.setdefault("components", {u["id"]: None for u in ASSESSMENT_UNITS})

    st.markdown('<div class="panel"><h3>Course components</h3></div>', unsafe_allow_html=True)
    changed = False
    cols = st.columns(2)
    for i, unit in enumerate(ASSESSMENT_UNITS):
        with cols[i % 2]:
            raw = comps.get(unit["id"])
            enabled = st.checkbox(
                f"I have a score for {unit['label']}",
                value=raw is not None,
                key=f"en_{unit['id']}",
            )
            if enabled:
                val = st.slider(
                    f"{unit['label']} (%)",
                    0,
                    100,
                    int(raw) if raw is not None else 75,
                    key=f"sc_{unit['id']}",
                    help=unit["focus"],
                )
                if comps.get(unit["id"]) != val:
                    comps[unit["id"]] = int(val)
                    changed = True
            else:
                if comps.get(unit["id"]) is not None:
                    comps[unit["id"]] = None
                    changed = True

    if changed:
        progress["components"] = comps
        save_progress(progress)

    proj = projected_course_percent(comps)
    entered = sum(1 for v in comps.values() if v is not None)
    g1, g2, g3 = st.columns(3)
    with g1:
        stat_card("Components entered", f"{entered}/6", "exams + Mastering + i>clicker")
    with g2:
        stat_card(
            "Projected %",
            f"{proj:.1f}%" if proj is not None else "—",
            "renormalized over entered weights",
        )
    with g3:
        stat_card(
            "Letter (syllabus scale)",
            letter_grade(proj) if proj is not None else "—",
            "score must be > band floor",
        )

    weight_df = []
    for w in GRADE_WEIGHTS:
        score = comps.get(w["id"])
        weight_df.append(
            {
                "Component": w["label"],
                "Weight": f"{int(w['weight']*100)}%",
                "Your score": f"{score}%" if score is not None else "—",
                "Letter": letter_grade(float(score)) if score is not None else "—",
            }
        )
    st.dataframe(pd.DataFrame(weight_df), width="stretch", hide_index=True)
    st.caption(POLICIES["curve_note"])

    st.markdown("---")
    st.markdown('<div class="panel"><h3>Practice / quiz log (optional history)</h3></div>', unsafe_allow_html=True)
    scores = progress.get("scores", [])
    left, right = st.columns((1, 1.1))
    with left:
        with st.form("log_score"):
            unit = st.selectbox(
                "Log entry",
                options=ASSESSMENT_UNITS,
                format_func=lambda u: f"{u['label']} ({u['focus']})",
            )
            score = st.slider("Score (%)", 0, 100, 75, key="hist_score")
            hours = st.number_input("Hours studied since last log", min_value=0.0, value=1.0, step=0.5)
            note = st.text_input("Optional note")
            if st.form_submit_button("Append to history", type="primary"):
                progress["scores"].append(
                    {
                        "date": date.today().isoformat(),
                        "unit": unit["id"],
                        "label": unit["label"],
                        "score": int(score),
                        "note": note,
                    }
                )
                progress["hours_logged"] = float(progress["hours_logged"]) + float(hours)
                # Also write into the official component slot
                progress["components"][unit["id"]] = int(score)
                save_progress(progress)
                st.success("Logged.")
                st.rerun()
        notes = st.text_area("Standing notes", value=progress.get("notes", ""), height=100)
        if notes != progress.get("notes", ""):
            progress["notes"] = notes
            save_progress(progress)

    with right:
        st.markdown("**Topic confidence**")
        conf_changed = False
        for topic in TOPICS:
            new_val = st.slider(
                topic, 1, 5, int(progress["topic_confidence"].get(topic, 3)), key=f"conf_{topic}"
            )
            if new_val != progress["topic_confidence"].get(topic):
                progress["topic_confidence"][topic] = int(new_val)
                conf_changed = True
        if conf_changed:
            save_progress(progress)

    if scores:
        fig = scores_figure(scores)
        st.pyplot(fig, width="stretch")
        plt.close(fig)
        st.dataframe(pd.DataFrame(scores), width="stretch", hide_index=True)
    fig = confidence_figure(progress)
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def page_force_lab() -> None:
    hero(
        "Force lab",
        "Verify planar FBDs, inclined-plane acceleration, and ideal projectiles — "
        "symbolic check, then the plot.",
    )
    mode = st.radio(
        "Simulation",
        ["Vector FBD", "Inclined plane", "Projectile (ideal)"],
        horizontal=True,
    )

    if mode == "Vector FBD":
        mcol, ncol = st.columns(2)
        with mcol:
            mass = st.number_input("Mass $m$ (kg)", min_value=0.01, value=2.0, step=0.1)
        with ncol:
            n_forces = st.slider("Number of forces", 1, 6, 3)

        forces: list[Force2D] = []
        # Defaults used for the live plot; expander edits override via widgets
        default_mags = [10.0, 5.0, 5.0, 4.0, 3.0, 2.0]
        default_angs = [0.0, 90.0, 180.0, 270.0, 45.0, 135.0]
        with st.expander("Edit force magnitudes, angles, labels", expanded=False):
            for i in range(n_forces):
                c1, c2, c3 = st.columns(3)
                with c1:
                    mag = st.number_input(
                        f"$|F_{{{i+1}}}|$ (N)",
                        min_value=0.0,
                        value=default_mags[i],
                        key=f"mag_{i}",
                    )
                with c2:
                    ang = st.number_input(
                        f"$\\theta_{{{i+1}}}$ (deg from $+x$)",
                        value=default_angs[i],
                        key=f"ang_{i}",
                    )
                with c3:
                    label = st.text_input(f"Label {i+1}", value=f"F{i+1}", key=f"lab_{i}")
                forces.append(force_from_magnitude_angle(mag, ang, label))
        # If expander collapsed, Streamlit still runs widgets — forces list is filled.
        # Guard empty edge case:
        if not forces:
            for i in range(n_forces):
                forces.append(
                    force_from_magnitude_angle(default_mags[i], default_angs[i], f"F{i+1}")
                )
        try:
            f_net = net_force(forces)
            ax_x, ax_y = acceleration_from_forces(forces, mass)
        except ValueError as err:
            st.error(str(err))
            return
        k1, k2, k3 = st.columns(3)
        with k1:
            stat_card("|F_net|", f"{f_net.magnitude:.3f} N")
        with k2:
            stat_card("Components", f"{f_net.fx:.2f}, {f_net.fy:.2f}")
        with k3:
            stat_card("|a|", f"{np.hypot(ax_x, ax_y):.3f} m/s²")
        plot_col, eq_col = st.columns((1.25, 0.85))
        with plot_col:
            fig, ax = plt.subplots(figsize=(5.2, 4.4))
            style_figure(ax)
            colors = plt.cm.tab10(np.linspace(0, 1, max(len(forces), 1)))
            for f, color in zip(forces, colors):
                ax.quiver(
                    0, 0, f.fx, f.fy,
                    angles="xy", scale_units="xy", scale=1, color=color, width=0.008,
                )
                ax.text(f.fx * 1.05, f.fy * 1.05, f.label or "", fontsize=9, color=BLUE)
            ax.quiver(
                0, 0, f_net.fx, f_net.fy,
                angles="xy", scale_units="xy", scale=1, color="#b00020", width=0.012,
            )
            ax.text(f_net.fx * 1.08, f_net.fy * 1.08, r"$F_{\mathrm{net}}$", color="#b00020", fontsize=10)
            lim = max(f_net.magnitude, max((f.magnitude for f in forces), default=1.0), 1.0) * 1.35
            ax.set_xlim(-lim, lim)
            ax.set_ylim(-lim, lim)
            ax.set_aspect("equal")
            ax.set_xlabel(r"$F_x$ (N)")
            ax.set_ylabel(r"$F_y$ (N)")
            ax.set_title("Live free-body diagram", color=BLUE, fontweight="bold")
            st.pyplot(fig, width="stretch")
            plt.close(fig)
        with eq_col:
            st.latex(
                rf"\vec{{F}}_{{\mathrm{{net}}}}=({f_net.fx:.3f}\,\hat{{i}}+{f_net.fy:.3f}\,\hat{{j}})\,\mathrm{{N}}"
            )
            st.latex(
                rf"\vec{{a}}=({ax_x:.3f}\,\hat{{i}}+{ax_y:.3f}\,\hat{{j}})\,\mathrm{{m/s^2}}"
            )
            st.caption("Open the expander above to edit individual forces.")

    elif mode == "Inclined plane":
        c1, c2, c3 = st.columns(3)
        _mass = c1.number_input("Mass (kg)", min_value=0.01, value=5.0)
        theta = c2.slider("Incline θ (deg)", 0.0, 60.0, 30.0)
        mu_k = c3.number_input("μ_k", min_value=0.0, value=0.1, step=0.05)
        try:
            a = inclined_plane_accel(_mass, theta, mu_k)
        except ValueError as err:
            st.error(str(err))
            return
        th = np.radians(theta)
        st.latex(rf"a_\parallel=g(\sin\theta-\mu_k\cos\theta)={a:.4f}\,\mathrm{{m/s^2}}")
        fig, ax = plt.subplots(figsize=(7, 4.1))
        style_figure(ax)
        L = 4.0
        ax.plot([0, L * np.cos(th)], [0, L * np.sin(th)], color=BLUE, lw=3)
        ax.plot([0, L], [0, 0], color="#444", lw=1)
        s = L * 0.55
        bx, by = s * np.cos(th), s * np.sin(th)
        ax.plot(bx, by, "s", color=MAIZE, markersize=16, markeredgecolor=BLUE)
        ax.set_aspect("equal")
        ax.set_title(rf"Incline $\theta={theta:.1f}^\circ$, $\mu_k={mu_k:.2f}$", color=BLUE)
        st.pyplot(fig, width="stretch")
        plt.close(fig)

    else:
        c1, c2, c3 = st.columns(3)
        v0 = c1.number_input("v₀ (m/s)", min_value=0.0, value=20.0)
        ang = c2.slider("Launch angle (deg)", 0.0, 90.0, 45.0)
        g = c3.number_input("g (m/s²)", min_value=0.1, value=9.81)
        try:
            x, y, t_f, R = projectile_trajectory(v0, ang, g=g)
        except ValueError as err:
            st.error(str(err))
            return
        k1, k2 = st.columns(2)
        with k1:
            stat_card("Time of flight", f"{t_f:.3f} s")
        with k2:
            stat_card("Range", f"{R:.3f} m")
        fig, ax = plt.subplots(figsize=(8, 3.5))
        style_figure(ax)
        ax.plot(x, y, color=BLUE, lw=2.4)
        ax.fill_between(x, y, alpha=0.14, color=MAIZE)
        ax.set_xlabel(r"$x$ (m)")
        ax.set_ylabel(r"$y$ (m)")
        ax.set_title("Ideal projectile (no drag)", color=BLUE, fontweight="bold")
        st.pyplot(fig, width="stretch")
        plt.close(fig)


def page_rules() -> None:
    hero(
        "Cursor rules",
        "Physics 140 expert mode with required LaTeX rendering. Edit `.cursorrules` "
        "in the project root to tune IA behavior.",
    )
    if not RULES_PATH.exists():
        st.error("`.cursorrules` is missing.")
        return
    text = RULES_PATH.read_text()
    preview_lines = text.strip().splitlines()[:18]
    preview = "\n".join(preview_lines)
    highlights = [
        "Guided breakdowns",
        "Code-as-truth checks",
        "No invented constraints",
        "LaTeX-first math",
    ]
    chips = " ".join(f'<span class="topic-chip soft">{h}</span>' for h in highlights)
    st.markdown(
        f"""
        <div class="panel">
          <h3>Active .cursorrules</h3>
          <div style="margin-bottom:0.45rem;color:#5C6B7A;font-size:0.9rem;">
            <b>{len(text.splitlines())} lines</b> · Physics 140 Expert Mode with required <code>$</code>/<code>$$</code> LaTeX.
          </div>
          {chips}
          <div class="rules-preview">{preview}\n…</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("View full rules file", expanded=False):
        st.code(text, language="markdown")
    st.caption(f"`{RULES_PATH}`")


def main() -> None:
    st.set_page_config(
        page_title="PHYSICS 140 Study Lab",
        page_icon="∇",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    ensure_dirs()
    progress = load_progress()

    with st.sidebar:
        st.markdown(f"### {COURSE['code']}")
        st.caption(f"{COURSE['term']} · {INSTRUCTOR['name']}")
        page = st.radio("Navigate", PAGES, label_visibility="collapsed")
        sc, stot, spct = coverage_summary(progress, SLIDES_DIR)
        pc, ptot, ppct = coverage_summary(progress, PRACTICE_DIR)
        nxt = next_exam()
        st.markdown("---")
        if nxt:
            d = days_until(nxt["regular_date"])
            st.caption(f"Next · {nxt['label']} in {d}d" if d >= 0 else f"Last · {nxt['label']}")
        st.caption(f"Slides covered · {spct:.0f}%")
        st.progress(min(max(spct / 100.0, 0.0), 1.0))
        st.caption(f"Practice covered · {ppct:.0f}%")
        st.progress(min(max(ppct / 100.0, 0.0), 1.0))
        st.markdown(
            """
            <div class="sidebar-cite">
              <b>In Cursor chat</b><br/>
              Reference materials with
              <span style="display:inline-block;background:#FFCB05;color:#00274C;font-weight:700;padding:0.12rem 0.4rem;border-radius:4px;margin:0.15rem 0.1rem;">@slides</span>
              and
              <span style="display:inline-block;background:#FFCB05;color:#00274C;font-weight:700;padding:0.12rem 0.4rem;border-radius:4px;margin:0.15rem 0.1rem;">@practice_exams</span>
              for grounded drills.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if page == "Command Center":
        page_command_center(progress)
    elif page == "Syllabus":
        page_syllabus()
    elif page == "Study":
        page_study(progress)
    elif page == "Coverage":
        page_coverage(progress)
    elif page == "Library":
        page_library(progress)
    elif page == "Packet Catalog":
        page_packet_catalog()
    elif page == "Grades":
        page_progress(progress)
    elif page == "Force Lab":
        page_force_lab()
    else:
        page_rules()


if __name__ == "__main__":
    main()
