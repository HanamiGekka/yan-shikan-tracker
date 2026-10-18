[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [繁體中文](README.zh-TW.md)

# Yan Shikan Tracker · 時間記録と日々の振り返り

時間の使い方を記録し、日々の振り返りと長期的な傾向の確認を行う、ローカルの Python CLI ツールです。確定した記録は Excel に保存し、そこから集計やグラフを再生成します。

現在のリリース：[v0.6.0](https://github.com/HanamiGekka/yan-shikan-tracker/releases/tag/v0.6.0)。

**プログラムの対話表示と Excel の項目名は、現在も主に中国語です。4 言語の README は文書の翻訳であり、英語・日本語のアプリ UI を提供するものではありません。** Web サービス、データベース、正式な Windows EXE、PyPI パッケージはありません。

## 主な機能

- 日付、所要時間、分類、気分の評価（0–3）、任意のメモを記録。同じ日に複数回追記できます。
- 確認済みの区間を復元可能な JSON の下書きに保存し、セッションを確定すると当日の Excel に反映します。
- 過去の分類名の別表記を読み取り、既存の記録は書き換えません。
- 日次集計の Excel、振り返りの文章、確認用の LLM プロンプト、7／30／90 日間と全期間のグラフを生成します。
- 指定日、期間、全記録を対象に出力を再生成できます。
- 一時的な日次ワークブックを検証してから原子的に置き換え、追記前の版を 1 つ保持します。

## インストールと起動

**Python 3.11 以降**が必要です。リポジトリのルートで実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

互換性のある conda 環境も使用できます。依存関係の範囲は対応環境を表し、特定の PC の構成を固定するものではありません。

メニューから記録、出力管理、終了を選びます。日付、分単位の時間、分類、気分、メモを入力し、区間ごとに確認して最後にセッションを確定します。**区間を確認しただけでは下書きのままで、セッションの確定時に正式な記録になります。** 元の記録を保存できたら下書きを消し、その後に出力を再生成します。出力に失敗しても保存済み Excel は残るので、出力管理からやり直せます。

初回起動時に `data/category_config.csv` を作成します。アプリを閉じてから目標時間と重みを編集できます。分類名と主要分類への所属はソースで定義します。既存の設定は起動時にメモリ上で正規化し、自動で書き換えません。

## 保存先とプライバシー

既定の保存先はリポジトリのルート基準で、ターミナルの作業ディレクトリには依存しません。

| 場所 | 内容 |
| --- | --- |
| `data/YYYY.MM/YYYY-MM-DD/` | 日付、分類、時間、気分、メモ、セッション ID、作成時刻を含む日次の元 Excel |
| `data/drafts/` | 復元可能な JSON 下書き |
| `data/data_backup/YYYY.MM/YYYY-MM-DD/` | 追記前のワークブック 1 版 |
| `output/` | 元の記録から再生成できる Excel、文章、グラフ |

**`data/`、`output/`、`.local/` は保護対象で、公開 Git 履歴には含めません。** `data/` は別途バックアップしてください。直前の 1 版だけでは十分なバックアップになりません。実際のメモ、下書き、統計をサンプル、テスト、Issue、文書へコピーしないでください。LLM プロンプトはローカルの文章ファイルです。外部サービスへ渡す前に内容を確認します。

試す場合は、新しい独立した保存先を指定します。

```powershell
$demoRoot = Join-Path $env:TEMP ('yan-shikan-demo-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$env:YAN_SHIKAN_DATA_ROOT = $demoRoot
python main.py
Remove-Item Env:YAN_SHIKAN_DATA_ROOT
```

このプロセスで生成するファイルはすべて `$demoRoot` 内に保存します。実際の記録先を実験用に指定しないでください。最後の行は環境変数を解除するだけで、ファイルは削除しません。

## 架空のサンプル

`sample_data/` には架空の 2030 年のワークブック 3 つと分類 CSV があります。メモは英語ですが、項目名と分類の別表記は既存の中国語形式に合わせています。テストはサンプルを一時ディレクトリへコピーします。実際の `data/` と混ぜないでください。

## テスト

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q main.py yan_shikan_tracker tests
python scripts/check_readmes.py
```

既存テストは採点、分類互換性、下書き復元、EOF 中断、同日追記、書き込み・出力の失敗、不正なワークブック、設定の保持、サンプル出力、保存先の解決を扱います。対話操作は[手動確認手順](docs/testing/MANUAL_SMOKE_TEST.md)、CI は Ubuntu／Python 3.11 を使用します。README の導線とローカルリンクも検査します。今回の翻訳で動作は変更していません。

## 構成と保守方針

ルートの `main.py` は起動専用で、実装は `yan_shikan_tracker/` にあります。入力、下書き、セッションの確定、Excel 保存を分担し、分類と採点規則を集約しています。レポートとグラフは元 Excel から再生成します。[公開ファイルの範囲](docs/release/PUBLIC_GIT_MANIFEST.md)を参照してください。

v0.6.0 はデータの完全性、復元可能な記録、小さくテストしやすい構成を重視しています。現在は保守段階で、変更は不具合、実際の利用上の必要性、明示的な依頼に基づきます。[CHANGELOG](CHANGELOG.md)は完了済みの変更、[ROADMAP](ROADMAP.md)は今後の案を記載します。

## ライセンス

[MIT ライセンス](LICENSE)。
