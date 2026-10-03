# Project Purpose

Yan Shikan Tracker is a small local Python CLI for time recording and review. Keep changes recoverable and testable. Avoid web services, database migrations, and unnecessary tooling.

# Architecture and Primary Files

Root `main.py` is a thin launcher. Implementation lives in `yan_shikan_tracker/`: `main.py` orchestrates the menu, `input_cli.py` handles interaction, `draft_io.py` handles recovery, `session_flow.py` commits, and `excel_io.py` stores Excel. Category/scoring rules live in `category_registry.py`, `config.py`, and `scorer.py`. Reports and charts use `reporter.py`, `plotter.py`, and `output_manager.py`.

Source Excel is authoritative; output is rebuildable. Preserve repository-level default storage and `YAN_SHIKAN_DATA_ROOT` overrides.

# Run and Test

- Install runtime dependencies: `python -m pip install -r requirements.txt`.
- Launch: `python main.py`.
- Install test dependencies: `python -m pip install -r requirements-dev.txt`.
- Test: `python -m pytest -q`.
- Compile: `python -m compileall -q main.py yan_shikan_tracker tests`.
- For demos or manual tests, set `YAN_SHIKAN_DATA_ROOT` to a fresh temporary directory; follow `docs/testing/MANUAL_SMOKE_TEST.md`.

# Data Safety

`data/`, `output/`, and `.local/` are protected private directories. Never publish, stage, or copy their contents into examples, tests, or documentation. Automated tests must use synthetic data and temporary directories. Production write changes must prove that failed commits preserve recoverable source Excel and drafts. Verify private-data hashes before and after authorized work.

# Coding Rules

Follow existing Python style and package-relative imports. Prefer focused changes; preserve same-day append, category compatibility, and output rebuilding. Sanitize read errors to relative paths and error types; do not include personal notes. Chinese application UI may remain Chinese.

# Git Rules

Stage only explicitly reviewed public files. Check `git diff --cached` and ignore rules before committing. Configure remotes, push, and publish only with explicit user authorization and after any required human gate. Use `main` and short feature branches only when useful.

Run relevant tests before commits.

# Documentation Rules

Maintain public documentation in English. README describes current usage; CHANGELOG records completed changes; ROADMAP contains future ideas. Keep historical local logs archived and ignored; do not create new dated engineering logs or duplicate existing documentation.

Update CHANGELOG for user-visible changes. Update ROADMAP only for genuine unfinished ideas.

# Definition of Done

Relevant tests pass; protected data hashes remain unchanged; public candidates contain no private files or high-risk content. Interaction changes require a focused human smoke test. Do not claim remote CI or manual validation passed before it actually does.
