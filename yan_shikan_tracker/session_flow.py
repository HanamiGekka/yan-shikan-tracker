from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .draft_io import delete_draft
from .excel_io import (
    get_daily_summary_output_path,
    get_llm_prompt_output_path,
    get_today_report_output_path,
    save_daily_segments,
)
from .output_manager import OutputRebuildResult, rebuild_output_for_date


@dataclass
class SessionWriteResult:
    date_str: str
    written_segment_count: int
    total_day_segment_count: int
    raw_data_path: Path
    summary_path: Path
    report_path: Path
    prompt_path: Path
    rebuild_result: OutputRebuildResult


class OutputRebuildError(RuntimeError):
    """The raw record is committed, but its derived output needs rebuilding."""

    def __init__(self, date_str: str, raw_data_path: Path):
        self.date_str = date_str
        self.raw_data_path = raw_data_path
        super().__init__(
            f"{date_str}: raw Excel saved at {raw_data_path}; output rebuild failed. "
            "Use Output Management to rebuild this date."
        )


def commit_confirmed_segments(
    *,
    date_str: str,
    segments: list[dict[str, object]],
    session_id: str,
    draft_paths: Iterable[Path] | None = None,
) -> SessionWriteResult:
    day_df, raw_data_path = save_daily_segments(
        date_str=date_str,
        segments=segments,
        session_id=session_id,
    )

    for draft_path in draft_paths or ():
        delete_draft(path=draft_path)

    try:
        rebuild_result = rebuild_output_for_date(date_str)
    except Exception as exc:
        raise OutputRebuildError(date_str, raw_data_path) from exc
    return SessionWriteResult(
        date_str=date_str,
        written_segment_count=len(segments),
        total_day_segment_count=len(day_df),
        raw_data_path=raw_data_path,
        summary_path=get_daily_summary_output_path(date_str),
        report_path=get_today_report_output_path(date_str),
        prompt_path=get_llm_prompt_output_path(date_str),
        rebuild_result=rebuild_result,
    )


def print_session_write_result(result: SessionWriteResult, *, intro: str) -> None:
    print(f"\n{intro}")
    print(f"- 已正式写入 data 的时间段数：{result.written_segment_count}")
    print(f"- 当日 data 累计时间段数：{result.total_day_segment_count}")
    print(f"- 原始记录：{result.raw_data_path}")
    print(f"- 每日汇总：{result.summary_path}")
    print(f"- 今日报告：{result.report_path}")
    print(f"- LLM提示词：{result.prompt_path}")
    _print_chart_paths(result.rebuild_result.chart_paths)


def _print_chart_paths(chart_paths: dict[str, object]) -> None:
    if not chart_paths:
        print("- charts：本次没有重绘图像喵。")
        return

    print("- charts（output/charts 下最新四张图喵）：")
    for label, path in chart_paths.items():
        print(f"  {label}: {path}")
