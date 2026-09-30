from __future__ import annotations

from typing import Any


CATEGORY_INTERNAL = "内务处理"
CATEGORY_SLEEP = "睡觉"
CATEGORY_EXTRA_SLEEP = "额外睡觉"
CATEGORY_COMMUTE_PROCESS = "赶路和过程时间"
CATEGORY_EATING = "吃饭"
CATEGORY_REST = "休息"
CATEGORY_JAPAN_MASTERS_EXAM = "日本修士考"
CATEGORY_JLPT = "日语JLPT"
CATEGORY_UNDERGRAD_RESEARCH = "本科科研"
CATEGORY_UNDERGRAD_COURSE = "本科课程"
CATEGORY_SCHOOL_AFFAIRS = "学校事务"
CATEGORY_EXERCISE = "运动"
CATEGORY_THINKING = "思考探索"
CATEGORY_SOCIAL = "社交"
CATEGORY_PROFESSIONAL = "专业能力"
CATEGORY_OTHER = "其他"

CANONICAL_CATEGORIES = [
    CATEGORY_INTERNAL,
    CATEGORY_SLEEP,
    CATEGORY_EXTRA_SLEEP,
    CATEGORY_COMMUTE_PROCESS,
    CATEGORY_EATING,
    CATEGORY_REST,
    CATEGORY_JAPAN_MASTERS_EXAM,
    CATEGORY_JLPT,
    CATEGORY_UNDERGRAD_RESEARCH,
    CATEGORY_UNDERGRAD_COURSE,
    CATEGORY_SCHOOL_AFFAIRS,
    CATEGORY_EXERCISE,
    CATEGORY_THINKING,
    CATEGORY_SOCIAL,
    CATEGORY_PROFESSIONAL,
    CATEGORY_OTHER,
]
CANONICAL_CATEGORY_SET = set(CANONICAL_CATEGORIES)

CORE_CATEGORIES = (
    CATEGORY_SLEEP,
    CATEGORY_JAPAN_MASTERS_EXAM,
    CATEGORY_JLPT,
    CATEGORY_EXERCISE,
    CATEGORY_THINKING,
    CATEGORY_PROFESSIONAL,
)
CORE_CATEGORY_SET = set(CORE_CATEGORIES)

CATEGORY_ALIASES = {
    "研究生备考": CATEGORY_JAPAN_MASTERS_EXAM,
    "研究室备考": CATEGORY_JAPAN_MASTERS_EXAM,
    "研究生": CATEGORY_JAPAN_MASTERS_EXAM,
    "赶路": CATEGORY_COMMUTE_PROCESS,
    "科研": CATEGORY_UNDERGRAD_RESEARCH,
    "日语": CATEGORY_JLPT,
    "日语学习": CATEGORY_JLPT,
}

CATEGORY_MENU = [
    ("1", CATEGORY_JAPAN_MASTERS_EXAM),
    ("2", CATEGORY_SLEEP),
    ("3", CATEGORY_JLPT),
    ("4", CATEGORY_EATING),
    ("5", CATEGORY_REST),
    ("6", CATEGORY_COMMUTE_PROCESS),
    ("7", CATEGORY_INTERNAL),
    ("8", CATEGORY_EXTRA_SLEEP),
    ("9", CATEGORY_UNDERGRAD_RESEARCH),
    ("a", CATEGORY_EXERCISE),
    ("b", CATEGORY_THINKING),
    ("c", CATEGORY_PROFESSIONAL),
    ("d", CATEGORY_UNDERGRAD_COURSE),
    ("e", CATEGORY_SCHOOL_AFFAIRS),
    ("f", CATEGORY_SOCIAL),
    ("g", CATEGORY_OTHER),
]
MENU_CODE_TO_CATEGORY = {code: category for code, category in CATEGORY_MENU}

FEELING_MULTIPLIERS = {
    0: 0.60,
    1: 0.90,
    2: 1.10,
    3: 1.25,
}

FEELING_LABELS = {
    0: "很差 / 状态很不好 / 低效",
    1: "一般 / 偏低",
    2: "良好 / 正常有效",
    3: "很好 / 高质量投入",
}

FEELING_GUIDE_TEXT = "0=很差 / 状态很不好 / 低效，1=一般 / 偏低，2=良好 / 正常有效，3=很好 / 高质量投入"


def normalize_category_name(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "<na>", "none"}:
        return ""
    return CATEGORY_ALIASES.get(text, text)


def normalize_feeling(value: Any, default: int = 2) -> int:
    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        parsed = int(default)
    return max(0, min(parsed, 3))


def describe_feeling(value: Any) -> str:
    feeling = normalize_feeling(value)
    return FEELING_LABELS.get(feeling, FEELING_LABELS[2])
