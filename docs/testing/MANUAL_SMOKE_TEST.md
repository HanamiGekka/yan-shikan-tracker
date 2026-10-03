# Manual CLI Smoke Test

## Current Validation Status

The initial synthetic workflow was checked successfully: a single 10-minute record was recovered from a draft, submitted, and rebuilt into a daily workbook, text reports, and four charts. The observed EOF traceback was fixed. The focused Ctrl+C re-test below was confirmed passed on 2026-10-03: no traceback, a readable preserved draft, and successful discard without formal submission.

## Focused Ctrl+C Re-Test

Allow 2-3 minutes. Use only fictional records in a fresh temporary directory. There is no need to repeat formal submission or output rebuilding.

From PowerShell at the repository root, with Python and runtime dependencies available:

```powershell
$smokeRoot = Join-Path $env:TEMP ('yan-shikan-smoke-' + (Get-Date -Format 'yyyyMMddHHmmss'))
$previousDataRoot = $env:YAN_SHIKAN_DATA_ROOT
$env:YAN_SHIKAN_DATA_ROOT = $smokeRoot
python main.py
```

Verify the displayed category configuration path is inside `$smokeRoot`. If it points to the real repository data directory, exit immediately. All generated files must remain inside `$smokeRoot`.

1. Choose Record (main-menu option `1`).
2. Enter fictional date `2030-02-21`, duration `5`, Exercise (category `a`), feeling `2`, and note `Focused manual demo only`.
3. Confirm the segment with `c`.
4. At the continue prompt, press actual **Ctrl+C**. Do not substitute Ctrl+Z or close the terminal. The app must explain interruption and draft preservation, exit without a Python traceback, and avoid formal submission.
5. In the same PowerShell window, run `python main.py` again. Choose Record (`1`) and select the sole synthetic draft (`1`). Choose View Summary (`1`); verify its date, one segment, five minutes, feeling, and fictional note are readable. This confirms that the stored draft can be loaded; recovery and submission were already checked in the initial run.
6. Choose Discard and End (`6`), then Exit from the main menu (`3`).
7. Check `$smokeRoot/data/drafts/` has no remaining draft JSON. No daily source workbook or generated reports should exist: this test does not submit data.

After the app exits, restore the previous environment setting:

```powershell
if ($null -eq $previousDataRoot) {
    Remove-Item Env:YAN_SHIKAN_DATA_ROOT -ErrorAction SilentlyContinue
} else {
    $env:YAN_SHIKAN_DATA_ROOT = $previousDataRoot
}
```

Keep the temporary directory until release cleanup verifies it contains only synthetic smoke data. Do not remove real repository `data/` or `output/`.

If any step fails, report the step and keep the temporary directory for diagnosis. If every check passes, reply exactly:

```text
SMOKE PASS
```

## Non-Blocking Environment Observations

A Qt EUDC font warning was observed in one Windows environment, but charts were generated. A chart with one synthetic date may have a broad automatically scaled date axis. Neither observation blocks this focused interruption check.
