# Manual CLI Smoke Test

Allow 5?10 minutes. Use only fictional data in a fresh temporary root. This procedure must not read or modify the repository's real `data/` or `output/`. The CLI remains Chinese; English explanations below identify the menu actions.

## Prepare

Open PowerShell at the repository root, with Python and runtime dependencies available. Keep the same PowerShell window for the entire test:

```powershell
$smokeRoot = Join-Path $env:TEMP ('yan-shikan-smoke-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$previousDataRoot = $env:YAN_SHIKAN_DATA_ROOT
$env:YAN_SHIKAN_DATA_ROOT = $smokeRoot
python main.py
```

Startup must display a category configuration path inside `$smokeRoot`. If it points to the real repository data directory, exit immediately and report failure. All generated files must remain inside `$smokeRoot`.

## Interaction Checks

1. Confirm the main menu has Record (`录入`), Output Management (`输出管理`), and Exit (`退出`). Choose Record (1).
2. Enter the fictional date `2030-02-20`, then 10 minutes, Exercise (`运动`, category `a`), feeling `2`, and note `Manual demo only`. Confirm the segment (`c`).
3. At the next-segment prompt, press `Ctrl+C`. Confirm that the app reports a saved draft and exits without formally committing the record.
4. Run `python main.py` again in the same window. Choose Record (1), select the fictional draft, and choose Resume (`恢复继续`, 2).
5. At the next duration prompt, enter `q` to end recording. Choose formal submission (1) and confirm (`y`). Verify that the displayed raw record and derived-output paths are inside `$smokeRoot`.
6. From the main menu, choose Output Management (2), then rebuild one date (1), and enter `2030-02-20`. Verify successful completion. Return to the main menu (0) and exit (3).

## Verify Files and Finish

Verify that `$smokeRoot/data/2030.02/2030-02-20/` contains the raw workbook and `$smokeRoot/output/2030.02/2030-02-20/` contains the summary and text outputs. Charts belong in `$smokeRoot/output/charts/`. Open the fictional raw workbook: it should contain exactly one confirmed 10-minute segment. Confirm the submitted draft is gone and every generated data/output file is under `$smokeRoot`.

Restore the previous environment setting after exiting:

```powershell
if ($null -eq $previousDataRoot) {
    Remove-Item Env:YAN_SHIKAN_DATA_ROOT -ErrorAction SilentlyContinue
} else {
    $env:YAN_SHIKAN_DATA_ROOT = $previousDataRoot
}
```

The test does not automatically delete `$smokeRoot`. Keep it for diagnosis if anything fails; report the failed step without sharing personal records. If all checks pass, reply exactly `SMOKE PASS` to authorize the next release step.
