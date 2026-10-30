from datetime import datetime
import pandas as pd
from services.matching_engine import score_candidate

def reconcile(invoices,payments,threshold=75):
    inv=invoices.copy().reset_index(drop=True)
    pay=payments.copy().reset_index(drop=True)
    remaining={str(row.invoice_id):float(row.amount) for _,row in inv.iterrows()}
    rows=[]
    used_invoice_payment={}
    for _,p in pay.iterrows():
        candidates=[]
        for _,i in inv.iterrows():
            balance=remaining[str(i.invoice_id)]
            if balance<=0.009: continue
            score,evidence=score_candidate(i,p)
            if score>=threshold: candidates.append((score,evidence,i))
        if candidates:
            candidates.sort(key=lambda x:(x[0], x[2].invoice_date if pd.notna(x[2].invoice_date) else pd.Timestamp.max),reverse=True)
            score,evidence,i=candidates[0]
            inv_id=str(i.invoice_id)
            allocation=min(float(p.amount),remaining[inv_id])
            remaining[inv_id]=round(remaining[inv_id]-allocation,2)
            excess=round(float(p.amount)-allocation,2)
            if excess>0.009: status="Overpayment"
            elif allocation+0.009 < float(i.amount): status="Partial"
            else: status="Matched"
            rows.append({
                "transaction_id":str(p.transaction_id),"description":str(p.description),
                "invoice_id":inv_id,"customer_name":str(i.customer_name),
                "payment_amount":float(p.amount),"allocated_amount":allocation,
                "unallocated_amount":excess,"confidence":float(score),
                "status":status,"evidence":evidence
            })
        else:
            rows.append({
                "transaction_id":str(p.transaction_id),"description":str(p.description),
                "invoice_id":"","customer_name":"","payment_amount":float(p.amount),
                "allocated_amount":0.0,"unallocated_amount":float(p.amount),
                "confidence":0.0,"status":"Unmatched","evidence":"No candidate met the matching threshold"
            })
    matches=pd.DataFrame(rows,columns=["transaction_id","description","invoice_id","customer_name","payment_amount","allocated_amount","unallocated_amount","confidence","status","evidence"])
    balances=inv[["invoice_id","customer_name","amount","invoice_date"]].copy()
    balances["allocated_amount"]=balances.invoice_id.map(lambda x:round(float(inv.loc[inv.invoice_id==x,"amount"].iloc[0])-remaining[str(x)],2))
    balances["outstanding_amount"]=balances.invoice_id.map(lambda x:round(remaining[str(x)],2))
    balances["status"]=balances.outstanding_amount.apply(lambda x:"Paid" if x<=0.009 else ("Partially paid" if x < 1e18 and x>0 else "Unpaid"))
    counts=matches.status.value_counts().to_dict()
    summary={"matched":int(counts.get("Matched",0)),"partial":int(counts.get("Partial",0)),
            "unmatched":int(counts.get("Unmatched",0)),"review":int(counts.get("Overpayment",0))}
    summary_df=pd.DataFrame([{"status":k,"count":int(v)} for k,v in matches.status.value_counts().items()])
    unmatched=matches[matches.status.isin(["Unmatched","Overpayment"])].copy()
    return {"run_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"matches_df":matches,
            "invoice_balances":balances,"unmatched_payments":unmatched,
            "summary":summary,"summary_df":summary_df,
            "allocated_total":float(matches.allocated_amount.sum())}
