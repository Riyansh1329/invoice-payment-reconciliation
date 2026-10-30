import re
import pandas as pd

def _clean_columns(df):
    df=df.copy()
    df.columns=[re.sub(r"[^a-z0-9]+","_",str(c).strip().lower()).strip("_") for c in df.columns]
    return df

def _first_existing(df,names):
    for n in names:
        if n in df.columns: return n
    return None

def prepare_invoices(raw):
    df=_clean_columns(raw)
    mapping={
        "invoice_id":["invoice_id","invoice_no","invoice_number","bill_no","id"],
        "customer_name":["customer_name","customer","client_name","party_name"],
        "customer_id":["customer_id","client_id","party_id"],
        "amount":["amount","invoice_amount","total","total_amount","value"],
        "invoice_date":["invoice_date","date","bill_date"]
    }
    out=pd.DataFrame()
    for target,aliases in mapping.items():
        col=_first_existing(df,aliases)
        if col: out[target]=df[col]
        elif target in ("customer_id","invoice_date"): out[target]=""
        else: raise ValueError(f"Invoice CSV is missing required column: {target} (accepted: {', '.join(aliases)})")
    out["invoice_id"]=out.invoice_id.astype(str).str.strip()
    out["customer_name"]=out.customer_name.fillna("").astype(str).str.strip()
    out["customer_id"]=out.customer_id.fillna("").astype(str).str.strip()
    out["amount"]=pd.to_numeric(out.amount,errors="coerce")
    out["invoice_date"]=pd.to_datetime(out.invoice_date,errors="coerce")
    if out.invoice_id.eq("").any() or out.invoice_id.duplicated().any():
        raise ValueError("Invoice IDs must be present and unique.")
    if out.amount.isna().any() or (out.amount<=0).any():
        raise ValueError("Invoice amounts must be valid positive numbers.")
    if out.customer_name.eq("").any(): raise ValueError("Every invoice must have a customer name.")
    return out.reset_index(drop=True)

def prepare_payments(raw):
    df=_clean_columns(raw)
    mapping={
        "transaction_id":["transaction_id","payment_id","txn_id","utr","id"],
        "description":["description","narration","details","remarks","customer_name","name"],
        "customer_name":["customer_name","customer","client_name","party_name"],
        "customer_id":["customer_id","client_id","party_id"],
        "amount":["amount","payment_amount","paid_amount","credit"],
        "payment_date":["payment_date","date","transaction_date","value_date"],
        "reference":["reference","invoice_reference","invoice_id","ref","remarks"]
    }
    out=pd.DataFrame()
    for target,aliases in mapping.items():
        col=_first_existing(df,aliases)
        if col: out[target]=df[col]
        elif target in ("description","customer_name","customer_id","payment_date","reference"): out[target]=""
        else: raise ValueError(f"Payment CSV is missing required column: {target}")
    out["transaction_id"]=out.transaction_id.astype(str).str.strip()
    out["description"]=out.description.fillna("").astype(str).str.strip()
    out["customer_name"]=out.customer_name.fillna("").astype(str).str.strip()
    out["customer_id"]=out.customer_id.fillna("").astype(str).str.strip()
    out["reference"]=out.reference.fillna("").astype(str).str.strip()
    out["amount"]=pd.to_numeric(out.amount,errors="coerce")
    out["payment_date"]=pd.to_datetime(out.payment_date,errors="coerce")
    if out.transaction_id.eq("").any() or out.transaction_id.duplicated().any():
        raise ValueError("Transaction IDs must be present and unique.")
    if out.amount.isna().any() or (out.amount<=0).any():
        raise ValueError("Payment amounts must be valid positive numbers.")
    return out.reset_index(drop=True)

def validate_pair(invoices,payments):
    issues=[]
    if invoices.empty: issues.append("Invoice file contains no records.")
    if payments.empty: issues.append("Payment file contains no records.")
    return issues
