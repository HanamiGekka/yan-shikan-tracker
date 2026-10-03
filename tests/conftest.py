from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect every project storage path away from private user directories."""
    from yan_shikan_tracker import draft_io
    from yan_shikan_tracker import excel_io
    from yan_shikan_tracker import output_manager

    data = tmp_path / "data"
    output = tmp_path / "output"
    replacements = {
        "DATA_DIR": data,
        "DRAFT_DIR": data / "drafts",
        "DATA_BACKUP_DIR": data / "data_backup",
        "CATEGORY_CONFIG_PATH": data / "category_config.csv",
        "LEGACY_TIME_LOG_PATH": data / "time_log.xlsx",
        "ROOT_LEGACY_TIME_LOG_PATH": tmp_path / "time_log.xlsx",
        "OUTPUT_DIR": output,
        "OUTPUT_CHART_DIR": output / "charts",
    }
    for name, value in replacements.items():
        monkeypatch.setattr(excel_io, name, value)
    monkeypatch.setattr(draft_io, "DRAFT_DIR", data / "drafts")
    monkeypatch.setattr(output_manager, "OUTPUT_DIR", output)
    excel_io.ensure_project_files()
    return tmp_path
