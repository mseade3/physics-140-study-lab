"""
Vision-based quiz generation from rendered lecture-slide PNGs.

Uses OpenAI-compatible Chat Completions with image inputs when OPENAI_API_KEY
is set. Falls back gracefully if unavailable.
"""

from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

from src.quiz_engine import QuizItem, _stable_id


def vision_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _b64_png(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("ascii")


def build_quiz_from_slide_images(
    image_paths: list[Path],
    *,
    n_questions: int = 8,
    model: str | None = None,
) -> list[QuizItem]:
    """
    Ask a vision model to write PHYSICS 140 quiz items from slide screenshots
    (pages already limited to the student's covered range).
    """
    if not vision_available():
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to your environment to enable "
            "diagram-aware quiz generation."
        )
    if not image_paths:
        return []

    model = model or os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
    # Cap images to keep request size reasonable; sample across the range
    paths = _sample_paths(image_paths, max_n=6)

    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "You are an elite UMich PHYSICS 140 IA. The student has only covered "
                "the attached lecture slides (diagrams included). Write a rigorous quiz "
                f"of exactly {n_questions} items grounded ONLY in these slides.\n\n"
                "Prefer questions that require reading diagrams: vector arrows, angles, "
                "components, parallelogram/triangle rules, unit vectors, coordinate axes.\n\n"
                "Return STRICT JSON (no markdown fences) with shape:\n"
                "{\n"
                '  "questions": [\n'
                "    {\n"
                '      "kind": "mcq" | "tf" | "cloze",\n'
                '      "prompt": "string (LaTeX allowed with $...$)",\n'
                '      "choices": ["..."] ,\n'
                '      "answer": "string (must match one choice for mcq/tf)",\n'
                '      "explanation": "short teaching note",\n'
                '      "source_page": <int page number visible on slide or best guess>,\n'
                '      "source_excerpt": "what on the slide supports this"\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "For tf, choices must be [\"True\", \"False\"]. For cloze, choices=[]."
            ),
        }
    ]
    for p in paths:
        # page_001.png -> 1
        m = re.search(r"page_(\d+)", p.name)
        page_no = int(m.group(1)) if m else 0
        content.append(
            {
                "type": "text",
                "text": f"Slide image for page {page_no}:",
            }
        )
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{_b64_png(p)}",
                    "detail": "high",
                },
            }
        )

    try:
        from urllib import request

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON. No preamble.",
                },
                {"role": "user", "content": content},
            ],
            "temperature": 0.4,
        }
        req = request.Request(
            os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
            + "/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        raw = data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Vision quiz request failed: {exc}") from exc

    return _parse_vision_json(raw, image_paths)


def _sample_paths(paths: list[Path], max_n: int) -> list[Path]:
    if len(paths) <= max_n:
        return paths
    # always include first, last, and evenly spaced middles
    idxs = sorted(
        {
            0,
            len(paths) - 1,
            *[round(i * (len(paths) - 1) / (max_n - 1)) for i in range(max_n)],
        }
    )
    return [paths[i] for i in idxs[:max_n]]


def _parse_vision_json(raw: str, image_paths: list[Path]) -> list[QuizItem]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    data = json.loads(raw)
    by_page = {}
    for p in image_paths:
        m = re.search(r"page_(\d+)", p.name)
        if m:
            by_page[int(m.group(1))] = str(p)

    items: list[QuizItem] = []
    for q in data.get("questions", []):
        page = int(q.get("source_page") or 1)
        kind = q.get("kind", "mcq")
        choices = list(q.get("choices") or [])
        if kind == "tf" and not choices:
            choices = ["True", "False"]
        img = by_page.get(page) or (str(image_paths[min(page - 1, len(image_paths) - 1)]) if image_paths else "")
        items.append(
            QuizItem(
                id=_stable_id("vision", q.get("prompt", "")[:80], str(page)),
                kind=kind,
                prompt=q.get("prompt", ""),
                choices=choices,
                answer=str(q.get("answer", "")),
                explanation=str(q.get("explanation", "")),
                source_page=page,
                source_excerpt=str(q.get("source_excerpt", "")),
                image_path=img,
            )
        )
    return items
