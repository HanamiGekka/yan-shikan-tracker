from __future__ import annotations

import os
from pathlib import Path

from .category_registry import (
    CANONICAL_CATEGORIES,
    CATEGORY_ALIASES,
    CATEGORY_COMMUTE_PROCESS,
    CATEGORY_EATING,
    CATEGORY_EXERCISE,
    CATEGORY_EXTRA_SLEEP,
    CATEGORY_INTERNAL,
    CATEGORY_JAPAN_MASTERS_EXAM,
    CATEGORY_JLPT,
    CATEGORY_MENU,
    CATEGORY_OTHER,
    CATEGORY_PROFESSIONAL,
    CATEGORY_REST,
    CATEGORY_SCHOOL_AFFAIRS,
    CATEGORY_SLEEP,
    CATEGORY_SOCIAL,
    CATEGORY_THINKING,
    CATEGORY_UNDERGRAD_COURSE,
    CATEGORY_UNDERGRAD_RESEARCH,
    CORE_CATEGORIES,
    CORE_CATEGORY_SET,
    MENU_CODE_TO_CATEGORY,
)


BASE_DIR = Path(__file__).resolve().parents[1]
# Set YAN_SHIKAN_DATA_ROOT to a temporary directory for demos or manual smoke tests.
# With no override, existing local data/output locations remain unchanged.
STORAGE_ROOT = Path(os.environ.get("YAN_SHIKAN_DATA_ROOT") or BASE_DIR).expanduser().resolve()
DATA_DIR = STORAGE_ROOT / "data"
OUTPUT_DIR = STORAGE_ROOT / "output"
DATA_BACKUP_DIR = DATA_DIR / "data_backup"
DRAFT_DIR = DATA_DIR / "drafts"
OUTPUT_CHART_DIR = OUTPUT_DIR / "charts"

# output/ is treated as a rebuildable derived-artifact area.
# Keep automatic backup off by default so rebuild flows stay simple and deterministic.
OUTPUT_BACKUP_ENABLED = False

CATEGORY_CONFIG_PATH = DATA_DIR / "category_config.csv"
LEGACY_TIME_LOG_PATH = DATA_DIR / "time_log.xlsx"
ROOT_LEGACY_TIME_LOG_PATH = STORAGE_ROOT / "time_log.xlsx"

TIME_LOG_FILE_PREFIX = "时间记录"
DAILY_SUMMARY_FILE_PREFIX = "每日汇总"
TODAY_REPORT_FILE_PREFIX = "今日报告"
LLM_PROMPT_FILE_PREFIX = "LLM提示词"

TIME_LOG_COLUMNS = [
    "date",
    "category",
    "duration_min",
    "feeling",
    "note",
    "session_id",
    "created_at",
]

TIME_LOG_EXPORT_COLUMNS_ZH = {
    "date": "日期",
    "category": "类别",
    "duration_min": "时长（分钟）",
    "feeling": "feeling评分",
    "note": "备注",
    "session_id": "录入会话ID",
    "created_at": "写入时间",
}

CATEGORY_CONFIG_COLUMNS = [
    "category",
    "mode",
    "target_min",
    "lower_min",
    "upper_min",
    "weight",
    "core",
]

DAILY_SUMMARY_COLUMNS = [
    "date",
    "total_score",
    "core_growth_score",
    "total_recorded_min",
    "segment_count",
]

SCORE_DETAIL_COLUMNS = [
    "date",
    "category",
    "total_recorded_min",
    "total_effective_min",
    "segment_count",
    "mode",
    "target_min",
    "lower_min",
    "upper_min",
    "weight",
    "core",
    "category_score",
]

CATEGORIES = [
    *CANONICAL_CATEGORIES,
]

CHART_WINDOWS = [
    ("7天", 7),
    ("30天", 30),
    ("90天", 90),
    ("全部", None),
]

DEFAULT_CATEGORY_CONFIG_ROWS = [
    {
        "category": CATEGORY_INTERNAL,
        "mode": "minimize",
        "target_min": 0.0,
        "lower_min": 0.0,
        "upper_min": 75.0,
        "weight": 3.0,
        "core": 0,
    },
    {
        "category": CATEGORY_SLEEP,
        "mode": "target",
        "target_min": 480.0,
        "lower_min": 420.0,
        "upper_min": 540.0,
        "weight": 16.0,
        "core": 1,
    },
    {
        "category": CATEGORY_EXTRA_SLEEP,
        "mode": "range",
        "target_min": 20.0,
        "lower_min": 0.0,
        "upper_min": 30.0,
        "weight": 2.0,
        "core": 0,
    },
    {
        "category": CATEGORY_COMMUTE_PROCESS,
        "mode": "minimize",
        "target_min": 0.0,
        "lower_min": 0.0,
        "upper_min": 80.0,
        "weight": 3.0,
        "core": 0,
    },
    {
        "category": CATEGORY_EATING,
        "mode": "range",
        "target_min": 90.0,
        "lower_min": 60.0,
        "upper_min": 135.0,
        "weight": 4.0,
        "core": 0,
    },
    {
        "category": CATEGORY_REST,
        "mode": "range",
        "target_min": 60.0,
        "lower_min": 20.0,
        "upper_min": 150.0,
        "weight": 4.0,
        "core": 0,
    },
    {
        "category": CATEGORY_JAPAN_MASTERS_EXAM,
        "mode": "maximize",
        "target_min": 360.0,
        "lower_min": 0.0,
        "upper_min": 600.0,
        "weight": 28.0,
        "core": 1,
    },
    {
        "category": CATEGORY_JLPT,
        "mode": "maximize",
        "target_min": 90.0,
        "lower_min": 0.0,
        "upper_min": 180.0,
        "weight": 10.0,
        "core": 1,
    },
    {
        "category": CATEGORY_UNDERGRAD_RESEARCH,
        "mode": "maximize",
        "target_min": 90.0,
        "lower_min": 0.0,
        "upper_min": 240.0,
        "weight": 6.0,
        "core": 0,
    },
    {
        "category": CATEGORY_UNDERGRAD_COURSE,
        "mode": "record_only",
        "target_min": 0.0,
        "lower_min": 0.0,
        "upper_min": 0.0,
        "weight": 0.0,
        "core": 0,
    },
    {
        "category": CATEGORY_SCHOOL_AFFAIRS,
        "mode": "minimize",
        "target_min": 0.0,
        "lower_min": 0.0,
        "upper_min": 45.0,
        "weight": 2.0,
        "core": 0,
    },
    {
        "category": CATEGORY_EXERCISE,
        "mode": "target",
        "target_min": 45.0,
        "lower_min": 20.0,
        "upper_min": 90.0,
        "weight": 8.0,
        "core": 1,
    },
    {
        "category": CATEGORY_THINKING,
        "mode": "range",
        "target_min": 45.0,
        "lower_min": 20.0,
        "upper_min": 100.0,
        "weight": 6.0,
        "core": 1,
    },
    {
        "category": CATEGORY_SOCIAL,
        "mode": "range",
        "target_min": 45.0,
        "lower_min": 0.0,
        "upper_min": 120.0,
        "weight": 2.0,
        "core": 0,
    },
    {
        "category": CATEGORY_PROFESSIONAL,
        "mode": "maximize",
        "target_min": 60.0,
        "lower_min": 0.0,
        "upper_min": 150.0,
        "weight": 6.0,
        "core": 1,
    },
    {
        "category": CATEGORY_OTHER,
        "mode": "record_only",
        "target_min": 0.0,
        "lower_min": 0.0,
        "upper_min": 0.0,
        "weight": 0.0,
        "core": 0,
    },
]
