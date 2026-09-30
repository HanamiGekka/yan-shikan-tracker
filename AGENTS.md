# Project Purpose

研时记是本地 Python CLI 时间记录与复盘工具。保持小型、可恢复、可测试；不引入 Web、数据库或大规模目录重构。

# Architecture

原始 Excel 是事实来源，`output/` 是可重建结果。草稿用于中断恢复。保持现有根目录模块结构。

# Main Files

`main.py` 入口；`input_cli.py` 交互；`draft_io.py` 草稿；`session_flow.py` 提交；`excel_io.py` 存储；`category_registry.py`/`config.py`/`scorer.py` 规则；`reporter.py`/`plotter.py`/`output_manager.py` 派生输出。

# Run Command

`python -m pip install -r requirements.txt`，然后 `python main.py`。演示或人工测试先设置 `YAN_SHIKAN_DATA_ROOT` 为独立临时目录。

# Test Command

`python -m pip install -r requirements-dev.txt`，然后 `python -m pytest -q tests`。

# Data Safety Rules

`data/`、`output/` 永远是私人目录。不得将真实内容复制到 `sample_data/`、`tests/`、文档或 Git。自动测试只能用虚构数据和临时目录；任何生产写入改动须证明失败后原始 Excel 与草稿仍可恢复。

# Coding Rules

沿用现有 Python 风格和类别兼容层。优先小范围变更；保留同日追加、旧类别读取和可重建输出。异常信息只含相对文件路径与错误类型，不输出个人备注。

# Git Rules

只暂存明确审阅过的公开文件。提交前检查 `git diff --cached` 与忽略规则。未经用户明确授权，不配置 remote、不 push、不公开发布。

# Documentation Rules

README 说明当前运行方式；CHANGELOG 记录已发生的版本变化；ROADMAP 记录计划。历史 `engineering_log/` 留在本机，不再新增日期型日志。

# Definition of Done

相关自动测试通过；真实 `data/`、`output/` 哈希不变；Git 候选无私人文件或高风险内容；交互变更附一次集中的人工 smoke test。
