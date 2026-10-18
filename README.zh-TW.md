[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md)

# 研時記 · Yan Shikan Tracker

本機 Python 命令列時間記錄工具，用來整理時間區段、每日回顧與長期趨勢。確認後的記錄先儲存至 Excel，再產生可重建的摘要與圖表。

目前發行：[v0.6.0](https://github.com/HanamiGekka/yan-shikan-tracker/releases/tag/v0.6.0)。

**程式互動與 Excel 欄位目前以中文為主。四種語言的 README 屬於文件翻譯，不代表程式已提供英文或日文介面。** 本專案沒有 Web 服務、資料庫、正式 Windows EXE 或 PyPI 發行套件。

## 主要功能

- 記錄日期、時間長度、分類、感受評分（0–3）與選填備註；同一天可追加多次工作階段。
- 已確認的區段儲存為可復原的 JSON 草稿，正式提交後才寫入當天的 Excel。
- 支援歷史分類別名，不改寫既有記錄。
- 產生每日彙總活頁簿、文字回顧、供自行檢閱的 LLM 提示文字，以及 7／30／90 天與完整歷史圖表。
- 按日期、日期範圍或所有記錄重建輸出。
- 先驗證暫存活頁簿，再以不可分割的檔案操作取代每日來源檔；追加前保留一份上一版本。

## 安裝與啟動

需要 **Python 3.11 或更新版本**。在儲存庫根目錄執行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

也可使用相容的 conda 環境。相依套件範圍描述支援環境，不綁定某台電腦的完整設定。

在選單選擇記錄、輸出管理或離開。依序輸入日期、分鐘數、分類、感受與備註，逐段確認後再提交工作階段。**確認區段後仍屬草稿，提交才產生正式記錄。** 原始記錄儲存成功後會先清除對應草稿，再重建輸出；若輸出失敗，已儲存的 Excel 仍保留，可透過輸出管理重建。

首次啟動會建立 `data/category_config.csv`。關閉程式後可修改目標時間與權重；分類名稱與核心分類歸屬由原始碼定義。啟動時只在記憶體中正規化既有設定，不自動改寫設定檔。

## 資料與隱私

預設儲存位置以儲存庫根目錄為準，不隨終端機的目前目錄改變：

| 位置 | 內容 |
| --- | --- |
| `data/YYYY.MM/YYYY-MM-DD/` | 每日來源 Excel：日期、分類、時間長度、感受、備註、工作階段 ID 與建立時間 |
| `data/drafts/` | 可復原的 JSON 草稿 |
| `data/data_backup/YYYY.MM/YYYY-MM-DD/` | 追加前的一份上一版每日活頁簿 |
| `output/` | 從來源記錄重建的活頁簿、文字與圖表 |

**`data/`、`output/` 與 `.local/` 為受保護目錄，不納入公開 Git 儲存庫。** 請另外備份 `data/`；單份上一版本不足以取代完整備份。不要把真實備註、草稿或統計複製到範例、測試、Issue 或專案文件。LLM 提示文字僅儲存在本機，傳送至外部服務前請先檢查隱私內容。

示範時請使用獨立的新目錄：

```powershell
$demoRoot = Join-Path $env:TEMP ('yan-shikan-demo-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$env:YAN_SHIKAN_DATA_ROOT = $demoRoot
python main.py
Remove-Item Env:YAN_SHIKAN_DATA_ROOT
```

此程序產生的檔案應全部位於 `$demoRoot`，不要指定真實記錄目錄進行試驗。最後一行只移除環境變數，不刪除檔案。

## 合成範例

`sample_data/` 提供三份虛構的 2030 年活頁簿與分類 CSV 範例。備註為英文，中文欄位與分類別名沿用程式的既有格式。測試會將範例複製到暫存目錄；請勿與真實 `data/` 混用。

## 測試

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q main.py yan_shikan_tracker tests
python scripts/check_readmes.py
```

既有測試涵蓋評分、分類相容、草稿復原、EOF 中斷、同日追加、寫入與輸出失敗、異常活頁簿、設定保留、合成範例輸出及儲存根目錄解析。[命令列手動檢查](docs/testing/MANUAL_SMOKE_TEST.md)說明互動驗收；CI 使用 Ubuntu／Python 3.11，並檢查 README 導覽與本機連結。本次翻譯沒有改變程式行為。

## 程式結構與維護

根目錄 `main.py` 僅負責啟動，實作位於 `yan_shikan_tracker/`。輸入、草稿、提交與 Excel 儲存各司其職；分類與評分集中定義，報告和圖表由來源 Excel 重建。公開範圍見[公開檔案說明](docs/release/PUBLIC_GIT_MANIFEST.md)。

v0.6.0 著重資料完整性、可復原記錄與小型可測試結構。專案目前處於維護階段，後續變更由缺陷、實際需求或明確委託驅動。[CHANGELOG](CHANGELOG.md)記錄已完成變更，[ROADMAP](ROADMAP.md)僅列未來構想。

## 授權條款

採用 [MIT 授權](LICENSE)。
