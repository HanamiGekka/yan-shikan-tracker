from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .category_registry import normalize_category_name, normalize_feeling
from .config import DRAFT_DIR


def _draft_path(date_str: str, session_id: str | None = None) -> Path:
    if session_id and session_id.strip():
        safe_session_id = _sanitize_session_id(session_id)
        return DRAFT_DIR / f"draft_{date_str}__{safe_session_id}.json"
    return DRAFT_DIR / f"draft_{date_str}.json"


def _sanitize_session_id(session_id: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "-", session_id.strip())
    return cleaned or "session"


def ensure_draft_dir() -> None:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def _normalize_int(raw_value: Any, default_value: int) -> int:
    if raw_value is None:
        return int(default_value)
    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if raw_value == "":
            return int(default_value)
    return int(raw_value)


def _normalize_segment(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "category": normalize_category_name(raw.get("category", "")),
        "duration_min": max(0, _normalize_int(raw.get("duration_min", 0), 0)),
        "feeling": normalize_feeling(raw.get("feeling", 2)),
        "note": str(raw.get("note", "")),
        "session_id": str(raw.get("session_id", "")).strip(),
        "created_at": str(raw.get("created_at", "")).strip(),
    }


def build_draft_segment(
    *,
    category: str,
    duration_min: int,
    feeling: int,
    note: str,
    session_id: str,
    created_at: str | None = None,
) -> dict[str, Any]:
    return _normalize_segment(
        {
            "category": category,
            "duration_min": duration_min,
            "feeling": feeling,
            "note": note,
            "session_id": session_id,
            "created_at": created_at or _timestamp(),
        }
    )


def _read_draft_payload(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _normalize_loaded_draft(path: Path, payload: dict[str, Any], fallback_date: str | None = None) -> dict[str, Any]:
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        segments = []

    date_str = str(payload.get("date", fallback_date or "")).strip()
    session_id = str(payload.get("session_id", "")).strip()
    return {
        "date": date_str,
        "segments": [_normalize_segment(item) for item in segments if isinstance(item, dict)],
        "session_id": session_id,
        "updated_at": str(payload.get("updated_at", "")).strip(),
        "path": path,
    }


def _iter_draft_paths(date_str: str | None = None) -> list[Path]:
    ensure_draft_dir()
    pattern = f"draft_{date_str}*.json" if date_str else "draft_*.json"
    return sorted(path for path in DRAFT_DIR.glob(pattern) if path.is_file())


def list_drafts(date_str: str | None = None) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    for path in _iter_draft_paths(date_str):
        payload = _read_draft_payload(path)
        if payload is None:
            continue
        draft = _normalize_loaded_draft(path, payload, fallback_date=date_str)
        if draft["date"]:
            drafts.append(draft)

    drafts.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return drafts


def load_draft(
    date_str: str | None = None,
    *,
    session_id: str | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    ensure_draft_dir()

    if path is not None:
        payload = _read_draft_payload(path)
        if payload is None:
            return None
        return _normalize_loaded_draft(path, payload, fallback_date=date_str)

    if not date_str:
        return None

    drafts = list_drafts(date_str)
    if not drafts:
        return None

    if session_id and session_id.strip():
        for draft in drafts:
            if draft.get("session_id", "") == session_id.strip():
                return draft
        return None

    return drafts[0]


def save_draft(
    date_str: str,
    segments: list[dict[str, Any]],
    session_id: str,
    *,
    existing_path: Path | None = None,
) -> Path:
    ensure_draft_dir()

    path = existing_path
    if path is None:
        existing_draft = load_draft(date_str, session_id=session_id)
        path = existing_draft["path"] if existing_draft is not None else _draft_path(date_str, session_id)

    normalized_segments = [_normalize_segment(item) for item in segments]
    payload = {
        "date": date_str,
        "segments": normalized_segments,
        "session_id": session_id,
        "updated_at": _timestamp(),
    }

    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_path.replace(path)
    return path


def delete_draft(
    date_str: str | None = None,
    *,
    session_id: str | None = None,
    path: Path | None = None,
) -> list[Path]:
    removed: list[Path] = []

    if path is not None:
        targets = [path]
    elif date_str and session_id and session_id.strip():
        draft = load_draft(date_str, session_id=session_id)
        targets = [draft["path"]] if draft is not None else []
    elif date_str:
        targets = [draft["path"] for draft in list_drafts(date_str)]
    else:
        targets = []

    for target in targets:
        if target.exists():
            target.unlink()
            removed.append(target)

    return removed


def delete_all_drafts() -> list[Path]:
    removed: list[Path] = []
    for draft in list_drafts():
        removed.extend(delete_draft(path=draft["path"]))
    return removed


def list_draft_summaries(date_str: str | None = None) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for draft in list_drafts(date_str):
        segments = draft["segments"]
        summaries.append(
            {
                "date": draft["date"],
                "segment_count": len(segments),
                "total_min": sum(int(item.get("duration_min", 0) or 0) for item in segments),
                "updated_at": draft.get("updated_at", ""),
                "session_id": draft.get("session_id", ""),
                "path": draft["path"],
            }
        )

    summaries.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return summaries
