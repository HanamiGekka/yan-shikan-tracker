from __future__ import annotations

import shutil
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import category_registry
import draft_io
import excel_io
import output_manager
import scorer
import session_flow

DAY = "2030-01-10"


def segment(index: int, category: str = "运动", feeling: int = 2) -> dict[str, object]:
    return {
        "category": category,
        "duration_min": 10 + index,
        "feeling": feeling,
        "note": f"Fictional note {index}",
        "session_id": f"demo-session-{index}",
        "created_at": f"{DAY} 09:{index:02d}:00",
    }


def test_scoring_and_category_compatibility() -> None:
    assert category_registry.normalize_category_name("赶路") == "赶路和过程时间"
    assert category_registry.normalize_category_name("运动") == "运动"
    assert scorer.apply_feeling(10, 0) == pytest.approx(6)
    assert scorer.apply_feeling(10, 3) == pytest.approx(12.5)
    log = pd.DataFrame(
        [
            {"date": DAY, "category": "运动", "duration_min": 10, "feeling": 0},
            {"date": DAY, "category": "运动", "duration_min": 10, "feeling": 3},
            {"date": DAY, "category": "赶路", "duration_min": 10, "feeling": 2},
        ]
    )
    config = pd.DataFrame(
        [
            {"category": "运动", "mode": "maximize", "target_min": 10, "lower_min": 0, "upper_min": 20, "weight": 10, "core": 1},
            {"category": "赶路和过程时间", "mode": "minimize", "target_min": 0, "lower_min": 0, "upper_min": 30, "weight": 3, "core": 0},
        ]
    )
    summary, detail = scorer.compute_daily_scores(log, config)
    assert summary.iloc[0]["core_growth_score"] == pytest.approx(10)
    assert summary.iloc[0]["total_score"] == pytest.approx(11.9)
    assert set(detail["category"]) == {"运动", "赶路和过程时间"}


def test_draft_commit_and_same_day_append(isolated_storage: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_flow, "rebuild_output_for_date", lambda _: output_manager.OutputRebuildResult())
    first = segment(1)
    draft = draft_io.save_draft(DAY, [first], "demo-session-1")
    assert draft_io.load_draft(path=draft)["segments"][0]["note"] == first["note"]
    result = session_flow.commit_confirmed_segments(
        date_str=DAY, segments=[first], session_id="demo-session-1", draft_paths=[draft]
    )
    assert result.raw_data_path.exists()
    assert not draft.exists()
    second = segment(2, "赶路", 3)
    excel_io.save_daily_segments(DAY, [second], "demo-session-2")
    excel_io.save_daily_segments(DAY, [second], "demo-session-2")
    raw = pd.read_excel(excel_io.get_daily_raw_log_path(DAY))
    assert len(raw) == 2
    assert list(raw.columns) == list(excel_io.TIME_LOG_EXPORT_COLUMNS_ZH.values())
    assert set(raw["录入会话ID"]) == {"demo-session-1", "demo-session-2"}
    backup = excel_io.DATA_BACKUP_DIR / "2030.01" / DAY / f"时间记录_{DAY}.xlsx"
    assert backup.exists()
    assert len(list(backup.parent.glob("*.xlsx"))) == 1


@pytest.mark.parametrize("failure", ["save", "replace"])
def test_atomic_failure_preserves_original(
    isolated_storage: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    excel_io.save_daily_segments(DAY, [segment(1)], "demo-session-1")
    original = excel_io.get_daily_raw_log_path(DAY)
    before = original.read_bytes()
    if failure == "save":
        def fail_save(*_args: object, **_kwargs: object) -> None:
            raise OSError("synthetic write failure")
        monkeypatch.setattr(excel_io.Workbook, "save", fail_save)
    else:
        real_replace = excel_io.os.replace

        def fail_replace(source: Path, target: Path) -> None:
            if Path(target) == original:
                raise OSError("synthetic replace failure")
            real_replace(source, target)

        monkeypatch.setattr(excel_io.os, "replace", fail_replace)
    with pytest.raises(OSError, match="synthetic"):
        excel_io.save_daily_segments(DAY, [segment(2)], "demo-session-2")
    assert original.read_bytes() == before
    assert len(pd.read_excel(original)) == 1
    assert not list(original.parent.glob(".*.xlsx"))


def test_output_failure_keeps_raw_and_reports_it(
    isolated_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    draft = draft_io.save_draft(DAY, [segment(1)], "demo-session-1")

    def fail_rebuild(_date: str) -> None:
        raise OSError("synthetic chart failure")

    monkeypatch.setattr(session_flow, "rebuild_output_for_date", fail_rebuild)
    with pytest.raises(session_flow.OutputRebuildError, match="raw Excel saved") as exc:
        session_flow.commit_confirmed_segments(
            date_str=DAY, segments=[segment(1)], session_id="demo-session-1", draft_paths=[draft]
        )
    assert exc.value.raw_data_path.exists()
    assert len(pd.read_excel(exc.value.raw_data_path)) == 1
    assert not draft.exists()
    monkeypatch.setattr(session_flow, "rebuild_output_for_date", lambda _: output_manager.OutputRebuildResult())
    excel_io.save_daily_segments(DAY, [segment(1)], "demo-session-1")
    assert len(pd.read_excel(exc.value.raw_data_path)) == 1


def test_raw_commit_failure_keeps_recoverable_draft(
    isolated_storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    draft = draft_io.save_draft(DAY, [segment(1)], "demo-session-1")

    def fail_raw_commit(**_kwargs: object) -> None:
        raise OSError("synthetic raw write failure")

    monkeypatch.setattr(session_flow, "save_daily_segments", fail_raw_commit)
    with pytest.raises(OSError, match="synthetic"):
        session_flow.commit_confirmed_segments(
            date_str=DAY, segments=[segment(1)], session_id="demo-session-1", draft_paths=[draft]
        )
    assert draft.exists()
    assert draft_io.load_draft(path=draft)["segments"][0]["note"] == "Fictional note 1"
    assert not excel_io.get_daily_raw_log_path(DAY).exists()


def test_bad_workbook_is_never_silently_skipped(isolated_storage: Path) -> None:
    bad = excel_io.get_daily_raw_log_path(DAY)
    bad.parent.mkdir(parents=True)
    bad.write_bytes(b"not an xlsx")
    with pytest.raises(excel_io.DataReadError) as exc:
        excel_io.load_all_time_logs()
    assert f"时间记录_{DAY}.xlsx" in str(exc.value)
    assert "ValueError" in str(exc.value)
    assert "not an xlsx" not in str(exc.value)
    assert bad.read_bytes() == b"not an xlsx"


def test_existing_config_is_not_rewritten(isolated_storage: Path) -> None:
    config = excel_io.CATEGORY_CONFIG_PATH
    before = config.read_bytes()
    excel_io.ensure_project_files()
    assert config.read_bytes() == before


def test_noninteractive_synthetic_smoke(isolated_storage: Path) -> None:
    samples = Path(__file__).resolve().parents[1] / "sample_data" / "daily"
    for source in samples.glob("*/时间记录_*.xlsx"):
        day = source.parent.name
        target = excel_io.get_daily_raw_log_path(day)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    result = output_manager.rebuild_all_output()
    assert len(result.generated_dates) == 3
    assert len(result.chart_paths) == 4
    for day in result.generated_dates:
        summary, report, prompt = excel_io.get_daily_output_paths(day)
        assert all(path.exists() and path.stat().st_size > 0 for path in (summary, report, prompt))
        with pd.ExcelFile(summary) as workbook:
            assert workbook.sheet_names == ["今日总览", "分类明细"]
            assert {"类别", "今日类别得分"}.issubset(pd.read_excel(workbook, sheet_name="分类明细").columns)
    assert all(path.stat().st_size > 0 for path in result.chart_paths.values())


def test_cli_can_start_with_isolated_storage_root(tmp_path: Path) -> None:
    project = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["YAN_SHIKAN_DATA_ROOT"] = str(tmp_path)
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, str(project / "main.py")],
        input="3\n", text=True, encoding="utf-8", capture_output=True, env=env,
        cwd=project, timeout=20,
    )
    assert completed.returncode == 0
    assert (tmp_path / "data" / "category_config.csv").exists()
    assert (tmp_path / "output" / "charts").is_dir()
