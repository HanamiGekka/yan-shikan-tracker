# Changelog

Known version history is retained below. Dates and changes reflect the existing version record.

## [0.6.0] - 2026-10-03

- Validate temporary daily Excel writes before atomic replacement and retain one previous workbook per date.
- Preserve recoverable drafts on raw write failure; report saved raw data when derived output fails.
- Handle ended interactive input without a traceback; retain confirmed drafts without automatic submission.
- Report source workbook read failures explicitly instead of silently omitting records.
- Create missing category configuration safely; normalize existing configuration without rewriting it.
- Keep default data storage at the repository root and support an isolated `YAN_SHIKAN_DATA_ROOT` override.
- Add fully synthetic samples, pytest regression tests, and a basic GitHub Actions CI workflow.
- Separate local archives from public files and move implementation into a simple Python package while preserving the root launcher and storage locations.
- Standardize maintained documentation in English and remove the personalized report salutation.
- Adopt the MIT license.

## [0.5.3] - 2026-04-22

- Unify project terminology and standard categories; centralize historical category aliases and feeling scoring.

## [0.5.2] - 2026-04-06

- Fix draft handling, direct submission after recovery, normal exit, and interruption flows.

## [0.5.1] - 2026-04-06

- Fix CLI session exit semantics and retain confirmed drafts after interruption.

## [0.5] - 2026-04-06

- Centralize output rebuilding by date, range, and full history, plus chart redraws; establish source data as authoritative.

## [0.4.4] - 2026-03-27

- Improve chart runtime diagnostics, daily suggestions, and summary workbook write verification.

## [0.4.3] - 2026-03-27

- Improve trend smoothing, daily category detail, and text reports.

## [0.4.2] - 2026-03-26

- Fix draft normalization for feeling=0 and improve smoothing fallbacks.

## [0.4.1] - 2026-03-26

- Fix low-feeling scoring boundaries and add multiple chart windows.

## [0.4] - 2026-03-15

- Add per-segment draft saving, recovery, and confirmation; unify chart output.

## [0.3] - 2026-03-09

- Replace same-day overwrites with cumulative appends.

## [0.2] - 2026-03-09

- Organize data and output by month and date.

## [0.1] - 2026-03-08

- Initial working CLI recording, scoring, report, and chart flow.
