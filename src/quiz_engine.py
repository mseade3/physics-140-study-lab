"""
Build study quizzes from lecture-slide text (pages 1..covered).

Questions are grounded in extracted slide wording with source page citations.
No network calls — works offline from PDF text.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import asdict, dataclass
from typing import Iterable

from src.pdf_study import PageText, combined_corpus


@dataclass
class QuizItem:
    id: str
    kind: str  # mcq | tf | cloze | teach
    prompt: str
    choices: list[str]
    answer: str
    explanation: str
    source_page: int
    source_excerpt: str
    image_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "QuizItem":
        return QuizItem(
            id=d["id"],
            kind=d["kind"],
            prompt=d["prompt"],
            choices=list(d.get("choices") or []),
            answer=d["answer"],
            explanation=d["explanation"],
            source_page=int(d["source_page"]),
            source_excerpt=d.get("source_excerpt", ""),
            image_path=d.get("image_path", ""),
        )


def _stable_id(*parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode()).hexdigest()[:10]
    return h


def _sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    out = []
    for c in chunks:
        c = re.sub(r"\s+", " ", c).strip(" •-\t")
        if len(c) < 35 or len(c) > 280:
            continue
        if c.count(" ") < 4:
            continue
        out.append(c)
    return out


_DEF_PATTERNS = [
    # SCALAR - quantity that...
    re.compile(
        r"^(?P<term>[A-Z][A-Z][A-Za-z\s\-/]{1,40}?)\s*[-–—:]\s*(?P<defn>.{15,220})$",
        re.M,
    ),
    # Vector is represented...
    re.compile(
        r"(?P<term>\b[A-Z][A-Za-z]{2,30}(?:\s+[A-Za-z]{3,20}){0,3})\s+is\s+(?P<defn>.{20,200})",
        re.I,
    ),
]


def _definitions(pages: Iterable[PageText]) -> list[tuple[int, str, str, str]]:
    found: list[tuple[int, str, str, str]] = []
    for p in pages:
        for line in p.text.splitlines():
            line = line.strip()
            if len(line) < 25:
                continue
            for pat in _DEF_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                term = re.sub(r"\s+", " ", m.group("term")).strip(" -:•")
                defn = re.sub(r"\s+", " ", m.group("defn")).strip(" .:;")
                if len(term) < 3 or len(defn) < 15:
                    continue
                bad = {
                    "the", "this", "example", "note", "figure", "important",
                    "then", "here", "toe", "tip", "a vector", "the direction",
                    "the magnitude", "direction", "magnitude",
                }
                if term.lower() in bad or len(term.split()) > 5:
                    continue
                # Prefer glossary-style terms (SCALAR/VECTOR) or short noun phrases
                if term.lower().startswith("the "):
                    continue
                found.append((p.page, term, defn, line))
    seen: set[str] = set()
    uniq = []
    for row in found:
        key = row[1].lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(row)
    return uniq


def _mcq_from_definition(
    page: int, term: str, defn: str, excerpt: str, distractors: list[str], rng: random.Random
) -> QuizItem | None:
    if len(distractors) < 2:
        return None
    wrong = rng.sample(distractors, k=min(3, len(distractors)))
    choices = wrong + [defn]
    rng.shuffle(choices)
    return QuizItem(
        id=_stable_id("mcq", term, str(page)),
        kind="mcq",
        prompt=f"From your slides (through the covered pages): what best matches **{term}**?",
        choices=choices,
        answer=defn,
        explanation=f"Slide p.{page}: {excerpt}",
        source_page=page,
        source_excerpt=excerpt[:240],
    )


def _cloze_from_definition(page: int, term: str, defn: str, excerpt: str) -> QuizItem:
    return QuizItem(
        id=_stable_id("cloze", term, str(page)),
        kind="cloze",
        prompt=f"Fill in the blank (slide p.{page}):\n\n**{term}** — _____\n\nType the definition in your own words (or close to the slide).",
        choices=[],
        answer=defn,
        explanation=f"Expected idea from p.{page}: {defn}",
        source_page=page,
        source_excerpt=excerpt[:240],
    )


def _tf_from_sentence(page: int, sentence: str, rng: random.Random) -> QuizItem | None:
    # Create a false variant by swapping key physics words when possible
    swaps = [
        ("positive", "negative"),
        ("negative", "positive"),
        ("magnitude", "direction"),
        ("direction", "magnitude"),
        ("scalar", "vector"),
        ("vector", "scalar"),
        ("addition", "subtraction"),
        ("subtraction", "addition"),
        ("tail", "tip"),
        ("tip", "tail"),
    ]
    false = sentence
    for a, b in swaps:
        if re.search(rf"\b{a}\b", sentence, flags=re.I):
            false = re.sub(rf"\b{a}\b", b, sentence, count=1, flags=re.I)
            break
    if false == sentence:
        return None
    truth = rng.choice([True, False])
    shown = sentence if truth else false
    return QuizItem(
        id=_stable_id("tf", shown[:40], str(page)),
        kind="tf",
        prompt=f"True or False (based on slide p.{page}):\n\n_{shown}_",
        choices=["True", "False"],
        answer="True" if truth else "False",
        explanation=f"Original slide wording (p.{page}): {sentence}",
        source_page=page,
        source_excerpt=sentence[:240],
    )


def _teach_card(page: int, title: str, body: str) -> QuizItem:
    excerpt = body[:320]
    return QuizItem(
        id=_stable_id("teach", title, str(page)),
        kind="teach",
        prompt=(
            f"**Study card — slide p.{page}: {title}**\n\n"
            f"{excerpt}\n\n"
            "After you read it, mark whether you could explain this out loud without looking."
        ),
        choices=["I can explain it", "I need another pass"],
        answer="I can explain it",
        explanation=(
            "Physics Target: name the principle on this slide. "
            "Blueprint: list symbols / diagram elements. "
            "Then restate the slide in one sentence."
        ),
        source_page=page,
        source_excerpt=excerpt,
    )


# Lightweight concept bank keyed by keywords that must appear in covered corpus
_CONCEPT_BANK: list[dict] = [
    {
        "keywords": ["scalar", "vector"],
        "prompt": "Which of the following is a **vector** quantity?",
        "choices": ["Mass", "Temperature", "Displacement", "Amount of money"],
        "answer": "Displacement",
        "explanation": "Vectors have magnitude and direction (e.g. displacement, velocity, force).",
    },
    {
        "keywords": ["unit vector", "magnitude"],
        "prompt": "How do you obtain the **unit vector** corresponding to a nonzero vector $\\vec{u}$?",
        "choices": [
            "Multiply $\\vec{u}$ by its magnitude",
            "Divide $\\vec{u}$ by its own magnitude",
            "Take only the x-component of $\\vec{u}$",
            "Square each component of $\\vec{u}$",
        ],
        "answer": "Divide $\\vec{u}$ by its own magnitude",
        "explanation": "$\\hat{u} = \\vec{u}/|\\vec{u}|$. Its magnitude is 1.",
    },
    {
        "keywords": ["parallelogram", "addition"],
        "prompt": "In the **parallelogram (tail-to-tail) rule**, the resultant $\\vec{R}=\\vec{A}+\\vec{B}$ is:",
        "choices": [
            "The diagonal of the parallelogram formed by $\\vec{A}$ and $\\vec{B}$",
            "Always equal to $|\\vec{A}| - |\\vec{B}|$",
            "Perpendicular to both $\\vec{A}$ and $\\vec{B}$",
            "Independent of the angle between $\\vec{A}$ and $\\vec{B}$",
        ],
        "answer": "The diagonal of the parallelogram formed by $\\vec{A}$ and $\\vec{B}$",
        "explanation": "Translate without rotating until tails meet; the parallelogram diagonal is the sum.",
    },
    {
        "keywords": ["component", "cos", "sin"],
        "prompt": "If a vector of magnitude $A$ makes angle $\\theta$ with $+x$, the x-component is:",
        "choices": [r"$A\sin\theta$", r"$A\cos\theta$", r"$A\tan\theta$", r"$A/\cos\theta$"],
        "answer": r"$A\cos\theta$",
        "explanation": "Standard plane polar resolution: $A_x = A\\cos\\theta$, $A_y = A\\sin\\theta$.",
    },
    {
        "keywords": ["subtraction", "opposite"],
        "prompt": "Vector subtraction $\\vec{A}-\\vec{B}$ is equivalent to:",
        "choices": [
            r"$\vec{A}+\vec{B}$",
            r"$\vec{A}+(-\vec{B})$",
            r"$|\vec{A}|-|\vec{B}|$ as a scalar only",
            r"Always a unit vector",
        ],
        "answer": r"$\vec{A}+(-\vec{B})$",
        "explanation": "Add the opposite of $\\vec{B}$ (same magnitude, reversed direction).",
    },
]

def _concept_items(corpus: str, rng: random.Random) -> list[QuizItem]:
    low = corpus.lower()
    items: list[QuizItem] = []
    for row in _CONCEPT_BANK:
        if not all(k.lower() in low for k in row["keywords"]):
            continue
        # find a supporting page mention if possible
        page = 1
        m = re.search(r"\[Slide p\.(\d+)\]", corpus)
        if m:
            page = int(m.group(1))
        for k in row["keywords"]:
            m2 = re.search(rf"\[Slide p\.(\d+)\].{{0,400}}{re.escape(k)}", corpus, flags=re.I | re.S)
            if m2:
                page = int(m2.group(1))
                break
        choices = list(row["choices"])
        rng.shuffle(choices)
        items.append(
            QuizItem(
                id=_stable_id("concept", row["prompt"][:50]),
                kind="mcq",
                prompt=row["prompt"] + f"\n\n_(Unlocked because your covered slides mention: {', '.join(row['keywords'])}.)_",
                choices=choices,
                answer=row["answer"],
                explanation=row["explanation"],
                source_page=page,
                source_excerpt=row["explanation"],
            )
        )
    return items


def build_quiz(
    pages: list[PageText] | tuple[PageText, ...],
    n_questions: int = 8,
    seed: int | None = None,
    include_teach: bool = True,
    image_map: dict[int, str] | None = None,
) -> list[QuizItem]:
    """
    Build a mixed quiz strictly from (or gated by) covered-page text.
    When image_map is provided ({page_number: png_path}), each item gets its
    source slide diagram attached so the student studies pictures, not text alone.
    """
    if not pages:
        return []
    image_map = image_map or {}
    rng = random.Random(seed if seed is not None else 140)
    corpus = combined_corpus(pages)
    defs = _definitions(pages)
    distractor_pool = [d for _, _, d, _ in defs]

    pool: list[QuizItem] = []

    for page, term, defn, excerpt in defs:
        mcq = _mcq_from_definition(
            page, term, defn, excerpt,
            [d for d in distractor_pool if d != defn],
            rng,
        )
        if mcq:
            pool.append(mcq)
        if rng.random() < 0.55:
            pool.append(_cloze_from_definition(page, term, defn, excerpt))

    for p in pages:
        for s in _sentences(p.text)[:4]:
            tf = _tf_from_sentence(p.page, s, rng)
            if tf:
                pool.append(tf)

    pool.extend(_concept_items(corpus, rng))

    if include_teach:
        step = max(1, len(pages) // 4)
        for p in pages[::step][:4]:
            card = _teach_card(p.page, p.title_guess, p.text)
            if p.page in image_map:
                card.prompt = (
                    f"**Diagram study — slide p.{p.page}: {p.title_guess}**\n\n"
                    "Look at the slide image (arrows, angles, axes). "
                    "Could you redraw this diagram from memory and explain each vector?"
                )
            pool.append(card)

        # Extra diagram-first cards for pages that have images
        for p in pages:
            if p.page not in image_map:
                continue
            if rng.random() > 0.35:
                continue
            pool.append(
                QuizItem(
                    id=_stable_id("diagram", str(p.page), p.title_guess),
                    kind="teach",
                    prompt=(
                        f"**Read the diagram on slide p.{p.page}** ({p.title_guess}).\n\n"
                        "Identify: (1) what each arrow represents, (2) any angles shown, "
                        "(3) the resultant if present. Then mark if you could teach it."
                    ),
                    choices=["I can explain the diagram", "I need another pass"],
                    answer="I can explain the diagram",
                    explanation=(
                        "Physics Target: state the vector operation on the slide. "
                        "Blueprint: label tails/tips and the coordinate axes before computing."
                    ),
                    source_page=p.page,
                    source_excerpt=p.title_guess,
                    image_path=image_map[p.page],
                )
            )

    by_id = {q.id: q for q in pool}
    pool = list(by_id.values())
    if not pool:
        pool = [_teach_card(p.page, p.title_guess, p.text) for p in pages[: min(5, len(pages))]]

    for q in pool:
        if not q.image_path and q.source_page in image_map:
            q.image_path = image_map[q.source_page]

    rng.shuffle(pool)
    return pool[: max(1, n_questions)]


def grade_cloze(user: str, answer: str) -> bool:
    """Loose credit: shared content words."""
    def norm(s: str) -> set[str]:
        words = re.findall(r"[a-z0-9]+", s.lower())
        stop = {"a", "an", "the", "of", "and", "or", "to", "by", "with", "that", "which", "is", "are", "for", "in"}
        return {w for w in words if w not in stop and len(w) > 2}

    u, a = norm(user), norm(answer)
    if not a:
        return False
    overlap = len(u & a) / len(a)
    return overlap >= 0.45 or answer.lower().strip() in user.lower().strip()
