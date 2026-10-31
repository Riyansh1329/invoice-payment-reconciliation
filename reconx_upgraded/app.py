import io
import pandas as pd
import streamlit as st

from services.data_processor import (
    prepare_invoices,
    prepare_payments,
    validate_pair
)

from services.reconciliation import reconcile

from database.db import (
    init_db,
    save_run,
    load_latest_run,
    save_decision,
    load_decisions
)


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="ReconX | Smart Reconciliation",
    page_icon="💸",
    layout="wide"
)

init_db()

st.markdown("""
<style>
:root {
    --forest: #183A2B;
    --forest-2: #244B38;
    --ivory: #F6F1E5;
    --ivory-card: #FFFCF4;
    --yellow: #E6B84A;
    --yellow-soft: #F4D98B;
    --ink: #1B3025;
    --muted: #657568;
}

/* Warm ivory workspace */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: #F6F1E5 !important;
}
[data-testid="stHeader"] {
    background: rgba(246,241,229,.96) !important;
}
.block-container {
    max-width: 1440px;
    padding-top: 2.4rem !important;
    padding-bottom: 2.5rem;
}

/* Hide old sidebar */
[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
    display: none !important;
}

/* Dark green navbar background */
.st-key-reconx-navbar {
    background: #183A2B !important;
    border: 1px solid rgba(230,184,74,.35) !important;
    border-radius: 14px !important;
    padding: .75rem 1.25rem !important;
    margin-bottom: 1rem !important;
}

/* Brand inside the dark navbar */
.reconx-brand {
    color: #F6F1E5 !important;
    font-size: 1.55rem;
    font-weight: 850;
    letter-spacing: -.5px;
    padding: .35rem 0 .65rem;
}
.reconx-brand small {
    display: block;
    color: #F4D98B !important;
    font-size: .72rem;
    font-weight: 550;
    letter-spacing: .2px;
    margin-top: 2px;
}

/* Text-only navbar buttons: no radio circles, no button boxes */
div[class*="st-key-nav_"] {
    padding-top: .2rem;
}
div[class*="st-key-nav_"] button {
    width: 100% !important;
    min-height: 2.5rem !important;
    padding: .45rem .12rem !important;
    background: transparent !important;
    color: #F6F1E5 !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-size: .93rem !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
    transition: color .2s ease, transform .2s ease !important;
}
div[class*="st-key-nav_"] button:hover {
    color: #E6B84A !important;
    background: transparent !important;
    border: 0 !important;
    transform: translateY(-2px);
    box-shadow: none !important;
}
div[class*="st-key-nav_"] button:focus:not(:active) {
    color: #F6F1E5 !important;
    border: 0 !important;
    box-shadow: none !important;
    outline: none !important;
}

/* Give the active tab a yellow underline */
div.st-key-nav_dashboard button,
div.st-key-nav_upload button,
div.st-key-nav_reconciliation button,
div.st-key-nav_review button,
div.st-key-nav_reports button {
    position: relative;
}
/* Brand + text-only array-style navbar */
.reconx-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    width: 100%;
    padding: 1.1rem 0 .9rem;
}
.reconx-nav-links {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    flex-wrap: nowrap;
    gap: clamp(.8rem, 1.8vw, 1.7rem);
}
.reconx-nav-link {
    display: inline-block;
    position: relative;
    padding: .55rem 0 .7rem;
    color: #183A2B !important;
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    text-decoration: none !important;
    white-space: nowrap;
    font-size: .94rem;
    font-weight: 700;
    transition: color .2s ease, transform .2s ease;
}
.reconx-nav-link:hover {
    color: #A87912 !important;
    transform: translateY(-2px);
}
.reconx-nav-link.active::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: .25rem;
    height: 3px;
    border-radius: 3px;
    background: #E6B84A;
}
@media (max-width: 900px) {
    .reconx-topbar {
        align-items: flex-start;
        flex-direction: column;
        gap: .5rem;
    }
    .reconx-nav-links {
        justify-content: flex-start;
        flex-wrap: wrap;
    }
}
/* Typography: force headings to dark green for strong contrast on ivory */
h1, h2, h3, h4,
[data-testid="stHeading"] h1,
[data-testid="stHeading"] h2,
[data-testid="stHeading"] h3 {
    color: #183A2B !important;
    font-weight: 800 !important;
}
p, label, .stMarkdown, [data-testid="stCaptionContainer"] {
    color: #1B3025;
}
h1 {
    font-size: 2.45rem !important;
    font-weight: 850 !important;
    letter-spacing: -.8px !important;
}
h2, h3 { font-weight: 760 !important; }
hr { border-color: rgba(24,58,43,.22) !important; }

/* KPI cards */
[data-testid="stMetric"] {
    background: #FFFCF4 !important;
    border: 1px solid rgba(24,58,43,.12) !important;
    border-top: 4px solid #E6B84A !important;
    border-radius: 15px !important;
    padding: 1rem 1.15rem !important;
    box-shadow: 0 7px 18px rgba(24,58,43,.08) !important;
}
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
[data-testid="stMetricDelta"] { color: #183A2B !important; }
[data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
}

/* Inputs, tables, alerts and buttons */
[data-testid="stAlert"] {
    background: #FFF9E9 !important;
    border: 1px solid rgba(230,184,74,.55) !important;
    border-radius: 13px !important;
}
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    border: 1px solid rgba(24,58,43,.18);
    border-radius: 12px;
    overflow: hidden;
}
.stButton > button, .stDownloadButton > button,
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] button span {
    background: #183A2B !important;
    color: #FFFFFF !important;
    border: 1px solid #183A2B !important;
    border-radius: 11px !important;
    font-weight: 700 !important;
    transition: transform .2s ease, box-shadow .2s ease !important;
}

/* Force button labels and nested text/icons to white */
.stButton > button *,
.stDownloadButton > button *,
[data-testid="stFileUploader"] button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
[data-testid="stFileUploader"] button:hover {
    background: #244B38 !important;
    border-color: #E6B84A !important;
    color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 7px 16px rgba(24,58,43,.18) !important;
}
.dashboard-note {
    color: #52695A;
    font-size: 14px;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. TOP NAVIGATION — TEXT-ONLY INLINE LINKS
# ==========================================

# The selected page is carried in the URL, so the navbar contains no buttons
# or radio controls—only clickable text labels arranged in one horizontal row.
# ==========================================
# 2. TOP NAVIGATION — SINGLE PAGE
# ==========================================

pages = [
    "Dashboard",
    "Upload Records",
    "Reconciliation",
    "Review Transactions",
    "Reports"
]

if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"

with st.container(key="reconx-navbar"):
    nav_brand, nav_links = st.columns([2, 8], vertical_alignment="center")

    with nav_brand:
        st.markdown(
            '<div class="reconx-brand">💸 ReconX'
            '<small>Invoice &amp; Payment Reconciliation</small></div>',
            unsafe_allow_html=True
        )

    with nav_links:
        cols = st.columns(5)

        for i, name in enumerate(pages):
            with cols[i]:
                is_active = st.session_state.active_page == name

                label = f"**{name}**" if is_active else name

                if st.button(
                    label,
                    key=f"nav_{i}",
                    use_container_width=True
                ):
                    st.session_state.active_page = name
                    st.rerun()

page = st.session_state.active_page

st.markdown("---")

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def money(value):
    return f"₹{float(value):,.2f}"


def current():
    return st.session_state.get("result")


# ==========================================
# 4. SESSION STATE INITIALIZATION
# ==========================================

if "invoices" not in st.session_state:
    st.session_state.invoices = None

if "payments" not in st.session_state:
    st.session_state.payments = None

if "result" not in st.session_state:

    saved = load_latest_run()

    if saved:
        st.session_state.invoices = saved["invoices"]
        st.session_state.payments = saved["payments"]
        st.session_state.result = saved["result"]

if "decisions" not in st.session_state:
    st.session_state.decisions = load_decisions()


# ==========================================
# 5. DASHBOARD
# ==========================================

if page == "Dashboard":

    st.title("Dashboard")

    st.write(
        "Welcome to ReconX. Manage your invoices and payment reconciliation."
    )

    st.markdown("---")

    r = current()

    # Dashboard metrics
    if r is None:
        total_inv = 0.0
        total_pay = 0.0
        matched = 0
        outstanding = 0.0

    else:
        total_inv = float(st.session_state.invoices["amount"].sum())
        total_pay = float(st.session_state.payments["amount"].sum())
        matched = int(r["summary"]["matched"])
        outstanding = max(
            0.0,
            total_inv - float(r["allocated_total"])
        )

    # Four metric columns
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        label="Total Invoices",
        value=money(total_inv)
    )

    c2.metric(
        label="Total Payments",
        value=money(total_pay)
    )

    c3.metric(
        label="Matched",
        value=str(matched)
    )

    c4.metric(
        label="Outstanding",
        value=money(outstanding)
    )

    st.markdown(
        """
        <p class="dashboard-note">
            Matched and Outstanding are provisional until confirmed
            reconciliation allocations are implemented.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Getting Started section
    st.subheader("Getting Started")

    st.info(
        "Upload your invoice and payment CSV files to begin reconciliation."
    )

    # Show additional information after reconciliation
    if r is not None:

        st.caption(
            f"Latest run: {r['run_at']} | "
            f"{len(st.session_state.invoices)} invoices | "
            f"{len(st.session_state.payments)} payments"
        )

        st.subheader("Reconciliation Status")

        if not r["summary_df"].empty:
            st.bar_chart(
                r["summary_df"].set_index("status")["count"]
            )

        st.subheader("Recent Suggested Matches")

        st.dataframe(
            r["matches_df"].head(10),
            use_container_width=True,
            hide_index=True
        )
# ==========================================
# 6. UPLOAD RECORDS
# ==========================================

elif page == "Upload Records":

    st.title("Upload Financial Records")

    st.write(
        "Upload your invoice and payment CSV files."
    )

    a, b = st.columns(2)

    with a:
        inv_file = st.file_uploader(
            "Invoice CSV",
            type="csv",
            key="inv_upload"
        )

    with b:
        pay_file = st.file_uploader(
            "Payment CSV",
            type="csv",
            key="pay_upload"
        )

    st.markdown("---")

    if st.button(
        "📤 Upload Data",
        type="primary",
        use_container_width=True
    ):

        if inv_file is None or pay_file is None:

            st.error(
                "Please select both Invoice and Payment CSV files."
            )

        else:

            try:

                # Read invoice CSV
                inv = prepare_invoices(
                    pd.read_csv(
                        io.BytesIO(inv_file.getvalue())
                    )
                )

                # Read payment CSV
                pay = prepare_payments(
                    pd.read_csv(
                        io.BytesIO(pay_file.getvalue())
                    )
                )

                # Validate records
                issues = validate_pair(inv, pay)

                if issues:

                    for issue in issues:
                        st.error(issue)

                else:

                    st.session_state.invoices = inv
                    st.session_state.payments = pay

                    # Reset old reconciliation result
                    st.session_state.result = None

                    st.success(
                        "Data uploaded successfully!"
                    )

                    st.info(
                        f"Ready: {len(inv)} invoices "
                        f"and {len(pay)} payments."
                    )

            except Exception as e:

                st.error(f"Upload failed: {e}")

    if (
        st.session_state.invoices is not None
        and st.session_state.payments is not None
    ):

        st.markdown("---")

        st.subheader("Uploaded Data Summary")

        c1, c2 = st.columns(2)

        c1.metric(
            "Total Invoices",
            len(st.session_state.invoices)
        )

        c2.metric(
            "Total Payments",
            len(st.session_state.payments)
        )

# ==========================================
# 7. RECONCILIATION
# ==========================================

elif page == "Reconciliation":

    st.title("Reconciliation")

    inv = st.session_state.invoices

    pay = st.session_state.payments

    if inv is None or pay is None:

        st.warning(
            "Upload both datasets first, or load demo data "
            "from Upload Records."
        )

    else:

        st.write(
            "Run the matching engine. Suggestions are explainable "
            "and should be reviewed before acceptance."
        )

        threshold = st.slider(
            "Minimum name similarity "
            "(when IDs/reference are unavailable)",
            0,
            100,
            75
        )

        if st.button(
            "Run Reconciliation",
            type="primary"
        ):

            try:

                result = reconcile(
                    inv,
                    pay,
                    threshold
                )

                st.session_state.result = result

                run_id = save_run(
                    inv,
                    pay,
                    result
                )

                st.session_state.decisions = load_decisions()

                st.success(
                    f"Reconciliation completed. Run #{run_id} saved."
                )

            except Exception as e:

                st.error(
                    f"Reconciliation failed: {e}"
                )

        r = current()

        if r is not None:

            c = st.columns(4)

            c[0].metric(
                "Matched",
                r["summary"]["matched"]
            )

            c[1].metric(
                "Partial",
                r["summary"]["partial"]
            )

            c[2].metric(
                "Unmatched",
                r["summary"]["unmatched"]
            )

            c[3].metric(
                "Needs Review",
                r["summary"]["review"]
            )

            st.subheader("Matching Results")

            st.dataframe(
                r["matches_df"],
                use_container_width=True,
                hide_index=True
            )


# ==========================================
# 8. REVIEW TRANSACTIONS
# ==========================================

elif page == "Review Transactions":

    st.title("Review Transactions")

    r = current()

    if r is None:

        st.info("Run reconciliation first.")

    else:

        df = r["matches_df"]

        # ==================================
        # GET ALREADY DECIDED TRANSACTIONS
        # ==================================

        decisions = st.session_state.decisions

        decided_ids = set()

        if decisions is not None and not decisions.empty:

            decided_ids = set(
                decisions["transaction_id"].astype(str)
            )

        # ==================================
        # FILTER PENDING TRANSACTIONS
        # ==================================

        pending = df[
            df["status"].isin([
                "Matched",
                "Partial",
                "Needs review",
                "Unmatched",
                "Overpayment"
            ])
            &
            ~df["transaction_id"].astype(str).isin(decided_ids)
        ].copy()

        # ==================================
        # DISPLAY PENDING TRANSACTIONS
        # ==================================

        if pending.empty:

            st.info("No suggested transactions.")

        else:

            st.caption(
                "Confirm or reject suggestions. Decisions are "
                "recorded in the local SQLite audit log."
            )

            for _, row in pending.iterrows():

                key = str(row.transaction_id)

                with st.container(border=True):

                    x, y, z = st.columns([2, 3, 2])

                    x.markdown(f"**{key}**")

                    x.caption(
                        f"Invoice: {row.invoice_id or '—'}"
                    )

                    y.write(str(row.description))

                    y.caption(
                        f"Payment {money(row.payment_amount)} · "
                        f"Suggested allocation {money(row.allocated_amount)} · "
                        f"Confidence {row.confidence:.0f}%"
                    )

                    z.write(f"**{row.status}**")

                    d1, d2 = st.columns(2)

                    # ==================================
                    # CONFIRM BUTTON
                    # ==================================

                    if d1.button(
                        "Confirm",
                        key=f"yes_{key}"
                    ):

                        save_decision(
                            key,
                            "Confirmed",
                            str(row.invoice_id or ""),
                            float(row.allocated_amount)
                        )

                        st.session_state.decisions = load_decisions()

                        st.success(f"{key} confirmed successfully!")

                        st.rerun()

                    # ==================================
                    # REJECT BUTTON
                    # ==================================

                    if d2.button(
                        "Reject",
                        key=f"no_{key}"
                    ):

                        save_decision(
                            key,
                            "Rejected",
                            str(row.invoice_id or ""),
                            float(row.allocated_amount)
                        )

                        st.session_state.decisions = load_decisions()

                        st.success(f"{key} rejected successfully!")

                        st.rerun()

        # ==================================
        # DECISION HISTORY
        # ==================================

        decisions = st.session_state.decisions

        st.markdown("---")

        st.subheader("Decision History")

        if decisions is not None and not decisions.empty:

            st.dataframe(
                decisions,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No decisions recorded yet.")
# ==========================================
# 9. REPORTS
# ==========================================

elif page == "Reports":

    st.title("📊 Financial Reconciliation Reports")

    st.write(
        "A simple overview of invoices, received payments "
        "and pending amounts."
    )

    r = current()

    if r is None:

        st.warning(
            "Please run reconciliation first."
        )

    else:

        # ==================================
        # 1. RECONCILIATION SUMMARY
        # ==================================

        st.subheader("1. Reconciliation Summary")

        summary_data = pd.DataFrame({
            "Payment Status": [
                "Successfully Matched",
                "Partial Payment",
                "Unmatched",
                "Needs Review"
            ],

            "Total Transactions": [
                r["summary"]["matched"],
                r["summary"]["partial"],
                r["summary"]["unmatched"],
                r["summary"]["review"]
            ],

            "Meaning": [
                "Payment matched with invoice",
                "Partial or multiple payment allocation",
                "Invoice could not be identified",
                "Requires manual verification"
            ]
        })

        st.dataframe(
            summary_data,
            use_container_width=True,
            hide_index=True
        )

        # ==================================
        # 2. FINANCIAL OVERVIEW
        # ==================================

        st.divider()

        st.subheader("2. Financial Overview")

        invoices = st.session_state.invoices
        payments = st.session_state.payments

        total_invoice_value = float(
            invoices["amount"].sum()
        )

        total_payment_value = float(
            payments["amount"].sum()
        )

        allocated_value = float(
            r["allocated_total"]
        )

        invoice_df = r["invoice_balances"].copy()

        outstanding = float(
            invoice_df["outstanding_amount"].sum()
        )

        unallocated = max(
            0,
            total_payment_value - allocated_value
        )

        financial_data = pd.DataFrame({
            "Financial Details": [
                "Total Invoice Value",
                "Total Payments Received",
                "Total Allocated Amount",
                "Outstanding Invoice Amount",
                "Unallocated Payment Amount"
            ],

            "Amount (INR)": [
                total_invoice_value,
                total_payment_value,
                allocated_value,
                outstanding,
                unallocated
            ]
        })

        st.dataframe(
            financial_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Amount (INR)": st.column_config.NumberColumn(
                    "Amount (INR)",
                    format="₹%.2f"
                )
            }
        )



        # ==================================
        # 2.5 VISUAL ANALYTICS DASHBOARD
        # ==================================

        st.divider()
        st.header("📊 Visual Analytics")

        # KPI strip, styled to match the reference dashboard
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Invoice Value", money(total_invoice_value))
        k2.metric("Payments Received", money(total_payment_value))
        k3.metric("Allocated", money(allocated_value))
        k4.metric("Outstanding", money(outstanding))

        # Prepare date-based totals only from dates present in the uploaded data.
        invoice_trend = invoices.copy()
        payment_trend = payments.copy()

        if "invoice_date" in invoice_trend.columns:
            invoice_trend["invoice_date"] = pd.to_datetime(
                invoice_trend["invoice_date"], errors="coerce"
            )
            invoice_trend = invoice_trend.dropna(subset=["invoice_date"])
            invoice_trend["Period"] = (
                invoice_trend["invoice_date"].dt.to_period("M").astype(str)
            )
            invoice_monthly = (
                invoice_trend.groupby("Period", as_index=False)["amount"]
                .sum()
                .rename(columns={"amount": "Invoice Value"})
            )
        else:
            invoice_monthly = pd.DataFrame(columns=["Period", "Invoice Value"])

        if "payment_date" in payment_trend.columns:
            payment_trend["payment_date"] = pd.to_datetime(
                payment_trend["payment_date"], errors="coerce"
            )
            payment_trend = payment_trend.dropna(subset=["payment_date"])
            payment_trend["Period"] = (
                payment_trend["payment_date"].dt.to_period("M").astype(str)
            )
            payment_monthly = (
                payment_trend.groupby("Period", as_index=False)["amount"]
                .sum()
                .rename(columns={"amount": "Payments Received"})
            )
        else:
            payment_monthly = pd.DataFrame(columns=["Period", "Payments Received"])

        monthly_chart = pd.merge(
            invoice_monthly, payment_monthly, on="Period", how="outer"
        ).fillna(0).sort_values("Period")

        # Customer-level comparison data
        customer_invoice = (
            invoices.groupby("customer_name", as_index=False)["amount"]
            .sum()
            .rename(columns={"amount": "Invoice Value"})
        )
        customer_paid = (
            invoice_df.groupby("customer_name", as_index=False)["allocated_amount"]
            .sum()
            .rename(columns={"allocated_amount": "Allocated"})
        )
        customer_chart = pd.merge(
            customer_invoice, customer_paid, on="customer_name", how="left"
        ).fillna(0).rename(columns={"customer_name": "Customer"})

        left_top, right_top = st.columns(2, gap="large")

        with left_top:
            with st.container(border=True):
                st.subheader("Invoice & Payment Trend")
                st.caption("Monthly totals based on dates in the uploaded CSV files.")
                if not monthly_chart.empty:
                    st.line_chart(
                        monthly_chart.set_index("Period"),
                        use_container_width=True,
                        height=260
                    )
                else:
                    st.info("Add valid invoice_date and payment_date columns to view this trend.")

        with right_top:
            with st.container(border=True):
                st.subheader("Customer Comparison")
                st.caption("Invoice value compared with allocated payments.")
                if not customer_chart.empty:
                    st.bar_chart(
                        customer_chart.set_index("Customer")[
                            ["Invoice Value", "Allocated"]
                        ],
                        use_container_width=True,
                        height=260
                    )
                else:
                    st.info("Customer comparison will appear after records are loaded.")

        left_bottom, right_bottom = st.columns(2, gap="large")

        with left_bottom:
            with st.container(border=True):
                st.subheader("Outstanding by Customer")
                st.caption("Remaining invoice amount for each customer.")
                outstanding_chart = invoice_df[
                    ["customer_name", "outstanding_amount"]
                ].copy()
                outstanding_chart = outstanding_chart.rename(
                    columns={
                        "customer_name": "Customer",
                        "outstanding_amount": "Outstanding"
                    }
                )
                if not outstanding_chart.empty:
                    st.bar_chart(
                        outstanding_chart.set_index("Customer"),
                        use_container_width=True,
                        height=260
                    )
                else:
                    st.info("No outstanding balances to display.")

        with right_bottom:
            with st.container(border=True):
                st.subheader("Reconciliation Status")
                st.caption("Number of payment transactions in each status.")
                status_chart = pd.DataFrame({
                    "Status": ["Matched", "Partial", "Unmatched", "Needs Review"],
                    "Transactions": [
                        r["summary"]["matched"],
                        r["summary"]["partial"],
                        r["summary"]["unmatched"],
                        r["summary"]["review"]
                    ]
                })
                st.bar_chart(
                    status_chart.set_index("Status"),
                    use_container_width=True,
                    height=260
                )


        # ==================================
        # 3. INVOICE-WISE PAYMENT DETAILS
        # ==================================

        st.divider()

        st.subheader("3. Invoice-wise Payment Details")

        invoice_report = invoice_df.rename(
            columns={
                "invoice_id": "Invoice ID",
                "customer_name": "Customer Name",
                "amount": "Invoice Amount",
                "allocated_amount": "Paid Amount",
                "outstanding_amount": "Pending Amount",
                "status": "Payment Status"
            }
        )

        invoice_columns = [
            "Invoice ID",
            "Customer Name",
            "Invoice Amount",
            "Paid Amount",
            "Pending Amount",
            "Payment Status"
        ]

        invoice_report = invoice_report[
            invoice_columns
        ]

        st.dataframe(
            invoice_report,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Invoice Amount": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Paid Amount": st.column_config.NumberColumn(
                    format="₹%.2f"
                ),
                "Pending Amount": st.column_config.NumberColumn(
                    format="₹%.2f"
                )
            }
        )

        st.download_button(
            "⬇️ Download Invoice Report",
            invoice_report.to_csv(
                index=False
            ).encode("utf-8"),
            "invoice_report.csv",
            "text/csv"
        )

        # ==================================
        # 4. PAYMENT MATCHING DETAILS
        # ==================================

        st.divider()

        st.subheader("4. Payment Matching Details")

        matches = r["matches_df"].copy()

        display_matches = matches.rename(
            columns={
                "transaction_id": "Transaction ID",
                "description": "Payment Description",
                "invoice_id": "Matched Invoice",
                "payment_amount": "Payment Amount",
                "allocated_amount": "Allocated Amount",
                "confidence": "Matching Confidence (%)",
                "status": "Result",
                "evidence": "Matching Explanation"
            }
        )

        display_columns = [
            "Transaction ID",
            "Payment Description",
            "Matched Invoice",
            "Payment Amount",
            "Allocated Amount",
            "Matching Confidence (%)",
            "Result",
            "Matching Explanation"
        ]

        display_columns = [
            col for col in display_columns
            if col in display_matches.columns
        ]

        display_matches = display_matches[
            display_columns
        ]

        st.dataframe(
            display_matches,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Payment Matching Report",
            display_matches.to_csv(
                index=False
            ).encode("utf-8"),
            "payment_matching_report.csv",
            "text/csv"
        )

        # ==================================
        # 5. UNMATCHED PAYMENT DETAILS
        # ==================================

        st.divider()

        st.subheader("5. Unmatched Payments")

        unmatched_df = r["unmatched_payments"].copy()

        if unmatched_df.empty:

            st.success(
                "All payments have been matched or allocated."
            )

        else:

            unmatched_report = unmatched_df.rename(
                columns={
                    "transaction_id": "Transaction ID",
                    "description": "Payment Description",
                    "payment_amount": "Payment Amount",
                    "status": "Payment Status",
                    "evidence": "Reason"
                }
            )

            st.dataframe(
                unmatched_report,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download Unmatched Payments",
                unmatched_report.to_csv(
                    index=False
                ).encode("utf-8"),
                "unmatched_payments.csv",
                "text/csv"
            )

        # ==================================
        # 6. EXCEPTION REPORT
        # ==================================

        st.divider()

        st.subheader("6. Transactions Requiring Attention")

        exceptions = matches[
            ~matches["status"].isin([
                "Matched",
                "Partial"
            ])
        ].copy()

        if exceptions.empty:

            st.success(
                "No transactions require additional attention."
            )

        else:

            st.dataframe(
                exceptions,
                use_container_width=True,
                hide_index=True
            )

        # ==================================
        # 7. DOWNLOAD COMPLETE REPORT
        # ==================================

        st.divider()

        st.subheader("7. Download Complete Report")

        report_buffer = invoice_report.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Download Complete Invoice Report",
            data=report_buffer,
            file_name="reconx_invoice_report.csv",
            mime="text/csv"
        )

        st.caption(
            f"Report generated: {r['run_at']}"
        )

        st.caption(
            "ReconX | Smart Invoice & Payment Reconciliation"
        )
