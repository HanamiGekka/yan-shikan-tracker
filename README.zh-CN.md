[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md)

# 研时记 · Yan Shikan Tracker

本地 Python 命令行时间记录工具，用于整理时间片段、每日复盘和长期趋势。确认的记录先保存到 Excel，再生成可重建的汇总与图表。

当前发行：[v0.6.0](https://github.com/HanamiGekka/yan-shikan-tracker/releases/tag/v0.6.0)。

**程序交互和 Excel 字段目前以中文为主。四语言 README 是文档翻译，不代表程序已经提供英语或日语界面。** 项目没有 Web 服务、数据库、正式 Windows EXE 或 PyPI 发布包。

## 主要功能

- 记录日期、时长、分类、感受评分（0–3）和可选备注；同一天可追加多次会话。
- 已确认的片段保存为可恢复 JSON 草稿，正式提交后写入当天的 Excel。
- 兼容历史分类别名，不改写已有记录。
- 生成每日汇总工作簿、文字复盘、供自行审阅的 LLM 提示文本，以及 7／30／90 天和全历史图表。
- 按日期、日期范围或全部记录重建输出。
- 写入前验证临时工作簿，再原子替换每日源文件；追加前保留一份上一版本。

## 安装与启动

需要 **Python 3.11 或更高版本**。在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

也可复用兼容的 conda 环境。依赖范围描述可支持的环境，不绑定某台电脑的完整环境。

在菜单中选择记录、输出管理或退出。记录时依次填写日期、分钟数、分类、感受和备注，确认每个片段后再提交会话。**确认片段仍是草稿，提交才生成正式记录。** 原始记录提交成功会先清除对应草稿，再重建输出；若输出失败，已保存的 Excel 记录仍保留，可通过输出管理重建。

首次启动创建 `data/category_config.csv`。关闭程序后可修改其中的目标时长和权重；分类名称和核心分类归属由源码定义。启动时仅在内存中规范化已有配置，不自动改写配置文件。

## 数据与隐私

默认存储相对于仓库根目录，不随终端当前目录变化：

| 位置 | 内容 |
| --- | --- |
| `data/YYYY.MM/YYYY-MM-DD/` | 每日源 Excel：日期、分类、时长、感受、备注、会话 ID 与创建时间 |
| `data/drafts/` | 可恢复 JSON 草稿 |
| `data/data_backup/YYYY.MM/YYYY-MM-DD/` | 追加前的一份上一版每日工作簿 |
| `output/` | 从源记录重建的工作簿、文字与图表 |

**`data/`、`output/` 和 `.local/` 受保护，不纳入公开 Git 仓库。** 请另行备份 `data/`；单份上一版本不是完整备份。不要把真实备注、草稿或统计复制到示例、测试、Issue 或项目文档。LLM 提示文本只保存在本地，发给外部服务前须自行检查隐私内容。

演示时使用独立的新目录：

```powershell
$demoRoot = Join-Path $env:TEMP ('yan-shikan-demo-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$env:YAN_SHIKAN_DATA_ROOT = $demoRoot
python main.py
Remove-Item Env:YAN_SHIKAN_DATA_ROOT
```

该进程生成的所有文件应位于 `$demoRoot`，不要把此变量指向真实记录目录进行试验。最后一行只移除环境变量，不删除文件。

## 合成示例

`sample_data/` 提供三份虚构的 2030 年工作簿和分类配置示例。备注为英文，中文字段与分类别名沿用程序实际格式。测试会把示例复制到临时目录；不要与真实 `data/` 混用。

## 测试

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q main.py yan_shikan_tracker tests
python scripts/check_readmes.py
```

现有测试覆盖评分、分类兼容、草稿恢复、EOF 中断、同日追加、写入和输出失败、异常工作簿、配置保留、合成示例输出及存储根目录解析。[命令行手工检查](docs/testing/MANUAL_SMOKE_TEST.md)说明交互验收；CI 在 Ubuntu／Python 3.11 上运行，并检查 README 导航与本地链接。本轮翻译未改变生产行为。

## 代码结构与维护

根目录 `main.py` 仅负责启动，实现在 `yan_shikan_tracker/`。输入、草稿、提交和 Excel 存储分工明确；分类与评分集中定义，报告和图表从源 Excel 重建。完整公开范围见[公开文件说明](docs/release/PUBLIC_GIT_MANIFEST.md)。

v0.6.0 以数据完整性、可恢复记录和小型可测试结构为重点。项目处于维护状态，后续变更由缺陷、实际需要或明确需求驱动。[CHANGELOG](CHANGELOG.md)记录已完成变更，[ROADMAP](ROADMAP.md)只列未来想法。

## 许可证

采用 [MIT 许可证](LICENSE)。
