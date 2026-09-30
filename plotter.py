from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors, font_manager, patheffects
import numpy as np
import pandas as pd

from config import CHART_WINDOWS

try:
    from scipy.interpolate import PchipInterpolator, make_interp_spline
except Exception:  # pragma: no cover - optional dependency fallback
    PchipInterpolator = None
    make_interp_spline = None


WINDOW_COLORS = {
    7: "#5B8FF9",
    30: "#F6BD16",
    90: "#E8684A",
    None: "#9270CA",
}
MIN_SMOOTH_POINTS = 4


class SmoothingResult(NamedTuple):
    x: np.ndarray
    y: np.ndarray
    backend: str
    reason: str | None = None


def _setup_chinese_font() -> None:
    candidates = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
    ]
    installed = {font.name for font in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.sans-serif"] = [name]
            break
    plt.rcParams["axes.unicode_minus"] = False


def _chart_file_name(window_label: str) -> str:
    return f"总分趋势_{window_label}.png"


def _chart_title(days: int | None) -> str:
    if days is None:
        return "总分趋势（全部历史）"
    return f"总分趋势（最近{days}天）"


def _empty_chart(path: Path, title: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 4.8), facecolor="#F7F9FC")
    ax.set_facecolor("#FFFFFF")
    ax.text(0.5, 0.5, "暂无数据", ha="center", va="center", fontsize=13, color="#667085")
    ax.set_title(title, fontsize=14, color="#1F2937", pad=12)
    ax.set_xlabel("日期")
    ax.set_ylabel("总分")
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.18, linestyle="--")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def _window_subset(df: pd.DataFrame, target_ts: pd.Timestamp, days: int | None) -> pd.DataFrame:
    if days is None:
        return df[df["date"] <= target_ts].copy()

    start_ts = target_ts - pd.Timedelta(days=days - 1)
    mask = (df["date"] >= start_ts) & (df["date"] <= target_ts)
    return df[mask].copy()


def _window_color(days: int | None) -> str:
    return WINDOW_COLORS.get(days, WINDOW_COLORS[None])


def _rgba(hex_color: str, alpha: float) -> tuple[float, float, float, float]:
    red, green, blue, _ = mcolors.to_rgba(hex_color)
    return red, green, blue, alpha


def _build_dense_x(x: np.ndarray) -> np.ndarray:
    return np.linspace(x.min(), x.max(), max(len(x) * 40, 240))


def smoothing_dependencies_available() -> bool:
    return make_interp_spline is not None and PchipInterpolator is not None


def get_smoothing_runtime_status() -> str:
    if smoothing_dependencies_available():
        return "scipy smoothing = ready"
    return "scipy smoothing = missing (install scipy in the active environment to enable spline/PCHIP)"


def _window_log_label(days: int | None) -> str:
    return "all" if days is None else f"{days}d"


def _log_smoothing_backend(days: int | None, backend: str, reason: str | None = None) -> None:
    message = f"[{_window_log_label(days)}] smoothing backend = {backend}"
    if reason:
        message += f" (reason: {reason})"
    print(message)


def _line_fallback(x: np.ndarray, y: np.ndarray, reason: str) -> SmoothingResult:
    return SmoothingResult(x=x, y=y, backend="line_fallback", reason=reason)


def _has_excessive_overshoot(
    x: np.ndarray,
    y: np.ndarray,
    dense_x: np.ndarray,
    dense_y: np.ndarray,
) -> bool:
    if len(x) < 2:
        return False

    for idx in range(len(x) - 1):
        mask = (dense_x >= x[idx]) & (dense_x <= x[idx + 1])
        if not np.any(mask):
            continue
        segment_y = dense_y[mask]
        lower = min(y[idx], y[idx + 1])
        upper = max(y[idx], y[idx + 1])
        tolerance = max(3.0, abs(y[idx + 1] - y[idx]) * 0.35 + 1.5)
        if segment_y.min() < lower - tolerance or segment_y.max() > upper + tolerance:
            return True
    return False


def _smooth_line_data(subset: pd.DataFrame) -> SmoothingResult:
    x = mdates.date2num(subset["date"].tolist())
    y = subset["total_score"].to_numpy(dtype=float)
    if len(x) < MIN_SMOOTH_POINTS:
        return _line_fallback(x, y, f"data points < {MIN_SMOOTH_POINTS}")

    unique_x, unique_indices = np.unique(x, return_index=True)
    unique_y = y[unique_indices]
    if len(unique_x) < MIN_SMOOTH_POINTS:
        return _line_fallback(x, y, f"unique data points < {MIN_SMOOTH_POINTS}")

    dense_x = _build_dense_x(unique_x)
    if not smoothing_dependencies_available():
        return _line_fallback(x, y, "scipy missing")

    spline_reason: str | None = None

    try:
        spline = make_interp_spline(unique_x, unique_y, k=3)
        spline_y = spline(dense_x)
        if not _has_excessive_overshoot(unique_x, unique_y, dense_x, spline_y):
            return SmoothingResult(
                x=dense_x,
                y=np.clip(spline_y, 0.0, 100.0),
                backend="spline",
            )
        spline_reason = "spline overshoot guard"
    except Exception as exc:
        spline_reason = f"spline error: {type(exc).__name__}"

    try:
        interpolator = PchipInterpolator(unique_x, unique_y)
        dense_y = np.clip(interpolator(dense_x), 0.0, 100.0)
        return SmoothingResult(
            x=dense_x,
            y=dense_y,
            backend="pchip",
            reason=spline_reason,
        )
    except Exception as exc:
        reason_parts = [part for part in (spline_reason, f"pchip error: {type(exc).__name__}") if part]
        return _line_fallback(x, y, "; ".join(reason_parts) or "interpolation failed")


def _apply_axis_style(ax, title: str) -> None:
    ax.set_title(title, fontsize=14, color="#1F2937", pad=12)
    ax.set_xlabel("日期", fontsize=10, color="#475467")
    ax.set_ylabel("总分", fontsize=10, color="#475467")
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, 20))
    ax.grid(axis="y", alpha=0.22, linestyle="--", linewidth=0.9)
    ax.grid(axis="x", alpha=0.08, linestyle="--", linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#D0D5DD")
    ax.spines["bottom"].set_color("#D0D5DD")
    ax.tick_params(colors="#475467")
    locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.margins(x=0.03)


def generate_trend_charts(
    daily_summary_df: pd.DataFrame,
    target_date: str,
    chart_dir: Path,
) -> dict[str, Path]:
    chart_dir.mkdir(parents=True, exist_ok=True)
    _setup_chinese_font()

    outputs: dict[str, Path] = {}
    _ = target_date  # Keep the current call signature, but always chart against full history.

    if daily_summary_df.empty:
        for label, days in CHART_WINDOWS:
            path = chart_dir / _chart_file_name(label)
            title = "总分趋势（全部历史）" if label == "全部" else f"总分趋势（最近{label}）"
            _empty_chart(path, title)
            _log_smoothing_backend(days, "line_fallback", "no summary data")
            outputs[label] = path
        return outputs

    df = daily_summary_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["total_score"] = pd.to_numeric(df["total_score"], errors="coerce").fillna(0.0)
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if df.empty:
        for label, days in CHART_WINDOWS:
            path = chart_dir / _chart_file_name(label)
            _empty_chart(path, _chart_title(days))
            _log_smoothing_backend(days, "line_fallback", "no valid summary data")
            outputs[label] = path
        return outputs

    chart_end_ts = df["date"].max()

    for label, days in CHART_WINDOWS:
        subset = _window_subset(df, chart_end_ts, days)
        title = _chart_title(days)
        path = chart_dir / _chart_file_name(label)
        if subset.empty:
            _empty_chart(path, title)
            _log_smoothing_backend(days, "line_fallback", "no data in window")
            outputs[label] = path
            continue

        subset = subset.reset_index(drop=True)
        avg_score = float(subset["total_score"].mean())
        line_color = _window_color(days)
        fill_color = _rgba(line_color, 0.16)
        marker_color = _rgba(line_color, 0.95)
        smooth_result = _smooth_line_data(subset)
        _log_smoothing_backend(days, smooth_result.backend, smooth_result.reason)

        fig, ax = plt.subplots(figsize=(11, 4.8), facecolor="#F7F9FC")
        ax.set_facecolor("#FFFFFF")

        if len(smooth_result.x) >= 2:
            ax.fill_between(
                mdates.num2date(smooth_result.x),
                smooth_result.y,
                0,
                color=fill_color,
                zorder=1,
            )
            ax.plot(
                mdates.num2date(smooth_result.x),
                smooth_result.y,
                linewidth=3.0 if smooth_result.backend != "line_fallback" else 2.6,
                color=line_color,
                alpha=0.92,
                solid_capstyle="round",
                antialiased=True,
                zorder=2,
            )

        ax.scatter(
            subset["date"],
            subset["total_score"],
            s=38,
            color=marker_color,
            edgecolors="#FFFFFF",
            linewidths=1.0,
            zorder=3,
        )
        ax.axhline(
            avg_score,
            color="#98A2B3",
            linestyle="--",
            linewidth=1.4,
            alpha=0.95,
            zorder=1,
        )
        avg_text_y = min(max(avg_score / 100.0 + 0.045, 0.12), 0.9)
        ax.text(
            0.98,
            avg_text_y,
            f"平均值：{avg_score:.1f}",
            transform=ax.transAxes,
            ha="right",
            va="center",
            fontsize=10,
            color="#475467",
            bbox={
                "boxstyle": "round,pad=0.28",
                "facecolor": "#FFFFFF",
                "edgecolor": "#D0D5DD",
                "alpha": 0.95,
            },
        )

        last_date = subset["date"].iloc[-1]
        last_score = float(subset["total_score"].iloc[-1])
        ax.annotate(
            f"{last_score:.1f}",
            xy=(last_date, last_score),
            xytext=(12, 12),
            textcoords="offset points",
            fontsize=10,
            color=line_color,
            ha="left",
            va="bottom",
            clip_on=False,
            path_effects=[
                patheffects.Stroke(linewidth=2.6, foreground="#FFFFFF", alpha=0.95),
                patheffects.Normal(),
            ],
        )

        _apply_axis_style(ax, title)
        fig.tight_layout()
        fig.savefig(path, dpi=150, facecolor=fig.get_facecolor())
        plt.close(fig)
        outputs[label] = path

    return outputs
