from __future__ import annotations

from config import CATEGORY_CONFIG_PATH
from excel_io import ensure_project_files
from input_cli import (
    DailyInputResult,
    choose_main_menu_action,
    choose_output_management_action,
    collect_daily_input,
    prompt_date_range,
    prompt_date_value,
    prompt_yes_no,
)
from output_manager import (
    OutputRebuildResult,
    clear_all_backups,
    clear_daily_backups,
    rebuild_all_output,
    rebuild_output_for_date,
    rebuild_output_range,
    redraw_all_charts,
)
from session_flow import OutputRebuildError


def _print_chart_paths(chart_paths: dict[str, object]) -> None:
    if not chart_paths:
        print("- charts：本次没有重绘图像喵。")
        return

    print("- charts（output/charts 下最新四张图喵）：")
    for label, path in chart_paths.items():
        print(f"  {label}: {path}")


def _print_rebuild_result(title: str, result: OutputRebuildResult) -> None:
    print(f"\n{title}")
    print(f"- 已清理 output 日期数：{len(result.cleared_dates)}")
    print(f"- 已重建 output 日期数：{len(result.generated_dates)}")
    if result.skipped_dates:
        preview = "、".join(result.skipped_dates[:5])
        suffix = " ..." if len(result.skipped_dates) > 5 else ""
        print(f"- 这些日期当前没有 data，所以只清理了旧 output：{preview}{suffix}")
    _print_chart_paths(result.chart_paths)


def _handle_record_entry() -> DailyInputResult:
    return collect_daily_input()


def _handle_output_management() -> None:
    while True:
        action = choose_output_management_action()
        if action == "back":
            return

        if action == "rebuild_today":
            date_str = prompt_date_value("请输入要重建的日期喵（回车默认今天喵）：", default_today=True)
            result = rebuild_output_for_date(date_str)
            _print_rebuild_result(f"已完成 {date_str} 的 output 重建喵。", result)
            continue

        if action == "rebuild_all":
            if not prompt_yes_no("确认清理并重建全部 output 喵？这不会修改 data。(y/n)："):
                print("已取消全部 output 重建。")
                continue
            result = rebuild_all_output()
            _print_rebuild_result("已完成全历史 output 重建喵。", result)
            continue

        if action == "rebuild_range":
            start_date, end_date = prompt_date_range()
            result = rebuild_output_range(start_date, end_date)
            _print_rebuild_result(
                f"已完成 {start_date} 到 {end_date} 的 output 重建喵。",
                result,
            )
            continue

        if action == "redraw_charts":
            chart_paths = redraw_all_charts()
            print("\n图像已经按当前 data 全量重绘啦喵。")
            _print_chart_paths(chart_paths)
            continue

        if action == "clear_today_backup":
            date_str = prompt_date_value("请输入要清理 backup 的日期喵（回车默认今天喵）：", default_today=True)
            removed = clear_daily_backups(date_str)
            print(f"\n已清理 {date_str} 的 backup 目录数：{len(removed)}")
            continue

        if action == "clear_all_backup":
            if not prompt_yes_no("确认清理全部 output backup 喵？这不会修改 data。(y/n)："):
                print("已取消全部 backup 清理。")
                continue
            removed = clear_all_backups()
            print(f"\n已清理全部 backup 目录数：{len(removed)}")


def main() -> None:
    ensure_project_files()
    print("研时记（Yan-Shikan-Tracker，研究时间记录）已启动。")
    print(f"分类配置文件：{CATEGORY_CONFIG_PATH}")

    while True:
        action = choose_main_menu_action()
        if action == "exit":
            print("已退出程序喵。")
            return
        if action == "record":
            try:
                record_result = _handle_record_entry()
            except OutputRebuildError as exc:
                print(f"原始记录已保存：{exc.raw_data_path}")
                print(f"{exc.date_str} 的 output 重建失败；请在输出管理中重建该日。")
                continue
            if record_result.exit_program:
                print("异常中断流程已经处理完毕，程序现在结束喵。")
                return
            continue
        if action == "output":
            _handle_output_management()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n收到程序级 Ctrl+C，研时记先退出啦喵。")
