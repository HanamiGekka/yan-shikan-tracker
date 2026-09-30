from __future__ import annotations

from typing import Any

import pandas as pd

from category_registry import FEELING_MULTIPLIERS, normalize_category_name, normalize_feeling
from config import DAILY_SUMMARY_COLUMNS, SCORE_DETAIL_COLUMNS


def apply_feeling(duration_min: float, feeling: int) -> float:
    normalized_feeling = normalize_feeling(feeling)
    multiplier = FEELING_MULTIPLIERS.get(normalized_feeling, FEELING_MULTIPLIERS[2])
    return float(duration_min) * multiplier


def _safe_positive(value: Any, fallback: float) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed) or float(parsed) <= 0:
        return float(fallback)
    return float(parsed)


def _clip_ratio(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _target_ratio(total: float, target_min: float, lower_min: float, upper_min: float) -> float:
    target = _safe_positive(target_min, 60.0)
    lower = max(0.0, float(lower_min))
    upper = max(float(upper_min), target)

    if lower > target:
        lower = target
    if upper < target:
        upper = target

    if lower == target:
        lower = max(0.0, target * 0.7)
    if upper == target:
        upper = target * 1.3

    if total < lower:
        if lower <= 0:
            return 0.0
        return _clip_ratio(0.5 * total / lower)

    if total > upper:
        return _clip_ratio(0.5 * (1.0 - (total - upper) / max(upper, 1.0)))

    if total <= target:
        span = max(target - lower, 1.0)
        return _clip_ratio(0.5 + 0.5 * (total - lower) / span)

    span = max(upper - target, 1.0)
    return _clip_ratio(1.0 - 0.5 * (total - target) / span)


def score_category(
    total_recorded_min: float,
    total_effective_min: float,
    mode: str,
    target_min: float,
    lower_min: float,
    upper_min: float,
    weight: float,
) -> float:
    recorded = max(0.0, float(total_recorded_min))
    total = max(0.0, float(total_effective_min))
    mode = str(mode).strip().lower()
    weight = max(0.0, float(weight))

    if mode == "record_only" or weight <= 0:
        return 0.0

    # If actual time was spent but effective time still resolves to zero
    # (for example, invalid or degenerate input), the category should not keep
    # a baseline reward.
    if recorded > 0 and total <= 0:
        return 0.0

    if mode == "maximize":
        target = _safe_positive(target_min, 60.0)
        ratio = _clip_ratio(total / target)
        return weight * ratio

    if mode == "target":
        ratio = _target_ratio(total, target_min, lower_min, upper_min)
        return weight * ratio

    if mode == "minimize":
        upper = _safe_positive(upper_min, _safe_positive(target_min, 60.0))
        ratio = _clip_ratio(1.0 - total / upper)
        return weight * ratio

    if mode == "range":
        lower = max(0.0, float(lower_min))
        upper = max(float(upper_min), lower + 1.0)
        if lower <= total <= upper:
            ratio = 1.0
        elif total < lower:
            ratio = total / lower if lower > 0 else 0.0
        else:
            ratio = 1.0 - (total - upper) / upper
        return weight * _clip_ratio(ratio)

    return 0.0


def _prepare_time_log(time_log_df: pd.DataFrame) -> pd.DataFrame:
    if time_log_df.empty:
        return pd.DataFrame(
            columns=["date", "category", "duration_min", "feeling", "effective_min", "segment_count"]
        )

    df = time_log_df.copy()
    for col in ["date", "category", "duration_min", "feeling"]:
        if col not in df.columns:
            df[col] = ""

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["date"])
    df = df[df["date"].astype(str).str.len() > 0]

    df["category"] = df["category"].map(normalize_category_name)
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").fillna(0.0)
    df["duration_min"] = df["duration_min"].clip(lower=0.0)
    df["feeling"] = df["feeling"].apply(normalize_feeling)
    df["effective_min"] = df.apply(
        lambda row: apply_feeling(row["duration_min"], row["feeling"]),
        axis=1,
    )
    df["segment_count"] = 1
    return df


def _prepare_category_config(category_config_df: pd.DataFrame) -> pd.DataFrame:
    if category_config_df.empty:
        return pd.DataFrame(
            columns=["category", "mode", "target_min", "lower_min", "upper_min", "weight", "core"]
        )

    df = category_config_df.copy()
    for col in ["category", "mode", "target_min", "lower_min", "upper_min", "weight", "core"]:
        if col not in df.columns:
            df[col] = 0

    df["category"] = df["category"].map(normalize_category_name)
    df["mode"] = df["mode"].astype(str).str.strip().str.lower()
    for col in ["target_min", "lower_min", "upper_min", "weight"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["core"] = pd.to_numeric(df["core"], errors="coerce").fillna(0).astype(int)
    df["core"] = df["core"].clip(lower=0, upper=1)
    df = df.drop_duplicates(subset=["category"], keep="last")
    df = df.reset_index(drop=True)
    df["category_order"] = df.index
    return df


def compute_daily_scores(
    time_log_df: pd.DataFrame,
    category_config_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    # TODO(vNext): support different scoring profiles for different day types
    # such as study days / class days / system-building days / recovery days.
    # This version still intentionally uses one unified scoring rule for all days.
    clean_log = _prepare_time_log(time_log_df)
    clean_config = _prepare_category_config(category_config_df)

    if clean_log.empty or clean_config.empty:
        empty_summary = pd.DataFrame(columns=DAILY_SUMMARY_COLUMNS)
        empty_detail = pd.DataFrame(columns=SCORE_DETAIL_COLUMNS)
        return empty_summary, empty_detail

    grouped_log = (
        clean_log.groupby(["date", "category"], as_index=False)
        .agg(
            total_recorded_min=("duration_min", "sum"),
            total_effective_min=("effective_min", "sum"),
            segment_count=("segment_count", "sum"),
        )
    )

    dates_df = pd.DataFrame({"date": sorted(clean_log["date"].unique().tolist())})
    dates_df["__k"] = 1
    config_df = clean_config.copy()
    config_df["__k"] = 1
    date_category_grid = dates_df.merge(config_df, on="__k", how="inner").drop(columns=["__k"])

    scored = date_category_grid.merge(grouped_log, on=["date", "category"], how="left")
    scored["total_recorded_min"] = scored["total_recorded_min"].fillna(0.0)
    scored["total_effective_min"] = scored["total_effective_min"].fillna(0.0)
    scored["segment_count"] = scored["segment_count"].fillna(0).astype(int)

    scored["category_score"] = scored.apply(
        lambda row: score_category(
            total_recorded_min=row["total_recorded_min"],
            total_effective_min=row["total_effective_min"],
            mode=row["mode"],
            target_min=row["target_min"],
            lower_min=row["lower_min"],
            upper_min=row["upper_min"],
            weight=row["weight"],
        ),
        axis=1,
    )

    daily_score_df = (
        scored.groupby("date", as_index=False)
        .agg(total_score=("category_score", "sum"))
    )
    daily_record_df = (
        clean_log.groupby("date", as_index=False)
        .agg(
            total_recorded_min=("duration_min", "sum"),
            segment_count=("segment_count", "sum"),
        )
    )
    core_df = (
        scored[scored["core"] == 1]
        .groupby("date", as_index=False)
        .agg(core_growth_score=("category_score", "sum"))
    )

    summary_df = daily_score_df.merge(daily_record_df, on="date", how="left")
    summary_df = summary_df.merge(core_df, on="date", how="left")
    summary_df["total_recorded_min"] = summary_df["total_recorded_min"].fillna(0.0)
    summary_df["segment_count"] = summary_df["segment_count"].fillna(0).astype(int)
    summary_df["core_growth_score"] = summary_df["core_growth_score"].fillna(0.0)
    summary_df["total_score"] = summary_df["total_score"].fillna(0.0)
    summary_df = summary_df[DAILY_SUMMARY_COLUMNS].sort_values("date").reset_index(drop=True)

    scored = scored.sort_values(["date", "category_order"]).reset_index(drop=True)
    scored = scored[SCORE_DETAIL_COLUMNS]
    return summary_df, scored
