from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_storage_paths(cwd: Path, override: Path | None) -> dict[str, str]:
    """Inspect fresh configuration imports without initializing runtime storage."""
    env = os.environ.copy()
    env.pop("YAN_SHIKAN_DATA_ROOT", None)
    if override is not None:
        env["YAN_SHIKAN_DATA_ROOT"] = str(override)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, "-c", (
            "import json; from yan_shikan_tracker import config; "
            "print(json.dumps({name: str(getattr(config, name)) "
            "for name in ('BASE_DIR', 'STORAGE_ROOT', 'DATA_DIR', 'OUTPUT_DIR')}))"
        )],
        cwd=cwd, env=env, text=True, encoding="utf-8",
        capture_output=True, check=True, timeout=20,
    )
    return json.loads(result.stdout)


def test_default_storage_remains_at_repository_root(tmp_path: Path) -> None:
    paths = read_storage_paths(tmp_path, None)
    assert Path(paths["BASE_DIR"]) == PROJECT_ROOT
    assert Path(paths["STORAGE_ROOT"]) == PROJECT_ROOT
    assert Path(paths["DATA_DIR"]) == PROJECT_ROOT / "data"
    assert Path(paths["OUTPUT_DIR"]) == PROJECT_ROOT / "output"
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "output").exists()


def test_storage_override_uses_temporary_root(tmp_path: Path) -> None:
    override = tmp_path / "synthetic-storage"
    paths = read_storage_paths(tmp_path, override)
    assert Path(paths["BASE_DIR"]) == PROJECT_ROOT
    assert Path(paths["STORAGE_ROOT"]) == override
    assert Path(paths["DATA_DIR"]) == override / "data"
    assert Path(paths["OUTPUT_DIR"]) == override / "output"
    assert not override.exists()
