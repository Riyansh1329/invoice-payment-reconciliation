# ReconX — Smart Invoice & Payment Reconciliation

ReconX is a Streamlit application that imports invoice and payment CSV files, validates and normalizes records, suggests payment-to-invoice allocations, highlights exceptions, stores runs and review decisions in SQLite, and exports reports.

## Features

- Upload invoice and payment CSV files with a preview.
- Validate required columns, unique IDs, and positive numeric amounts.
- Normalize common column names and customer/reference values.
- Explainable matching using invoice reference, customer ID, and RapidFuzz name similarity.
- Allocate partial payments against remaining invoice balances.
- Flag unmatched payments and overpayments instead of silently forcing a match.
- Dashboard KPIs, invoice balances, exception queue, and CSV exports.
- SQLite persistence for the latest run history and review decision audit log.
- Automated tests with pytest.

> Matching suggestions are not proof of identity. Review them before treating a transaction as reconciled. The demo app records review decisions; it does not initiate payments or connect to a bank.

## CSV format

**Invoices (required):** `invoice_id`, `customer_name`, `amount`  
Optional: `customer_id`, `invoice_date`

**Payments (required):** `transaction_id`, `amount`  
Optional: `description`, `customer_name`, `customer_id`, `payment_date`, `reference`

Column aliases such as `invoice_no`, `invoice_number`, `payment_id`, `txn_id`, `invoice_amount`, and `payment_amount` are also accepted.

## Run on Windows (PowerShell)

1. Extract the ZIP.
2. Open the extracted `invoice-payment-reconciliation` folder in VS Code.
3. Open Terminal → New Terminal and confirm you are in the folder containing `app.py`.
4. Run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, run this once in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Then open the local address printed by Streamlit, usually `http://localhost:8501`.

### If Python 3.11 is not installed

Check installed Python versions:

```powershell
py --list
```

Use an installed version by replacing `3.11` above (for example `py -3.13 -m venv .venv`).

## Try the demo data

In the app, select **Upload Records → Load included demo data**, then open **Reconciliation → Run reconciliation**. Review the suggestions, then inspect **Dashboard**, **Review Transactions**, and **Reports**.

## Run tests

```powershell
python -m pytest -q
```

## Project structure

```text
app.py                       Streamlit user interface and navigation
services/data_processor.py   CSV column mapping, cleaning and validation
services/matching_engine.py  Explainable invoice/payment candidate scoring
services/reconciliation.py   Allocation logic, statuses and invoice balances
database/db.py               SQLite run persistence and review audit log
data/                        Demo invoice and payment CSV files
tests/                       Automated tests
requirements.txt              Python dependencies
```

## Data flow

CSV upload → validation/normalization → candidate scoring → payment allocation → review → SQLite persistence → dashboard/reports.

## Known limitations

- CSV import only; no direct bank, ERP, or accounting-platform integration.
- Current allocation chooses the strongest eligible invoice candidate for each payment. Ambiguous cases should be reviewed.
- Review decisions are stored in the audit log but do not alter the original matching calculation.
- SQLite is local to the machine running the app. Back up `database/reconx.sqlite3` if you need to retain history.
