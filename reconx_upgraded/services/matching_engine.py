import re
from rapidfuzz import fuzz

def norm(value):
    return re.sub(r"[^a-z0-9]+","",str(value or "").lower())

def score_candidate(invoice,payment):
    inv_id=norm(invoice.invoice_id)
    ref=norm(payment.reference)
    desc=norm(payment.description)
    if ref and (ref==inv_id or inv_id in ref):
        return 100, "Invoice reference found in payment reference"
    if invoice.customer_id and payment.customer_id and norm(invoice.customer_id)==norm(payment.customer_id):
        return 96, "Customer ID matches"
    customer=norm(invoice.customer_name)
    p_name=norm(payment.customer_name)
    if not p_name: p_name=desc
    if customer and p_name:
        score=fuzz.ratio(customer,p_name)
        if score>=50: return float(score), f"Customer name similarity: {score:.0f}%"
    return 0, "No reliable identity evidence"
