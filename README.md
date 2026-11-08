# FinanceIQ — Vega Self Drive Car

Automated synthetic financial analytics for one company. No live bank, Plaid, or QuickBooks connections. The included sample uses illustrative USD amounts and January–June 2026 dates. Reports show cash receipts less cash payments, not accounting profit.

## Windows CMD / VS Code

Open this folder in VS Code, select **Terminal > New Terminal > Command Prompt**, and run:

```cmd
run.cmd
```

The runner creates `.venv` if needed, installs the pinned dependencies once, runs all tests, regenerates the deterministic synthetic CSVs, imports them into SQLite, and starts Streamlit at http://127.0.0.1:8501. Keep the terminal open; press Ctrl+C to stop. No environment activation is required. Run only one interactive runner at a time.

For a fresh machine, install 64-bit Python 3.12 with the Python launcher, reopen CMD, and verify `py -3 --version` first. The project was tested on Python 3.12.14 / Windows. Internet access is needed for initial dependency installation. If Python is installed without the launcher:

```cmd
set "FINANCEIQ_PYTHON=C:\Path\To\python.exe"
run.cmd
```

Use a short extraction path (such as `C:\Projects\FinanceIQ`) if Windows reports a path-length error. The supplied requirements pin Streamlit 1.50.0 after a newer release failed to install in this long workspace path. `requirements.in` records the top-level requirements; `requirements.txt` freezes the tested environment, including dependencies.

## Commands

```cmd
run.cmd verify
run.cmd etl
.venv\Scripts\python.exe -m streamlit run app.py
```

- `verify`: tests, deterministic data generation, and ETL; exits without launching a dashboard.
- `etl`: imports the current CSV files only; no regeneration, tests, or dashboard. Fails on missing or invalid input. Run `verify` successfully before scheduling it.
- The final command starts the dashboard without regenerating data.

`verify` and the default run overwrite both synthetic CSVs with the fixed seed-42 sample. They do not clear SQLite or manual reviews. ETL upserts by transaction ID, collapses identical duplicates, rejects conflicting duplicates, and preserves reviewed categories. Import is transactional: invalid input rolls back row changes. Imports do not delete previously loaded IDs that are removed from the source. The tests use isolated temporary datasets and databases.

## Verification

```cmd
run.cmd verify
run.cmd etl
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -c "from src.reports import summary; d=summary(); print({k:v for k,v in d.items() if k not in ('transactions','categories','monthly')}); print('Unique transactions:',len(d['transactions']))"
type logs\workflow.log
```

On the untouched sample, expect 14 passing tests, 56 bank CSV rows, 54 ledger rows, and 55 unique database transactions. Receipts: **$86,087.46**; payments: **$47,396.53**; surplus: **$38,690.93**. One unidentified vendor payment is unmatched and requires review. Approving it changes the review count; reimport preserves that choice. Test coverage includes duplicate handling, invalid-input rollback, repeat imports, single-company scope, totals, month filtering, manual review persistence, and Streamlit UI interactions.

Open the dashboard, choose January, check that the transaction table has nine records, then return to All. The local financial assistant works without an API key. The existing optional API integration remains available only if you separately configure your own `OPENAI_API_KEY`; this workflow creates no keys and makes no AI API calls. With an existing key set, clicking Analyze may use that integration. No API integration was validated in this work.

Logs rotate at approximately 1 MB with three backups. Failures return a nonzero exit code and stop the runner before dashboard launch. Dependency-installation and pytest details appear in the terminal; workflow outcomes and exception traces appear in `logs\workflow.log`.

## Optional Windows Task Scheduler

No task is registered automatically. From CMD in this folder, after `run.cmd verify` succeeds:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File .\schedule.ps1 -At "09:00"
schtasks /Query /TN "FinanceIQ-Vega-Daily-ETL" /V /FO LIST
schtasks /Run /TN "FinanceIQ-Vega-Daily-ETL"
```

This registers daily 09:00 ETL in the Windows computer's local time zone, for the current logged-in user, without storing a password or requesting administrator privileges. The script sets the working folder and quotes paths containing spaces. It prevents overlapping instances, retries a missed start when available, and limits a run to 15 minutes. The computer must be on and the user logged in; default Windows battery rules may delay it. It imports the same fixed synthetic sample until you change the CSVs; it does not simulate new daily transactions. Keep the project in place after registration.

Wait for the task to finish, query it again, and confirm `Last Result` is `0` and `logs\workflow.log` has a new successful entry. To remove the task:

```cmd
schtasks /Delete /TN "FinanceIQ-Vega-Daily-ETL"
```

The scheduler registration script was reviewed but not registered or executed as a scheduled task.

## Files

- `run.cmd`: environment, dependencies, tests, pipeline, dashboard.
- `src/workflow.py`: orchestration, rotating logs, exit codes.
- `src/generate_data.py`: fixed synthetic Vega data.
- `src/pipeline.py`: validation, classification, reconciliation, SQLite upserts and review.
- `src/reports.py`: cash-basis aggregates and monthly filtering.
- `app.py`: dashboard; `src/assistant.py`: local summary plus existing optional API integration.
- `data/finance.db`: SQLite; two CSVs are the ETL inputs.
- `tests/`: isolated pipeline and dashboard checks.
- `schedule.ps1`: optional, explicit task registration.

The original ZIP in Downloads was not modified. This working copy was extracted from `financeiq_vega_self_drive_car.zip` and extended.
