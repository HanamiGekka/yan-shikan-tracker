# Yan Shikan Tracker

A local Python CLI for time tracking, daily review, and productivity trends.

## Overview

Record time segments, review daily scores, and rebuild reports from local Excel records. The CLI and workbook labels currently use Chinese. There is no web service or database.

## Features

- Record date, duration, category, feeling (0-3), and an optional note.
- Save confirmed segments to recoverable JSON drafts and append multiple sessions to the same day.
- Read historical category aliases without changing stored records.
- Generate daily summary workbooks, text reviews, LLM prompts, and 7/30/90-day and full-history charts.
- Rebuild outputs for a date, date range, or all recorded dates.
- Validate a temporary daily workbook before atomic replacement, retaining one previous version per date.

## How It Works

The root `main.py` launches `yan_shikan_tracker.main`. Input and drafts flow through `input_cli.py`, `draft_io.py`, and `session_flow.py`; `excel_io.py` stores the source records. `category_registry.py`, `config.py`, and `scorer.py` define category and scoring rules. `reporter.py`, `plotter.py`, and `output_manager.py` create rebuildable outputs.

A successful raw commit clears its draft before rebuilding output. If output generation fails, the raw record remains saved; use Output Management to rebuild that date.

## Installation

Use Python 3.11 or later. From the repository root, create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

An existing conda environment also works. Dependency ranges describe supported local environments rather than freezing a personal environment.

## Usage

```powershell
python main.py
```

Choose Record, Output Management, or Exit. Record a date, duration in minutes, category, feeling, and note; confirm each segment, then submit the session. Confirmed segments remain drafts until submission.

The first launch creates `data/category_config.csv`. With the app closed, edit target durations and weights there. Existing configuration is normalized in memory and is not rewritten on startup. Category names and core-category membership remain defined in the source.

## Data Storage and Privacy

Default storage stays at the repository root, regardless of the terminal's current directory:

- `data/YYYY.MM/YYYY-MM-DD/`: daily source Excel with date, category, duration, feeling, note, session ID, and creation time.
- `data/drafts/`: recoverable JSON drafts.
- `data/data_backup/YYYY.MM/YYYY-MM-DD/`: one previous daily workbook before an append.
- `output/`: generated workbooks, text, and charts, all rebuildable from source records.

**`data/` and `output/` contain local user data and are intentionally not tracked by Git.** Back up `data/` separately: a single previous version is not a complete backup strategy. Never copy real notes, drafts, or statistics into tests, examples, issues, or repository documentation. Generated LLM prompts are local text files; review privacy before sharing them with any external service.

For a safe demo, use a new temporary storage root:

```powershell
$demoRoot = Join-Path $env:TEMP ('yan-shikan-demo-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$env:YAN_SHIKAN_DATA_ROOT = $demoRoot
python main.py
Remove-Item Env:YAN_SHIKAN_DATA_ROOT
```

All generated files must be inside `$demoRoot`. Do not point this variable at your real records when experimenting.

## Sample Data

`sample_data/` contains three fictional 2030 workbooks and an example category CSV. Notes are English; Chinese schema labels and category aliases match the app's existing format. Never mix demo records with real `data/`. Automated tests copy samples to temporary directories.

## Testing

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q main.py yan_shikan_tracker tests
```

Tests cover scoring, category compatibility, draft recovery, same-day append, write failures, output failures, malformed workbooks, configuration preservation, sample output generation, and storage-root resolution. Manual CLI validation is in [the smoke test](docs/testing/MANUAL_SMOKE_TEST.md). CI uses Python 3.11 on Ubuntu.

## Repository Structure

```text
yan-shikan-tracker/
|-- yan_shikan_tracker/
|-- tests/
|-- sample_data/
|-- docs/testing/
|-- docs/release/
|-- .github/workflows/
|-- main.py
|-- requirements.txt
|-- requirements-dev.txt
|-- README.md
|-- AGENTS.md
|-- CHANGELOG.md
|-- ROADMAP.md
|-- LICENSE
```

Local data, generated output, and local archives are excluded from this public tree. See [the public manifest](docs/release/PUBLIC_GIT_MANIFEST.md).

## Project Status

The v0.6.0 candidate focuses on data integrity and repository cleanup. Public publication remains gated on the manual CLI smoke test and remote CI. No EXE, web deployment, or PyPI package is planned for this release. Future ideas are in [ROADMAP.md](ROADMAP.md).

## License

MIT; see [LICENSE](LICENSE).
