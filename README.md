# Yan Shikan Tracker / 研时记

研时记是本地 Python 命令行工具，用于逐段记录时间，并生成每日评分、文字复盘和趋势图。原始记录由使用者保存在本机。

## Features

- 按日期录入时长、类别、状态评分和备注；每段确认后保存可恢复草稿。
- 同一天可多次追加。类别旧名会在读取和计算时归一。
- 生成每日汇总 Excel、文字报告、LLM 提示词和 7/30/90 天及全历史趋势图。
- 可按日、日期范围或全历史重建派生输出。
- 原始每日 Excel 经临时文件验证后替换；覆盖前在本地保留一份前版本。

## Architecture

`main.py` 是 CLI 入口。`input_cli.py` 和 `draft_io.py` 负责交互与草稿，`session_flow.py` 串联正式提交，`excel_io.py` 保存和读取原始 Excel。`category_registry.py`、`config.py`、`scorer.py` 定义类别与评分；`reporter.py`、`plotter.py`、`output_manager.py` 生成派生结果。没有 Web 前端或数据库。

## Requirements and installation

使用 Python 3.11 或更高版本。建议在独立虚拟环境中安装直接依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

若使用已有 conda 环境，先激活环境，再运行 `python -m pip install -r requirements.txt`。依赖清单记录兼容范围，没有冻结整个个人环境。

## Usage

```powershell
python main.py
```

主菜单提供录入、输出管理和退出。录入时依次输入日期、时长、类别、feeling（0–3）和备注；可确认、重填、放弃或结束当前会话。确认段落先进入草稿；正式提交后写入原始 Excel，再重建该日输出。若输出重建失败，原始记录仍保留，程序会提示从输出管理重新生成。

首次启动会生成本地 `data/category_config.csv`。可在关闭程序后编辑目标时长和权重；已有配置不会在启动时被自动改写。

## Data model and safety

- `data/YYYY.MM/YYYY-MM-DD/时间记录_YYYY-MM-DD.xlsx`：唯一事实来源，列包含日期、类别、时长、feeling、备注、会话 ID、写入时间。
- `data/drafts/`：未正式提交的 JSON 草稿。
- `data/data_backup/YYYY.MM/YYYY-MM-DD/`：同日追加前的上一版原始工作簿，每日只保留一份。
- `output/`：从原始记录生成的汇总 Excel、TXT 和图像；可重建，不能代替原始数据备份。

**`data/` 与 `output/` 永远是本地私人目录，不纳入公开 Git。** 请另行备份 `data/`；不要把真实记录、备注、草稿或派生统计复制到 issue、测试夹具或演示数据中。

## Synthetic sample data

`sample_data/` 提供三个完全虚构的 2030 年日期工作簿和示例类别配置，用于查看格式与回归测试。它不取自真实记录。`python -m pytest` 会把样例复制到临时目录，不会写入真实 `data/`。

需要手动体验 CLI 时，先设置一个**新的临时根目录**，再启动程序：

```powershell
$env:YAN_SHIKAN_DATA_ROOT = Join-Path $env:TEMP 'yan-shikan-demo'
python main.py
Remove-Item Env:YAN_SHIKAN_DATA_ROOT
```

设置变量后，程序只在指定根目录下创建 `data/`、`output/`；不读取项目原有私人记录。手动体验请使用明显虚构日期，结束后自行确认临时目录内容。不要把临时根目录指向真实项目。

## Testing

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

测试覆盖评分、旧类别兼容、草稿恢复、同日追加、原子写入失败、输出重建失败、坏文件报错和虚构数据生成链。测试存储路径重定向到 pytest 临时目录。

## Project status and license

当前处于本地发布准备阶段，最后一个已记录的功能版本是 v0.5.3。公开发布前还需人工 CLI smoke test 和许可决定。**目前未添加 LICENSE；未获作者许可时，不应假定代码可再分发或修改。**
