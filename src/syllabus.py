"""Official CSP PHYSICS 140 syllabus constants (Fall 2026 — Dr. Mike Melnichuk)."""

from __future__ import annotations

COURSE = {
    "code": "PHYSICS 140",
    "program": "CSP",
    "term": "Fall 2026",
    "title": "General Physics I",
    "warning": (
        "This course is extremely hard and intensive. Physics 140 is about "
        "1.5× harder than Physics 150. Pre-med / life-science majors should "
        "confirm with an advisor whether Physics 150 is the right placement."
    ),
}

INSTRUCTOR = {
    "name": "Dr. Mike Melnichuk",
    "preferred": "Mike or Dr. Mike",
    "email": "mmeln@umich.edu",
    "office": "1484(A) Randall",
}

CLASS = {
    "days": "Monday–Friday",
    "time": "12:00 PM – 1:00 PM (EST)",
    "room": "271 Weiser",
}

HELP_ROOM = {
    "location": "1416 Randall",
    "starts": "2026-09-08",
    "hours": [
        {"day": "Monday", "time": "10:00 AM – 12:00 PM"},
        {"day": "Tuesday", "time": "10:00 AM – 12:00 PM"},
        {"day": "Wednesday", "time": "10:00 AM – 12:00 PM"},
        {"day": "Thursday", "time": "10:00 AM – 12:00 PM"},
        {"day": "Friday", "time": "10:00 AM – 12:00 PM"},
    ],
}

MATERIALS = [
    {
        "id": "mastering",
        "name": "Mastering Physics",
        "detail": "Web homework from Young & Freedman 15e. Course ID: melnichuk16001. None dropped.",
    },
    {
        "id": "iclicker",
        "name": "i>clicker Cloud",
        "detail": "Join code OQGL. Correct 4/4, incorrect 3/4, absent/no answer 0/4. Eight lowest scores dropped.",
    },
    {
        "id": "textbook",
        "name": "University Physics with Modern Physics, 15e",
        "detail": "Young & Freedman — e-book (via Mastering) or hardcopy.",
    },
]

GRADE_WEIGHTS = [
    {"id": "iclicker", "label": "i>clicker quizzes (class participation)", "weight": 0.20},
    {"id": "mastering", "label": "Mastering Physics homework", "weight": 0.16},
    {"id": "exam_1", "label": "Exam 1", "weight": 0.16},
    {"id": "exam_2", "label": "Exam 2", "weight": 0.16},
    {"id": "exam_3", "label": "Exam 3", "weight": 0.16},
    {"id": "exam_4", "label": "Exam 4 (Final)", "weight": 0.16},
]

# Letter bands: score must be > lower bound to earn the letter (syllabus style).
GRADE_SCALE = [
    ("A+", 97),
    ("A", 92),
    ("A-", 89),
    ("B+", 85),
    ("B", 80),
    ("B-", 75),
    ("C+", 60),
    ("C", 50),
    ("C-", 40),
    ("D+", 30),
    ("D", 20),
    ("D-", 10),
    ("E", 0),
]

EXAMS = [
    {
        "id": "exam_1",
        "label": "Exam 1",
        "regular_date": "2026-10-01",
        "regular_weekday": "Thursday",
        "regular_time": "6:00 PM – 7:50 PM",
        "room": "TBA",
        "alternate": "Monday — check Physics SSO",
        "index_cards": 1,
    },
    {
        "id": "exam_2",
        "label": "Exam 2",
        "regular_date": "2026-10-29",
        "regular_weekday": "Thursday",
        "regular_time": "6:00 PM – 7:50 PM",
        "room": "TBA",
        "alternate": "Monday — check Physics SSO",
        "index_cards": 2,
    },
    {
        "id": "exam_3",
        "label": "Exam 3",
        "regular_date": "2026-11-19",
        "regular_weekday": "Thursday",
        "regular_time": "6:00 PM – 7:50 PM",
        "room": "TBA",
        "alternate": "Monday — check Physics SSO",
        "index_cards": 3,
    },
    {
        "id": "exam_4",
        "label": "Exam 4 (Final)",
        "regular_date": "2026-12-16",
        "regular_weekday": "Wednesday",
        "regular_time": "7:30 PM – 9:30 PM",
        "room": "TBA",
        "alternate": "Check Physics SSO",
        "index_cards": "4× 3×5 cards OR one double-sided 8.5×11 sheet",
    },
]

POLICIES = {
    "formula_aid": (
        "Each exam (four Canvas MC quizzes): start with one 3×5 index card of formulae; "
        "add a card each exam, up to four double-sided 3×5 cards — or one double-sided "
        "8.5×11 sheet for the Final only. Calculator OK if no formulas stored in memory."
    ),
    "no_drops_exams_hw": "No exam dropped. No Mastering Physics homework dropped. No extra credit.",
    "iclicker_drops": "Eight (8) lowest i>clicker scores dropped (any cause).",
    "grade_dispute": "Report grade issues within one week.",
    "absence": "Report absence-related issues within one week.",
    "rhamuep_deadline": "2026-09-21",
    "rhamuep": (
        "Religious-holiday alternate/make-up exam requests must be made by "
        "September 21, 2026. Submit an Alternate Exam Request Form two weeks before the exam."
    ),
    "curve_note": (
        "If class average is significantly below 75%, the scale may be lowered so at least "
        "half of students receive A/B-range grades (A+ through B-)."
    ),
}

SSO = {
    "name": "Physics Student Service Office (SSO)",
    "location": "1255 NEAL (1st floor)",
    "email": "physics.sso@umich.edu",
    "phones": ["(734) 764-5539", "(734) 764-5537", "(734) 936-0659"],
}

# For progress logging UI
ASSESSMENT_UNITS = [
    {"id": "exam_1", "label": "Exam 1", "focus": "16% of course · formula card ×1"},
    {"id": "exam_2", "label": "Exam 2", "focus": "16% of course · formula cards ×2"},
    {"id": "exam_3", "label": "Exam 3", "focus": "16% of course · formula cards ×3"},
    {"id": "exam_4", "label": "Exam 4 (Final)", "focus": "16% of course · 4 cards or 8.5×11 sheet"},
    {"id": "mastering", "label": "Mastering Physics (avg)", "focus": "16% of course · none dropped"},
    {"id": "iclicker", "label": "i>clicker (avg after drops)", "focus": "20% of course · 8 lowest dropped"},
]

TOPICS = [
    "1D / 2D Kinematics",
    "Newton's Laws & FBDs",
    "Friction & Inclined Planes",
    "Work & Energy",
    "Momentum & Collisions",
    "Rotational Kinematics",
    "Torque & Equilibrium",
    "Angular Momentum",
]


def letter_grade(percent: float) -> str:
    """Map a percent score to the CSP Physics 140 letter band."""
    for letter, lower in GRADE_SCALE:
        if percent > lower:
            return letter
    return "E"


def projected_course_percent(component_scores: dict[str, float | None]) -> float | None:
    """
    Weighted course % from component scores in [0, 100].
    Missing components are ignored and remaining weights are renormalized.
    Returns None if nothing entered.
    """
    num = 0.0
    den = 0.0
    for row in GRADE_WEIGHTS:
        score = component_scores.get(row["id"])
        if score is None:
            continue
        num += float(score) * row["weight"]
        den += row["weight"]
    if den <= 0:
        return None
    return num / den
