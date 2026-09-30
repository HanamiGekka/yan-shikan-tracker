from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from category_registry import FEELING_GUIDE_TEXT, describe_feeling
from config import CATEGORY_MENU, MENU_CODE_TO_CATEGORY
from draft_io import (
    build_draft_segment,
    delete_all_drafts,
    delete_draft,
    list_draft_summaries,
    load_draft,
    save_draft,
)
from session_flow import commit_confirmed_segments, print_session_write_result


QUIT_COMMANDS = {"q", "quit"}


class RecordingSessionAbort(Exception):
    """Normal exit intent from the current recording session."""


@dataclass
class DailyInputResult:
    flow_status: str
    date_str: str | None = None
    session_id: str | None = None
    exit_program: bool = False


def _today_str() -> str:
    return datetime.now().date().isoformat()


def _make_session_id(date_str: str) -> str:
    return f"{date_str}_{datetime.now().strftime('%H%M%S')}"


def _is_quit_command(raw: str) -> bool:
    return raw.strip().lower() in QUIT_COMMANDS


def prompt_date_value(prompt: str, *, default_today: bool = False) -> str:
    while True:
        raw = input(prompt).strip()
        if not raw and default_today:
            return _today_str()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
        except ValueError:
            print("日期格式不对喵，请按 YYYY-MM-DD 重新输入哦。")


def _input_record_date() -> str | None:
    while True:
        raw = input("请输入要录入的日期喵（YYYY-MM-DD，回车默认今天，q 返回主菜单）：").strip()
        if not raw:
            return _today_str()
        if _is_quit_command(raw):
            return None
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date().isoformat()
        except ValueError:
            print("日期格式不对喵，请按 YYYY-MM-DD 重新输入哦。")


def prompt_date_range() -> tuple[str, str]:
    start_date = prompt_date_value("请输入起始日期喵（YYYY-MM-DD）：")
    end_date = prompt_date_value("请输入结束日期喵（YYYY-MM-DD）：")
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return start_date, end_date


def prompt_yes_no(prompt: str) -> bool:
    while True:
        raw = input(prompt).strip().lower()
        if raw == "y":
            return True
        if raw == "n":
            return False
        print("请输入 y 或 n 喵。")


def choose_main_menu_action() -> str:
    print("\n===== 主菜单喵 =====")
    print("1. 录入今日时间")
    print("2. 输出管理")
    print("3. 退出")
    while True:
        raw = input("请选择功能喵：").strip()
        if raw == "1":
            return "record"
        if raw == "2":
            return "output"
        if raw in {"3", "0"}:
            return "exit"
        print("请输入 1、2 或 3 喵。")


def choose_output_management_action() -> str:
    print("\n===== 输出管理~o( =∩ω∩= )m =====")
    print("1. 重建当日 output")
    print("2. 重建全部 output")
    print("3. 重建指定日期范围 output")
    print("4. 重绘图像")
    print("5. 清除当日 backup")
    print("6. 清除全部 backup")
    print("0. 返回上一层")
    while True:
        raw = input("请选择操作喵：").strip()
        if raw == "1":
            return "rebuild_today"
        if raw == "2":
            return "rebuild_all"
        if raw == "3":
            return "rebuild_range"
        if raw == "4":
            return "redraw_charts"
        if raw == "5":
            return "clear_today_backup"
        if raw == "6":
            return "clear_all_backup"
        if raw == "0":
            return "back"
        print("请输入 1、2、3、4、5、6 或 0 喵。")


def _fresh_session(date_str: str | None = None) -> dict[str, Any]:
    safe_date = date_str
    if safe_date is None:
        safe_date = _input_record_date()
        if safe_date is None:
            return {"action": "back"}
    return {
        "action": "start",
        "date_str": safe_date,
        "segments": [],
        "session_id": _make_session_id(safe_date),
        "draft_path": None,
    }


def _input_duration() -> int:
    while True:
        raw = input("填写当前时间段时长喵（分钟）：").strip()
        if _is_quit_command(raw):
            raise RecordingSessionAbort
        if raw.isdigit():
            value = int(raw)
            if 0 <= value <= 1440:
                return value
        print("请输入 0 到 1440 的整数喵；如果想结束这次录入，输入 q 就好。")


def _print_category_menu() -> None:
    print("请选择类别编号喵：")
    for code, category in CATEGORY_MENU:
        print(f"  {code}. {category}")


def _input_category() -> str:
    while True:
        _print_category_menu()
        raw = input("请输入类别编号喵：").strip().lower()
        if _is_quit_command(raw):
            raise RecordingSessionAbort
        if raw in MENU_CODE_TO_CATEGORY:
            return MENU_CODE_TO_CATEGORY[raw]
        print("类别编号不对喵，再看一眼菜单慢慢选。")


def _input_feeling() -> int:
    print(f"feeling 参考：{FEELING_GUIDE_TEXT}")
    while True:
        raw = input("请输入 feeling（0-3）喵：").strip()
        if _is_quit_command(raw):
            raise RecordingSessionAbort
        if raw in {"0", "1", "2", "3"}:
            return int(raw)
        print("feeling 只能是 0、1、2、3 喵。")


def _input_note() -> str:
    raw = input("备注（可留空）喵：").strip()
    if _is_quit_command(raw):
        raise RecordingSessionAbort
    return raw


def _segment_preview_text(segment: dict[str, Any]) -> str:
    note_text = segment["note"] if segment["note"] else "（空）"
    feeling_label = describe_feeling(segment["feeling"])
    return (
        f"类别：{segment['category']}\n"
        f"时长：{segment['duration_min']} 分钟\n"
        f"feeling：{segment['feeling']}（{feeling_label}）\n"
        f"备注：{note_text}"
    )


def _input_segment_action() -> str:
    while True:
        raw = input("输入 c=确认保存，r=重填本段，x=放弃本段，q=结束本次录入喵：").strip().lower()
        if _is_quit_command(raw):
            raise RecordingSessionAbort
        if raw in {"c", "r", "x"}:
            return raw
        print("请输入 c、r、x 或 q 喵。")


def _input_continue_after_save() -> str:
    while True:
        raw = input("是否继续录入下一条喵？(y/n，q 也会进入退出确认)：").strip().lower()
        if raw == "y":
            return "continue"
        if raw == "n" or _is_quit_command(raw):
            return "exit"
        print("请输入 y、n 或 q 喵。")


def _collect_one_segment(session_id: str, index: int) -> tuple[str, dict[str, Any] | None]:
    print(f"\n正在录入第 {index} 个时间段喵。")

    while True:
        duration_min = _input_duration()
        category = _input_category()
        feeling = _input_feeling()
        note = _input_note()

        segment = build_draft_segment(
            category=category,
            duration_min=duration_min,
            feeling=feeling,
            note=note,
            session_id=session_id,
        )

        print("\n本段摘要：")
        print(_segment_preview_text(segment))

        action = _input_segment_action()
        if action == "c":
            return "saved", segment
        if action == "x":
            print("这段就先放掉，不会保存喵，直接去下一段。")
            return "skipped", None

        print("好喵，这一段重新填。")


def _persist_draft(
    date_str: str,
    segments: list[dict[str, Any]],
    session_id: str,
    draft_path: Path | None,
) -> Path | None:
    try:
        return save_draft(
            date_str,
            segments,
            session_id,
            existing_path=draft_path,
        )
    except OSError as exc:
        print(f"草稿写入失败喵：{exc}")
        print("这次会话还留在内存里，但为了安全，建议先别继续折腾，尽快重新启动再确认一下。")
        return draft_path


def _show_draft_list(drafts: list[dict[str, Any]]) -> None:
    print("\n检测到未完成草稿喵，先处理一下更稳当：")
    for index, draft in enumerate(drafts, start=1):
        print(
            f"{index}. 日期：{draft['date']} | 已确认 {draft['segment_count']} 段 | "
            f"累计 {draft['total_min']} 分钟 | 最近更新：{draft['updated_at']}"
        )
    print("输入编号可以管理对应草稿；输入 a 可以清空全部草稿后结束；输入 q 返回主菜单。")


def _print_draft_detail(draft: dict[str, Any]) -> None:
    total_min = sum(item["duration_min"] for item in draft["segments"])
    print(f"\n草稿摘要：{draft['date']}")
    print(f"- 已确认段数：{len(draft['segments'])}")
    print(f"- 累计分钟数：{total_min}")
    print(f"- 最近更新时间：{draft.get('updated_at', '') or '（未知）'}")
    if not draft["segments"]:
        print("- 这份草稿里还没有已确认时间段喵。")
        return

    print("- 已确认时间段：")
    for index, segment in enumerate(draft["segments"], start=1):
        note_text = segment["note"] if segment["note"] else "（空）"
        feeling_label = describe_feeling(segment["feeling"])
        print(
            f"  {index}. {segment['category']} | {segment['duration_min']} 分钟 | "
            f"feeling={segment['feeling']}（{feeling_label}） | 备注：{note_text}"
        )


def _handle_single_draft_menu(summary: dict[str, Any]) -> dict[str, Any]:
    while True:
        draft = load_draft(path=summary["path"])
        if draft is None:
            print("这份草稿刚刚已经找不到了喵，回草稿列表再看一下。")
            return {"action": "back_to_list"}

        total_min = sum(item["duration_min"] for item in draft["segments"])
        print(f"\n===== 草稿处理：{draft['date']} =====")
        print(f"- 已确认段数：{len(draft['segments'])}")
        print(f"- 累计分钟数：{total_min}")
        print(f"- 最近更新时间：{draft.get('updated_at', '') or '（未知）'}")
        print("1. 查看摘要")
        print("2. 恢复继续")
        print("3. 写入继续")
        print("4. 无视继续")
        print("5. 丢弃继续")
        print("6. 丢弃结束")
        print("7. 清空结束")
        print("0. 返回草稿列表")
        print("q. 返回主菜单")

        raw = input("请选择草稿动作喵：").strip().lower()
        if raw == "1":
            _print_draft_detail(draft)
            continue
        if raw == "2":
            print(f"{draft['date']} 的草稿已经恢复好啦，可以继续往下录。")
            return {
                "action": "start",
                "date_str": draft["date"],
                "segments": list(draft["segments"]),
                "session_id": draft.get("session_id", "").strip() or _make_session_id(draft["date"]),
                "draft_path": draft["path"],
            }
        if raw == "3":
            if not draft["segments"]:
                print("这份草稿还没有已确认时间段，所以先没法正式写入 data 喵。")
                continue

            write_result = commit_confirmed_segments(
                date_str=draft["date"],
                segments=list(draft["segments"]),
                session_id=draft.get("session_id", "").strip() or _make_session_id(draft["date"]),
                draft_paths=[draft["path"]],
            )
            print_session_write_result(
                write_result,
                intro="草稿已经正式写进 data，并基于 data 重建好当日 output 啦喵。",
            )
            print("接下来会继续同一天的新录入，这时会从空白新会话开始。")
            return _fresh_session(draft["date"])
        if raw == "4":
            print("这份草稿先不碰，原样保留；这次直接开始新的今日录入喵。")
            return _fresh_session()
        if raw == "5":
            delete_draft(path=draft["path"])
            print("已丢弃这份草稿，接下来直接开始新的今日录入喵。")
            return _fresh_session()
        if raw == "6":
            delete_draft(path=draft["path"])
            print("这份草稿已经丢弃，本次流程也到这里结束喵。")
            return {"action": "end"}
        if raw == "7":
            removed = delete_all_drafts()
            print(f"全部草稿都清空啦，共清掉 {len(removed)} 份，本次流程结束喵。")
            return {"action": "end"}
        if raw == "0":
            return {"action": "back_to_list"}
        if _is_quit_command(raw):
            print("先回主菜单喵，这次不强行进入录入流程。")
            return {"action": "back"}
        print("请输入 1、2、3、4、5、6、7、0 或 q 喵。")


def _resolve_startup_flow() -> dict[str, Any]:
    while True:
        drafts = list_draft_summaries()
        if not drafts:
            return _fresh_session()

        _show_draft_list(drafts)
        raw = input("请选择要处理的草稿编号喵：").strip().lower()
        if _is_quit_command(raw):
            print("这次先不进录入啦，回主菜单等你。")
            return {"action": "back"}
        if raw == "a":
            removed = delete_all_drafts()
            print(f"全部草稿都清空啦，共清掉 {len(removed)} 份，本次流程结束喵。")
            return {"action": "end"}
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(drafts):
                resolution = _handle_single_draft_menu(drafts[index - 1])
                if resolution["action"] == "back_to_list":
                    continue
                return resolution
        print("请输入有效的草稿编号，或者输入 a / q 喵。")


def _print_loaded_session_summary(date_str: str, segments: list[dict[str, Any]]) -> None:
    total_min = sum(item["duration_min"] for item in segments)
    print(
        f"\n已载入 {date_str} 的草稿内容："
        f"{len(segments)} 段已确认记录，累计 {total_min} 分钟。"
    )
    print("如果你现在只想正式提交，不想再录新段，也可以直接在下一步输入 q 进入退出确认。")


def _print_exit_overview(date_str: str, segments: list[dict[str, Any]]) -> None:
    total_min = sum(item["duration_min"] for item in segments)
    category_counter = Counter()
    for item in segments:
        category_counter[item["category"]] += item["duration_min"]

    print("\n----- 本次录入会话摘要 -----")
    print(f"日期：{date_str}")
    print(f"已确认时间段数：{len(segments)}")
    print(f"累计分钟数：{total_min}")
    print("类别分布（分钟）：")
    for category, minutes in category_counter.most_common():
        print(f"  - {category}: {minutes}")

    if total_min < 1200:
        print("提醒喵：今天累计分钟数明显还不到 1440，可能还有没记上的时间。")
    if total_min > 1440:
        print("提醒喵：今天累计分钟数已经超过 1440，请顺手确认一下有没有重复录入。")


def _prompt_exit_menu(
    *,
    date_str: str,
    confirmed_segments: list[dict[str, Any]],
    session_id: str,
    draft_path: Path | None,
) -> DailyInputResult | None:
    _print_exit_overview(date_str, confirmed_segments)

    while True:
        print("\n===== 结束本次录入会话 =====")
        print("1. 写入 data 并正常退出")
        print("2. 取消退出，继续录入")
        raw = input("请选择退出方式喵：").strip().lower()

        if raw == "1":
            confirmed = prompt_yes_no("再确认一次：现在就正式写入 data 并结束本次录入喵？(y/n)：")
            if not confirmed:
                print("好喵，这次退出不生效，我们继续录。")
                return None

            draft_paths = [draft_path] if draft_path is not None else []
            write_result = commit_confirmed_segments(
                date_str=date_str,
                segments=list(confirmed_segments),
                session_id=session_id,
                draft_paths=draft_paths,
            )
            print_session_write_result(
                write_result,
                intro="这次录入已经正式写进 data，并把当日 output 重建好啦喵。",
            )
            return DailyInputResult(
                flow_status="saved",
                date_str=date_str,
                session_id=session_id,
            )

        if raw == "2":
            print("退出动作已经取消，继续录下一段就好喵。")
            return None

        print("请输入 1 或 2 喵。")


def _handle_normal_session_end(
    *,
    date_str: str,
    confirmed_segments: list[dict[str, Any]],
    session_id: str,
    draft_path: Path | None,
) -> DailyInputResult | None:
    if not confirmed_segments:
        print("\n这次还没有任何已确认时间段，就先轻轻回主菜单啦，不会制造空草稿喵。")
        return DailyInputResult(
            flow_status="cancelled",
            date_str=date_str,
            session_id=session_id,
        )

    print("\n收到结束本次录入的指令喵，先走正式退出分流。")
    return _prompt_exit_menu(
        date_str=date_str,
        confirmed_segments=confirmed_segments,
        session_id=session_id,
        draft_path=draft_path,
    )


def _handle_abnormal_session_end(
    *,
    date_str: str,
    confirmed_segments: list[dict[str, Any]],
    session_id: str,
    draft_path: Path | None,
) -> DailyInputResult:
    print("\n收到 Ctrl+C 了喵，这次按异常中断处理。")

    if confirmed_segments:
        persisted_path = _persist_draft(
            date_str=date_str,
            segments=confirmed_segments,
            session_id=session_id,
            draft_path=draft_path,
        )
        if persisted_path is not None:
            print("已确认时间段已经安全写进草稿啦，下次启动还能继续恢复。")
        else:
            print("草稿这次没能顺利写进去，建议优先检查磁盘或权限喵。")
    else:
        print("这次还没有已确认时间段，所以不会额外生成空草稿喵。")

    print("程序会在这里结束，不会自动正式写入 data。")
    return DailyInputResult(
        flow_status="aborted",
        date_str=date_str,
        session_id=session_id,
        exit_program=True,
    )


def collect_daily_input() -> DailyInputResult:
    startup = _resolve_startup_flow()
    if startup["action"] == "back":
        return DailyInputResult(flow_status="cancelled")
    if startup["action"] == "end":
        return DailyInputResult(flow_status="cancelled")

    date_str = startup["date_str"]
    confirmed_segments = list(startup["segments"])
    active_session_id = startup["session_id"]
    active_draft_path = startup["draft_path"]

    print(f"\n本次录入目标日期：{date_str}")
    if confirmed_segments:
        _print_loaded_session_summary(date_str, confirmed_segments)

    while True:
        try:
            status, segment = _collect_one_segment(active_session_id, len(confirmed_segments) + 1)

            if status == "saved" and segment is not None:
                confirmed_segments.append(segment)
                active_draft_path = _persist_draft(
                    date_str=date_str,
                    segments=confirmed_segments,
                    session_id=active_session_id,
                    draft_path=active_draft_path,
                )
                print("这一段已经确认，并且立刻安全写进草稿啦喵。")

                if _input_continue_after_save() == "continue":
                    continue

                exit_result = _prompt_exit_menu(
                    date_str=date_str,
                    confirmed_segments=confirmed_segments,
                    session_id=active_session_id,
                    draft_path=active_draft_path,
                )
                if exit_result is None:
                    continue
                return exit_result

            if status == "skipped":
                continue

        except RecordingSessionAbort:
            exit_result = _handle_normal_session_end(
                date_str=date_str,
                confirmed_segments=confirmed_segments,
                session_id=active_session_id,
                draft_path=active_draft_path,
            )
            if exit_result is None:
                continue
            return exit_result

        except KeyboardInterrupt:
            return _handle_abnormal_session_end(
                date_str=date_str,
                confirmed_segments=confirmed_segments,
                session_id=active_session_id,
                draft_path=active_draft_path,
            )
