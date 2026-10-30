import json
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH=Path(__file__).resolve().parent/"reconx.sqlite3"

def _connect():
    con=sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys=ON")
    return con

def init_db():
    with _connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS reconciliation_runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            invoices_json TEXT NOT NULL, payments_json TEXT NOT NULL, matches_json TEXT NOT NULL,
            balances_json TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS review_decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, transaction_id TEXT NOT NULL,
            decision TEXT NOT NULL, invoice_id TEXT, allocated_amount REAL,
            decided_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def _records(df):
    return json.loads(df.to_json(orient="records",date_format="iso"))

def save_run(invoices,payments,result):
    with _connect() as con:
        cur=con.execute("""INSERT INTO reconciliation_runs
            (created_at,invoices_json,payments_json,matches_json,balances_json)
            VALUES(?,?,?,?,?)""",(result["run_at"],json.dumps(_records(invoices)),
            json.dumps(_records(payments)),json.dumps(_records(result["matches_df"])),
            json.dumps(_records(result["invoice_balances"]))))
        return cur.lastrowid

def load_latest_run():
    with _connect() as con:
        row=con.execute("SELECT created_at,invoices_json,payments_json,matches_json,balances_json FROM reconciliation_runs ORDER BY id DESC LIMIT 1").fetchone()
    if not row: return None
    inv=pd.DataFrame(json.loads(row[1])); pay=pd.DataFrame(json.loads(row[2]))
    matches=pd.DataFrame(json.loads(row[3])); balances=pd.DataFrame(json.loads(row[4]))
    for col in ("invoice_date",): 
        if col in inv: inv[col]=pd.to_datetime(inv[col],errors="coerce")
    if "payment_date" in pay: pay["payment_date"]=pd.to_datetime(pay.payment_date,errors="coerce")
    if "invoice_date" in balances: balances["invoice_date"]=pd.to_datetime(balances.invoice_date,errors="coerce")
    counts=matches.status.value_counts().to_dict() if not matches.empty else {}
    summary={"matched":int(counts.get("Matched",0)),"partial":int(counts.get("Partial",0)),
             "unmatched":int(counts.get("Unmatched",0)),"review":int(counts.get("Overpayment",0))}
    summary_df=pd.DataFrame([{"status":k,"count":int(v)} for k,v in counts.items()])
    return {"invoices":inv,"payments":pay,"result":{"run_at":row[0],"matches_df":matches,
        "invoice_balances":balances,"unmatched_payments":matches[matches.status.isin(["Unmatched","Overpayment"])],
        "summary":summary,"summary_df":summary_df,"allocated_total":float(matches.allocated_amount.sum())}}

def save_decision(transaction_id,decision,invoice_id,allocated_amount):
    with _connect() as con:
        con.execute("INSERT INTO review_decisions(transaction_id,decision,invoice_id,allocated_amount) VALUES(?,?,?,?)",
                    (transaction_id,decision,invoice_id,float(allocated_amount)))

def load_decisions():
    with _connect() as con:
        return pd.read_sql_query("SELECT transaction_id,decision,invoice_id,allocated_amount,decided_at FROM review_decisions ORDER BY id DESC",con)
