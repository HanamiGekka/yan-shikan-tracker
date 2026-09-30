from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
import re
import shutil
import sys

import pandas as pd

from config import OUTPUT_DIR
from excel_io import (
    ensure_project_files,
    get_daily_output_paths,
    get_day_detail_for_date,
    get_output_chart_dir,
    get_output_day_dir,
    load_all_time_logs,
    load_category_config,
    save_daily_summary_workbook,
)
from plotter import generate_trend_charts, get_smoothing_runtime_status
from reporter import generate_llm_prompt, generate_today_report
from scorer import compute_daily_scores


MONTH_DIR_PATTERN = re.compile(r"^\d{4}\.\d{2}$")
DAY_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class OutputBuildContext:
    daily_summary_df: pd.DataFrame
    category_detail_df: pd.DataFrame
    category_config_df: pd.DataFrame
    recorded_dates: list[str]


@dataclass
class OutputRebuildResult:
    cleared_dates: list[str] = field(default_factory=list)
    generated_dates: list[str] = field(default_factory=list)
    skipped_dates: list[str] = field(default_factory=list)
    chart_paths: dict[str, Path] = field(default_factory=dict)


def _parse_date(date_str: str) -> date:
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _iter_calendar_dates(start_date: str, end_date: str) -> list[str]:
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        start, end = end, start

    out: list[str] = []
    current = start
    while current <= end:
        out.append(current.isoformat())
        current += timedelta(days=1)
    return out


def _unique_sorted_dates(date_values: list[str]) -> list[str]:
    return sorted({str(value) for value in date_values})


def _iter_output_day_dirs() -> list[Path]:
    day_dirs: list[Path] = []
    if not OUTPUT_DIR.exists():
        return day_dirs

    for month_dir in OUTPUT_DIR.iterdir():
        if not month_dir.is_dir() or not MONTH_DIR_PATTERN.match(month_dir.name):
            continue
        for day_dir in month_dir.iterdir():
            if day_dir.is_dir() and DAY_DIR_PATTERN.match(day_dir.name):
                day_dirs.append(day_dir)
    return sorted(day_dirs)


def _prune_empty_output_dirs(date_str: str) -> None:
    day_dir = get_output_day_dir(date_str)
    if day_dir.exists() and not any(day_dir.iterdir()):
        day_dir.rmdir()

    month_dir = day_dir.parent
    if month_dir.exists() and month_dir != OUTPUT_DIR and not any(month_dir.iterdir()):
        month_dir.rmdir()


def _load_output_build_context() -> OutputBuildContext:
    ensure_project_files()
    time_log_df = load_all_time_logs()
    category_config_df = load_category_config()
    daily_summary_df, category_detail_df = compute_daily_scores(time_log_df, category_config_df)
    recorded_dates = (
        daily_summary_df["date"].astype(str).tolist()
        if not daily_summary_df.empty and "date" in daily_summary_df.columns
        else []
    )
    return OutputBuildContext(
        daily_summary_df=daily_summary_df,
        category_detail_df=category_detail_df,
        category_config_df=category_config_df,
        recorded_dates=_unique_sorted_dates(recorded_dates),
    )


def clear_daily_output(date_str: str) -> list[Path]:
    removed: list[Path] = []
    for path in get_daily_output_paths(date_str):
        if path.exists():
            path.unlink()
            removed.append(path)
    _prune_empty_output_dirs(date_str)
    return removed


def _write_daily_output(date_str: str, context: OutputBuildContext) -> None:
    day_detail_df = get_day_detail_for_date(date_str, context.category_detail_df)
    save_daily_summary_workbook(
        target_date=date_str,
        daily_summary_df=context.daily_summary_df,
        day_detail_df=day_detail_df,
        category_config_df=context.category_config_df,
    )
    generate_today_report(
        target_date=date_str,
        daily_summary_df=context.daily_summary_df,
        category_detail_df=context.category_detail_df,
        category_config_df=context.category_config_df,
        output_path=get_daily_output_paths(date_str)[1],
    )
    generate_llm_prompt(
        target_date=date_str,
        daily_summary_df=context.daily_summary_df,
        category_detail_df=context.category_detail_df,
        category_config_df=context.category_config_df,
        output_path=get_daily_output_paths(date_str)[2],
    )


def redraw_all_charts(context: OutputBuildContext | None = None) -> dict[str, Path]:
    build_context = context or _load_output_build_context()
    chart_dir = get_output_chart_dir()
    chart_dir.mkdir(parents=True, exist_ok=True)

    for path in chart_dir.glob("*.png"):
        path.unlink()

    chart_target_date = (
        build_context.recorded_dates[-1]
        if build_context.recorded_dates
        else datetime.now().date().isoformat()
    )
    print(f"[trend] active python = {sys.executable}")
    print(f"[trend] {get_smoothing_runtime_status()}")
    return generate_trend_charts(
        daily_summary_df=build_context.daily_summary_df,
        target_date=chart_target_date,
        chart_dir=chart_dir,
    )


def _rebuild_target_dates(
    target_dates: list[str],
    *,
    context: OutputBuildContext | None = None,
    redraw_charts: bool,
) -> OutputRebuildResult:
    build_context = context or _load_output_build_context()
    available_dates = set(build_context.recorded_dates)
    result = OutputRebuildResult()

    for date_str in _unique_sorted_dates(target_dates):
        clear_daily_output(date_str)
        result.cleared_dates.append(date_str)
        if date_str not in available_dates:
            result.skipped_dates.append(date_str)
            continue

        _write_daily_output(date_str, build_context)
        result.generated_dates.append(date_str)

    if redraw_charts:
        result.chart_paths = redraw_all_charts(context=build_context)
    return result


def rebuild_output_for_date(date_str: str) -> OutputRebuildResult:
    return _rebuild_target_dates([date_str], redraw_charts=True)


def rebuild_output_range(start_date: str, end_date: str) -> OutputRebuildResult:
    return _rebuild_target_dates(
        _iter_calendar_dates(start_date, end_date),
        redraw_charts=True,
    )


def rebuild_all_output() -> OutputRebuildResult:
    build_context = _load_output_build_context()
    existing_output_dates = [path.name for path in _iter_output_day_dirs()]
    target_dates = _unique_sorted_dates(existing_output_dates + build_context.recorded_dates)
    return _rebuild_target_dates(
        target_dates,
        context=build_context,
        redraw_charts=True,
    )


def _backup_dirs_for_date(date_str: str) -> list[Path]:
    day_dir = get_output_day_dir(date_str)
    if not day_dir.exists():
        return []
    return sorted(
        path
        for path in day_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{date_str}_backup_")
    )


def clear_daily_backups(date_str: str) -> list[Path]:
    removed: list[Path] = []
    for backup_dir in _backup_dirs_for_date(date_str):
        shutil.rmtree(backup_dir)
        removed.append(backup_dir)
    _prune_empty_output_dirs(date_str)
    return removed


def clear_all_backups() -> list[Path]:
    removed: list[Path] = []
    for day_dir in _iter_output_day_dirs():
        removed.extend(clear_daily_backups(day_dir.name))
    return removed
