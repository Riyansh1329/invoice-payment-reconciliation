import pandas as pd
from services.data_processor import prepare_invoices, prepare_payments
from services.reconciliation import reconcile

def sample():
    inv=prepare_invoices(pd.DataFrame([
        {"invoice_id":"I1","customer_name":"Rahul Sharma","customer_id":"C1","amount":5000,"invoice_date":"2026-10-01"},
        {"invoice_id":"I2","customer_name":"Amit Verma","customer_id":"C2","amount":3000,"invoice_date":"2026-10-02"},
    ]))
    pay=prepare_payments(pd.DataFrame([
        {"transaction_id":"T1","description":"Rahul Sharma","customer_id":"C1","amount":5000,"reference":"I1"},
        {"transaction_id":"T2","description":"Amit V","customer_id":"C2","amount":1000},
        {"transaction_id":"T3","description":"Mystery","amount":500},
    ]))
    return inv,pay

def test_matching_exact_partial_unmatched():
    inv,pay=sample()
    r=reconcile(inv,pay)
    assert list(r["matches_df"].status)==["Matched","Partial","Unmatched"]
    assert r["invoice_balances"].loc[1,"outstanding_amount"]==2000

def test_amounts_are_positive():
    try:
        prepare_invoices(pd.DataFrame([{"invoice_id":"I1","customer_name":"A","amount":0}]))
        assert False
    except ValueError as e:
        assert "positive" in str(e)

def test_duplicate_invoice_ids_rejected():
    try:
        prepare_invoices(pd.DataFrame([{"invoice_id":"I1","customer_name":"A","amount":10},{"invoice_id":"I1","customer_name":"B","amount":20}]))
        assert False
    except ValueError as e:
        assert "unique" in str(e)

def test_overpayment_is_flagged():
    inv=prepare_invoices(pd.DataFrame([{"invoice_id":"I1","customer_name":"A","amount":100}]))
    pay=prepare_payments(pd.DataFrame([{"transaction_id":"T1","description":"A","amount":150,"reference":"I1"}]))
    r=reconcile(inv,pay)
    assert r["matches_df"].iloc[0].status=="Overpayment"
    assert r["matches_df"].iloc[0].unallocated_amount==50
