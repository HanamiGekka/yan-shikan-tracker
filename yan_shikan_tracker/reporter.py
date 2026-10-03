from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import CORE_CATEGORY_SET
from .category_registry import CATEGORY_JAPAN_MASTERS_EXAM


PRIORITY_CATEGORIES = (CATEGORY_JAPAN_MASTERS_EXAM, "日语JLPT", "专业能力", "运动")
LOW_VALUE_CATEGORIES = ("内务处理", "休息", "其他", "额外睡觉")


def _safe_float(value: Any) -> float:
    parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(parsed):
        return 0.0
    return float(parsed)


def _safe_int(value: Any) -> int:
    return int(round(_safe_float(value)))


def _get_day_summary(target_date: str, daily_summary_df: pd.DataFrame) -> pd.Series | None:
    day_df = daily_summary_df[daily_summary_df["date"] == target_date]
    if day_df.empty:
        return None
    return day_df.iloc[0]


def _get_day_detail(target_date: str, category_detail_df: pd.DataFrame) -> pd.DataFrame:
    if category_detail_df.empty:
        return pd.DataFrame(columns=category_detail_df.columns)
    return category_detail_df[category_detail_df["date"] == target_date].copy()


def _get_category_row(day_detail_df: pd.DataFrame, category: str) -> pd.Series | None:
    hit = day_detail_df[day_detail_df["category"] == category]
    if hit.empty:
        return None
    return hit.iloc[0]


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator) / float(denominator)


def _round_minutes(value: float, step: int = 5) -> int:
    if value <= 0:
        return 0
    return int(round(value / step) * step)


def _recent_low_streak(
    target_date: str,
    category: str,
    threshold: float,
    category_detail_df: pd.DataFrame,
) -> int:
    if category_detail_df.empty:
        return 0

    history = category_detail_df[category_detail_df["category"] == category].copy()
    if history.empty:
        return 0

    history["date"] = pd.to_datetime(history["date"], errors="coerce")
    target_ts = pd.to_datetime(target_date, errors="coerce")
    history = history[(history["date"].notna()) & (history["date"] <= target_ts)].sort_values("date")
    if history.empty:
        return 0

    streak = 0
    for _, row in history.iloc[::-1].iterrows():
        if _safe_float(row["total_effective_min"]) < threshold:
            streak += 1
            continue
        break
    return streak


def _suggest_recovery_minutes(category: str, target_min: float, deficit_min: float) -> int:
    if category == "运动":
        return min(max(20, _round_minutes(max(deficit_min, 20), step=5)), 30)

    base = max(30.0, min(deficit_min, max(target_min * 0.5, 45.0)))
    return min(max(30, _round_minutes(base, step=5)), 120)


def _build_issues_and_suggestions(
    target_date: str,
    summary_row: pd.Series,
    day_detail_df: pd.DataFrame,
    category_detail_df: pd.DataFrame,
    category_config_df: pd.DataFrame,
) -> tuple[list[str], list[str]]:
    total_recorded = _safe_float(summary_row.get("total_recorded_min", 0))
    total_score = _safe_float(summary_row.get("total_score", 0))
    core_score = _safe_float(summary_row.get("core_growth_score", 0))
    total_max_score = _safe_float(category_config_df["weight"].sum())
    core_max_score = _safe_float(category_config_df[category_config_df["core"] == 1]["weight"].sum())

    core_effective = _safe_float(day_detail_df[day_detail_df["core"] == 1]["total_effective_min"].sum())
    non_core_effective = _safe_float(day_detail_df[day_detail_df["core"] == 0]["total_effective_min"].sum())
    top3_categories = (
        day_detail_df[day_detail_df["total_recorded_min"] > 0]
        .sort_values("total_recorded_min", ascending=False)
        .head(3)["category"]
        .astype(str)
        .tolist()
    )
    day_lookup = {str(row["category"]): row for _, row in day_detail_df.iterrows()}

    issue_candidates: list[tuple[int, str]] = []
    suggestion_candidates: list[tuple[int, str]] = []

    def add_issue(priority: int, text: str) -> None:
        issue_candidates.append((priority, text))

    def add_suggestion(priority: int, text: str) -> None:
        suggestion_candidates.append((priority, text))

    for category in PRIORITY_CATEGORIES:
        row = day_lookup.get(category)
        if row is None:
            continue

        effective_min = _safe_float(row["total_effective_min"])
        target_min = _safe_float(row["target_min"])
        weight = _safe_float(row["weight"])
        if target_min <= 0:
            continue

        streak_threshold = max(20.0, target_min * 0.5)
        streak = _recent_low_streak(target_date, category, streak_threshold, category_detail_df)
        ratio = _safe_ratio(effective_min, target_min)
        if ratio < 0.7:
            deficit_min = max(0.0, target_min - effective_min)
            streak_text = (
                f"，且已连续 {streak} 天低于 {streak_threshold:.0f} 分钟警戒线"
                if streak >= 2
                else ""
            )
            add_issue(
                int(weight * 10),
                f"{category}今天有效投入 {effective_min:.0f} 分钟，距离 {target_min:.0f} 分钟目标还差 {deficit_min:.0f} 分钟{streak_text}，优先级明显没顶住。",
            )
            recovery_min = _suggest_recovery_minutes(category, target_min, deficit_min)
            if category == CATEGORY_JAPAN_MASTERS_EXAM:
                add_suggestion(
                    int(weight * 10),
                    f"明天第一步先开日本修士考相关准备，至少补 {recovery_min} 分钟深度块，先碰最难或最抗拒的一块。",
                )
            elif category == "运动":
                add_suggestion(
                    int(weight * 10),
                    f"明天补上 {recovery_min} 分钟运动，放在下午或晚饭前，先完成再安排休息和娱乐。",
                )
            else:
                add_suggestion(
                    int(weight * 10),
                    f"明天给{category}先补 {recovery_min} 分钟，最好放进前半天固定时间窗，避免再次被琐事挤掉。",
                )
        elif streak >= 2:
            add_issue(
                int(weight * 9),
                f"{category}已经连续 {streak} 天低于 {streak_threshold:.0f} 分钟警戒线，长期欠账正在累积。",
            )
            add_suggestion(
                int(weight * 9),
                f"明天把{category}固定进不可挪动的时段，至少先守住 {streak_threshold:.0f} 分钟底线。",
            )

    sleep_row = day_lookup.get("睡觉")
    if sleep_row is not None:
        sleep_eff = _safe_float(sleep_row["total_effective_min"])
        sleep_low = _safe_float(sleep_row["lower_min"])
        sleep_up = _safe_float(sleep_row["upper_min"])
        if sleep_low > 0 and sleep_eff < sleep_low:
            sleep_gap = max(0.0, sleep_low - sleep_eff)
            add_issue(
                95,
                f"睡觉今天有效时长只有 {sleep_eff:.0f} 分钟，低于下限 {sleep_low:.0f} 分钟约 {sleep_gap:.0f} 分钟，恢复质量偏弱。",
            )
            add_suggestion(
                95,
                "今晚优先把睡眠拉回 7 小时以上，明早固定起床时间，尽量不要再靠额外补觉修正。",
            )
        elif sleep_up > 0 and sleep_eff > sleep_up:
            overflow = sleep_eff - sleep_up
            add_issue(
                82,
                f"睡觉时长比上限多出约 {overflow:.0f} 分钟，节律可能已经开始松动。",
            )
            add_suggestion(
                82,
                "明天先固定起床点，再观察白天状态，不要把低效直接转成更长睡眠。",
            )

    extra_sleep_row = day_lookup.get("额外睡觉")
    if extra_sleep_row is not None:
        extra_sleep_eff = _safe_float(extra_sleep_row["total_effective_min"])
        extra_sleep_up = _safe_float(extra_sleep_row["upper_min"])
        if extra_sleep_up > 0 and extra_sleep_eff > extra_sleep_up:
            add_issue(
                72,
                f"额外补觉用了 {extra_sleep_eff:.0f} 分钟，已经超过上限 {extra_sleep_up:.0f} 分钟，白天节奏有被打散的迹象。",
            )
            add_suggestion(
                72,
                "明天把高耗脑任务拆成更短的执行块，优先减少无计划补觉，而不是把疲劳继续后移。",
            )

    think_row = day_lookup.get("思考探索")
    if think_row is not None:
        think_eff = _safe_float(think_row["total_effective_min"])
        think_up = _safe_float(think_row["upper_min"])
        if think_up > 0 and think_eff > think_up:
            add_issue(
                78,
                f"思考探索今天用了 {think_eff:.0f} 分钟，高于上限 {think_up:.0f} 分钟，容易挤占执行类任务。",
            )
            capped_min = max(45, min(_round_minutes(think_up, step=5), 90))
            add_suggestion(
                78,
                f"明天把思考探索上限先卡在 {capped_min} 分钟，并在结束前写出 1 个可执行下一步，避免只思考不落地。",
            )

    low_value_df = day_detail_df[day_detail_df["category"].isin(LOW_VALUE_CATEGORIES)]
    low_value_recorded = _safe_float(low_value_df["total_recorded_min"].sum())
    low_value_share = _safe_ratio(low_value_recorded, total_recorded)
    if low_value_recorded >= 180 and low_value_share >= 0.18:
        low_value_names = (
            low_value_df[low_value_df["total_recorded_min"] > 0]
            .sort_values("total_recorded_min", ascending=False)
            .head(2)["category"]
            .astype(str)
            .tolist()
        )
        lead_text = " / ".join(low_value_names) if low_value_names else "低价值类别"
        add_issue(
            76,
            f"{lead_text}今天合计占了 {low_value_recorded:.0f} 分钟，占全天记录约 {low_value_share:.0%}，对主线形成了实质挤压。",
        )
        compress_min = max(30, min(_round_minutes(low_value_recorded - 150, step=5), 90))
        add_suggestion(
            76,
            f"明天把内务处理、休息、其他这类低价值时段合计压缩 {compress_min} 分钟左右，尽量集中到一个统一窗口处理。",
        )

    if total_recorded < 1000:
        add_issue(60, f"今天总记录只有 {total_recorded:.0f} 分钟，全天覆盖还不完整，容易漏掉真正挤占时间的碎片段。")
        add_suggestion(60, "明天优先补齐碎片时间记录，先把覆盖拉到 1200 分钟附近，再看结构问题。")

    if non_core_effective > core_effective:
        add_issue(
            74,
            f"非核心有效时长 {non_core_effective:.0f} 分钟已经高于核心投入 {core_effective:.0f} 分钟，优先级执行出现了反转。",
        )
        add_suggestion(
            74,
            "明天把核心任务尽量前置到白天，非核心活动只留给收尾时段，不要再和主线抢前半天。",
        )

    total_ratio = _safe_ratio(total_score, total_max_score)
    core_ratio = _safe_ratio(core_score, core_max_score)
    if total_ratio - core_ratio >= 0.12:
        add_issue(
            71,
            f"今天总分 {total_score:.2f} / {total_max_score:.0f} 还有托底，但核心成长分只有 {core_score:.2f} / {core_max_score:.0f}，主线推进和整体分数明显脱节。",
        )
        add_suggestion(
            71,
            "明天先补核心类缺口，再去处理能托住总分但不真正推进长期目标的项目。",
        )

    if CATEGORY_JAPAN_MASTERS_EXAM not in top3_categories and CATEGORY_JAPAN_MASTERS_EXAM in day_lookup:
        grad_eff = _safe_float(day_lookup[CATEGORY_JAPAN_MASTERS_EXAM]["total_effective_min"])
        grad_target = _safe_float(day_lookup[CATEGORY_JAPAN_MASTERS_EXAM]["target_min"])
        if grad_target > 0 and grad_eff < grad_target * 0.7:
            top_text = " / ".join(top3_categories) if top3_categories else "当前前三类别"
            add_issue(
                69,
                f"今天投入最多的前三类别是 {top_text}，日本修士考没有进入前三，和当前长期优先级不完全一致。",
            )

    if total_score < 60:
        add_suggestion(58, "明天先守住高权重项目的底线，把总分尽量拉回 60+，再去优化细节。")

    issues = [
        text
        for _, text in sorted(issue_candidates, key=lambda item: (-item[0], item[1]))
        if text
    ]
    suggestions = [
        text
        for _, text in sorted(suggestion_candidates, key=lambda item: (-item[0], item[1]))
        if text
    ]

    issues = list(dict.fromkeys(issues))[:5]
    suggestions = list(dict.fromkeys(suggestions))[:4]

    if len(issues) < 3:
        if top3_categories:
            issues.append(f"今天投入最高的类别集中在 {' / '.join(top3_categories)}，明天需要继续检查这和长期主线是否一致。")
        else:
            issues.append("今天没有足够多的有效记录可供诊断，结构问题可能被低估了。")
        issues = list(dict.fromkeys(issues))[:5]

    if len(suggestions) < 3:
        best_core_df = day_detail_df[
            (day_detail_df["category"].isin(PRIORITY_CATEGORIES))
            & (day_detail_df["total_effective_min"] > 0)
        ].sort_values("category_score", ascending=False)
        if not best_core_df.empty:
            best_category = str(best_core_df.iloc[0]["category"])
            suggestions.append(f"把今天相对最稳的 {best_category} 继续保留到明天同一时段，避免刚建立的势头断掉。")
        suggestions = list(dict.fromkeys(suggestions))[:4]

    if len(suggestions) < 3:
        suggestions.append("明天开始前先写下 1 个必须完成的核心动作，再打开当天记录，先保主线再扩散。")
        suggestions = list(dict.fromkeys(suggestions))[:4]

    return issues, suggestions


def _build_top_category_lines(day_detail_df: pd.DataFrame) -> list[str]:
    top3 = (
        day_detail_df[day_detail_df["total_recorded_min"] > 0]
        .sort_values("total_recorded_min", ascending=False)
        .head(3)
    )
    if top3.empty:
        return ["- 无可用记录"]

    lines: list[str] = []
    for _, row in top3.iterrows():
        recorded_min = _safe_float(row["total_recorded_min"])
        recorded_hours = recorded_min / 60.0
        effective_min = _safe_float(row["total_effective_min"])
        score = _safe_float(row["category_score"])
        lines.append(
            f"- {row['category']}：{_safe_int(recorded_min)} 分钟（{recorded_hours:.2f} 小时），"
            f"有效 {effective_min:.1f} 分钟，得分 {score:.2f}"
        )
    return lines


def generate_today_report(
    target_date: str,
    daily_summary_df: pd.DataFrame,
    category_detail_df: pd.DataFrame,
    category_config_df: pd.DataFrame,
    output_path: Path,
) -> str:
    summary_row = _get_day_summary(target_date, daily_summary_df)
    day_detail_df = _get_day_detail(target_date, category_detail_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if summary_row is None:
        text = f"日期：{target_date}\n未找到该日期数据，无法生成日报。\n"
        output_path.write_text(text, encoding="utf-8")
        return text

    core_max_score = _safe_float(category_config_df[category_config_df["core"] == 1]["weight"].sum())
    issues, suggestions = _build_issues_and_suggestions(
        target_date=target_date,
        summary_row=summary_row,
        day_detail_df=day_detail_df,
        category_detail_df=category_detail_df,
        category_config_df=category_config_df,
    )
    top_category_lines = _build_top_category_lines(day_detail_df)

    total_min = _safe_float(summary_row["total_recorded_min"])
    total_hours = total_min / 60.0
    total_score = _safe_float(summary_row["total_score"])
    core_score = _safe_float(summary_row["core_growth_score"])

    lines = [
        f"日期：{target_date}",
        "",
        "一、单日总览",
        f"今日录入时间段数量：{_safe_int(summary_row['segment_count'])}",
        f"今日总记录时长：{_safe_int(total_min)} 分钟（{total_hours:.2f} 小时）",
        f"今日总体效率分（0~100）：{total_score:.2f}",
        f"今日核心成长分：{core_score:.2f} / {core_max_score:.2f}",
        "核心成长说明：核心分只统计 睡觉、日本修士考、日语JLPT、运动、思考探索、专业能力。",
        "",
        "二、今日投入最多的前3个类别",
    ]

    lines.extend(top_category_lines)

    lines.append("")
    lines.append("三、今日需要注意的问题")
    for item in issues:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("四、明日建议")
    for idx, item in enumerate(suggestions, start=1):
        lines.append(f"{idx}. {item}")

    text = "\n".join(lines) + "\n"
    output_path.write_text(text, encoding="utf-8")
    return text


def _build_7d_compare_text(
    target_date: str,
    daily_summary_df: pd.DataFrame,
    category_detail_df: pd.DataFrame,
    day_detail_df: pd.DataFrame,
) -> str:
    summary_df = daily_summary_df.copy()
    summary_df["date"] = pd.to_datetime(summary_df["date"], errors="coerce")
    target_ts = pd.to_datetime(target_date)

    history = summary_df[summary_df["date"] < target_ts].sort_values("date").tail(7)
    if len(history) < 3:
        return "最近历史数据不足（少于 3 天），暂不做 7 日均值比较。"

    today_row = summary_df[summary_df["date"] == target_ts].iloc[0]
    lines = [
        (
            f"- 总记录分钟数：今日 {_safe_float(today_row['total_recorded_min']):.1f}，"
            f"近7日均值 {_safe_float(history['total_recorded_min'].mean()):.1f}"
        ),
        (
            f"- 总体效率分：今日 {_safe_float(today_row['total_score']):.2f}，"
            f"近7日均值 {_safe_float(history['total_score'].mean()):.2f}"
        ),
        (
            f"- 核心成长分：今日 {_safe_float(today_row['core_growth_score']):.2f}，"
            f"近7日均值 {_safe_float(history['core_growth_score'].mean()):.2f}"
        ),
        "- 各类别有效时长（今日 vs 近7日均值）：",
    ]

    detail_df = category_detail_df.copy()
    detail_df["date"] = pd.to_datetime(detail_df["date"], errors="coerce")
    recent_dates = set(history["date"].dt.strftime("%Y-%m-%d").tolist())
    recent_detail = detail_df[detail_df["date"].dt.strftime("%Y-%m-%d").isin(recent_dates)]
    avg_map = (
        recent_detail.groupby("category", as_index=False)["total_effective_min"].mean()
        if not recent_detail.empty
        else pd.DataFrame(columns=["category", "total_effective_min"])
    )
    avg_dict = dict(zip(avg_map["category"], avg_map["total_effective_min"]))

    for _, row in day_detail_df.sort_values("weight", ascending=False).iterrows():
        category = str(row["category"])
        today_eff = _safe_float(row["total_effective_min"])
        avg_eff = _safe_float(avg_dict.get(category, 0.0))
        lines.append(f"  {category}: 今日 {today_eff:.1f}，近7日均值 {avg_eff:.1f}")

    return "\n".join(lines)


def generate_llm_prompt(
    target_date: str,
    daily_summary_df: pd.DataFrame,
    category_detail_df: pd.DataFrame,
    category_config_df: pd.DataFrame,
    output_path: Path,
) -> str:
    summary_row = _get_day_summary(target_date, daily_summary_df)
    day_detail_df = _get_day_detail(target_date, category_detail_df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if summary_row is None:
        text = f"日期：{target_date}\n未找到该日期数据，请先录入后重试。\n"
        output_path.write_text(text, encoding="utf-8")
        return text

    core_max_score = _safe_float(category_config_df[category_config_df["core"] == 1]["weight"].sum())
    compare_text = _build_7d_compare_text(target_date, daily_summary_df, category_detail_df, day_detail_df)

    category_lines = []
    for _, row in day_detail_df.sort_values("weight", ascending=False).iterrows():
        core_tag = "核心" if str(row["category"]) in CORE_CATEGORY_SET else "非核心"
        category_lines.append(
            (
                f"- {row['category']}（{core_tag}）: "
                f"原始{_safe_float(row['total_recorded_min']):.1f}分, "
                f"有效{_safe_float(row['total_effective_min']):.1f}分, "
                f"得分{_safe_float(row['category_score']):.2f}"
            )
        )

    prompt = (
        "请作为时间管理教练分析以下记录。\n"
        "请你详细分析一下我们今天的时间消耗吧，请一定要结合我们时间记录Data Excel里面的备注进行详细分析。\n"
        "并且，请你结合我们已有的过往所有聊天记录、相关数据和文件，分析我们昨天的优劣，综合以下数据给出结构化分析。\n\n"
        "【当日关键指标】\n"
        f"- 日期：{target_date}\n"
        f"- 今日总记录分钟数：{_safe_float(summary_row['total_recorded_min']):.1f}\n"
        f"- 今日总体效率分（0~100）：{_safe_float(summary_row['total_score']):.2f}\n"
        f"- 今日核心成长分：{_safe_float(summary_row['core_growth_score']):.2f} / {core_max_score:.2f}\n\n"
        "【各类别数据（原始时长/有效时长/得分）】\n"
        f"{chr(10).join(category_lines) if category_lines else '- 无数据'}\n\n"
        "【与最近7日均值比较】\n"
        f"{compare_text}\n\n"
        "【请按以下5点输出，并结合我们的自检问题分析】\n"
        "1. 今天的时间结构是否合理。\n"
        "2. 哪些类别投入不足。\n"
        "3. 哪些低价值类别占用过多。\n"
        "4. 明天最值得优化的3个动作（必须具体可执行）。\n"
        "5. 今天是否符合长期优先级。\n\n"

        "【长期优先级（固定）】\n"
        "- 日本修士考\n"
        "- 日语JLPT\n"
        "- 睡眠稳定\n"
        "- 适量运动\n"
        "- 专业能力成长\n"
        "- 思考探索不过度脱离执行\n\n"

        "【我们目前阶段的自检问题】\n"
        "- 今天日本修士考相关准备有没有启动？专业基础、英语、研究计划或申请相关准备里推进了什么？\n"
        "- 今天日语JLPT有没有不断档？课程、真题或复盘推进了什么？\n"
        "- 中午有没有塌？有没有吃撑？\n"
        "- 课程任务有没有超时？有没有超过90 min?\n"
        "- 思考探索有没有输出结果？\n"
        "- 内务处理有没有尽可能提效？\n"
        "- 睡前有没有把明天第一锚定好？\n"
    )

    output_path.write_text(prompt, encoding="utf-8")
    return prompt
