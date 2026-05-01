"""
app.py
------
Main web app file. Run with:  streamlit run app.py
"""

import io
import yaml
import streamlit as st
import streamlit_authenticator as stauth
import plotly.express as px
import pandas as pd
import requests
from yaml.loader import SafeLoader
from datetime import date, datetime
from database import (create_table, create_budget_table, add_transaction, get_all_transactions,
                      delete_transaction, delete_multiple_transactions,
                      set_budget, get_budgets)

# ─── APP SETUP ───────────────────────────────────────────────────────────────
create_table()
create_budget_table()

st.set_page_config(page_title="SPLIT_WISE", page_icon="💜", layout="wide")

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.html("""
<style>
.stApp { background-color: #0f1117; color: #e2e8f0; }

[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #2d3748; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] label { color: #94a3b8 !important; font-weight: 600; font-size: 0.85rem !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #1e2330 !important; border: 1px solid #374151 !important;
    color: #ffffff !important; border-radius: 6px !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #7c3aed; color: white; border: none; border-radius: 8px;
    font-weight: 700; font-size: 0.95rem; width: 100%; transition: background 0.2s ease;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { background: #6d28d9; }

h2, h3 { color: #e2e8f0 !important; border-bottom: 1px solid #2d3748; padding-bottom: 0.3rem; }
[data-testid="stDataFrame"] { border: 1px solid #2d3748; border-radius: 8px; overflow: hidden; }
[data-testid="stAlert"] { background-color: #1e2330; border-left: 4px solid #7c3aed; color: #e2e8f0; }
[data-testid="stExpander"] { background-color: #161b22; border: 1px solid #2d3748; border-radius: 8px; }

.stButton > button[kind="secondary"] {
    background: transparent; border: 1px solid #ef4444; color: #ef4444;
    border-radius: 8px; transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover { background: #ef4444; color: white; }

.stSelectbox > div > div {
    background-color: #1e2330 !important; border: 1px solid #374151 !important;
    color: #e2e8f0 !important; border-radius: 6px !important;
}
.stRadio > div { gap: 0.5rem; }

/* ── All label text white ── */
.stTextInput label p,
.stTextInput label,
.stForm label,
.stForm label p,
.stNumberInput label,
.stNumberInput label p,
.stSelectbox label,
.stSelectbox label p,
.stRadio label,
.stRadio label p,
.stDateInput label,
.stDateInput label p,
.stCheckbox label,
.stCheckbox label p,
.stCheckbox span {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
}
/* Login form input boxes */
.stTextInput input {
    background-color: #1e2330 !important;
    border: 1px solid #374151 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}
/* Login button */
.stForm .stButton > button {
    background: #7c3aed !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    width: 100% !important;
}
.stForm .stButton > button:hover {
    background: #6d28d9 !important;
}

/* Download button */
[data-testid="stDownloadButton"] > button {
    background: #1e2330; border: 1px solid #374151; color: #e2e8f0;
    border-radius: 8px; transition: all 0.2s ease;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #2d3748; border-color: #10b981; color: #10b981;
}

/* ── MOBILE RESPONSIVE (iPhone Pro Max 14/15 = 430px wide) ── */
@media screen and (max-width: 768px) {

    /* Stack all Streamlit columns vertically */
    [data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        flex: 0 0 100% !important;
    }

    /* Smaller header in banner */
    .stApp h1 { font-size: 1.4rem !important; letter-spacing: 2px !important; }
    .stApp h2, .stApp h3 { font-size: 1rem !important; }

    /* Give sidebar toggle more tap area */
    [data-testid="stSidebarCollapsedControl"] button {
        width: 2.5rem !important;
        height: 2.5rem !important;
    }

    /* Make charts fill full width */
    .js-plotly-plot, .plotly { width: 100% !important; }

    /* Make dataframes scrollable horizontally */
    [data-testid="stDataFrame"] { overflow-x: auto !important; }

    /* Bigger tap targets for buttons on mobile */
    .stButton > button {
        min-height: 2.8rem !important;
        font-size: 1rem !important;
    }

    /* Bigger tap targets for inputs */
    input, select, textarea {
        font-size: 1rem !important;
        min-height: 2.8rem !important;
    }

    /* KPI card — reduce padding on small screen */
    .kpi-card-inner { padding: 0.9rem 1rem !important; }

    /* Remove excess margin around main content */
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 1rem !important;
    }
}
</style>
""")

# ─── AUTHENTICATION ──────────────────────────────────────────────────────────
def _secrets_to_dict(obj):
    """Recursively convert Streamlit secrets AttrDict to a plain Python dict."""
    if hasattr(obj, "items"):
        return {k: _secrets_to_dict(v) for k, v in obj.items()}
    return obj

def load_auth_config():
    """
    Load auth config from Streamlit secrets (Streamlit Cloud deployment)
    or fall back to config.yaml (local development).
    """
    try:
        return {
            "credentials":   _secrets_to_dict(st.secrets["credentials"]),
            "cookie":        _secrets_to_dict(st.secrets["cookie"]),
            "preauthorized": {"emails": []},
        }
    except (KeyError, Exception):
        with open("config.yaml", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)

auth_config = load_auth_config()

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

# Show login form — placed in the centre of the page
name, authentication_status, username = authenticator.login(
    fields={"Form name": "SPLIT_WISE Login", "Username": "Username",
            "Password": "Password", "Login": "Login"},
    location="main"
)

if authentication_status is False:
    st.error("Incorrect username or password.")
    st.stop()          # Stop here — show nothing else

elif authentication_status is None:
    st.info("Please enter your username and password to continue.")
    st.stop()          # Stop here — show nothing else

# ── If we reach here, the user is logged in ──────────────────────────────────
# Show logout button in sidebar
authenticator.logout("Logout", location="sidebar")
st.sidebar.markdown("---")

# ─── LOAD DATA (early — needed for sidebar month filter) ─────────────────────
df = get_all_transactions()
if not df.empty:
    df["month_sort"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
    df["month"]      = pd.to_datetime(df["date"]).dt.strftime("%b %Y")

# ─── CATEGORIES ──────────────────────────────────────────────────────────────
EXPENSE_CATEGORIES  = ["Grocery", "Rent", "Send to India", "Transport",
                        "Medical", "Shopping", "Entertainment",
                        "Loan Repayment", "Credit Card Bill", "Other"]
INCOME_CATEGORIES   = ["Salary", "Freelance", "Business", "Other"]
CREDIT_CATEGORIES   = ["Lent to Friend", "Lent to Family", "Advance Given", "Other"]
# Saving = money set aside; stays with you but in a dedicated pot
SAVING_CATEGORIES   = ["Emergency Fund", "Travel Fund", "Investments", "Chitty", "Other Savings"]
# Debit = money we borrowed that we need to repay
DEBIT_CATEGORIES    = ["Borrowed from Friend", "Loan Taken", "Credit Card Debt", "Other"]
# Withdrawal = taking money OUT of a savings pot (uses same categories so we know which pot was reduced)
WITHDRAWAL_CATEGORIES = SAVING_CATEGORIES

# ─── LIVE EXCHANGE RATE ──────────────────────────────────────────────────────
# open.er-api.com is free, no API key needed, and supports KWD unlike frankfurter.app
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/KWD", timeout=5)
        data = r.json()
        if data.get("result") == "success":
            return data["rates"]   # e.g. {"INR": 272.5, "USD": 3.26, ...}
        return None
    except Exception:
        return None

# ─── HEADER BANNER ───────────────────────────────────────────────────────────
st.html("""
<div style="background:#161b22; border-radius:12px; padding:1.5rem 2rem;
            margin-bottom:1.5rem; border-left:5px solid #7c3aed;
            display:flex; justify-content:space-between; align-items:center;">
    <div>
        <h1 style="color:#ffffff; font-size:2rem; font-weight:800;
                   letter-spacing:4px; margin:0 0 0.2rem 0;">&#128156; SPLIT_WISE</h1>
        <p style="color:#94a3b8; font-size:0.9rem; margin:0;">
            Welcome, <span style="color:#a78bfa; font-weight:600;">SHOBIN &amp; NEENA</span>
        </p>
    </div>
    <div style="text-align:right;">
        <p style="color:#64748b; font-style:italic; font-size:0.85rem; margin:0;">
            &ldquo;A small saving today is a big freedom tomorrow.&rdquo;
        </p>
    </div>
</div>
""")

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("### ✦ ADD NEW ENTRY")

person     = st.sidebar.selectbox("Who are you?", ["Neena", "Shobin"])

# ── Month filter ──────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### ☰ FILTER DASHBOARD")
if not df.empty and "month_sort" in df.columns:
    _month_opts = ["All"] + [datetime.strptime(m, "%Y-%m").strftime("%b %Y")
                              for m in sorted(df["month_sort"].unique().tolist(), reverse=True)]
else:
    _month_opts = ["All"]
sel_month_radio = st.sidebar.radio("Select Month", _month_opts, key="global_month_filter")
st.sidebar.markdown("---")

entry_type = st.sidebar.radio("Type", ["Income", "Expense", "Credit", "Saving", "Withdrawal", "Debit"])

if entry_type == "Income":
    category = st.sidebar.selectbox("Category", INCOME_CATEGORIES)
elif entry_type == "Credit":
    category = st.sidebar.selectbox("Category", CREDIT_CATEGORIES)
elif entry_type == "Saving":
    category = st.sidebar.selectbox("Category", SAVING_CATEGORIES)
    st.sidebar.caption("Saving = money you set aside (emergency cash, travel fund, investments). It stays with you.")
elif entry_type == "Withdrawal":
    category = st.sidebar.selectbox("Category", WITHDRAWAL_CATEGORIES)
    st.sidebar.caption("Withdrawal = taking money OUT of a savings pot. Reduces that pot's balance.")
elif entry_type == "Debit":
    category = st.sidebar.selectbox("Category", DEBIT_CATEGORIES)
else:
    category = st.sidebar.selectbox("Category", EXPENSE_CATEGORIES)

# ── Amount input — KWD or INR for all types ──────────────────────────────────
entry_currency = st.sidebar.radio("Currency", ["KWD", "INR"])
if entry_currency == "INR":
    inr_input = st.sidebar.number_input("Amount (INR ₹)", min_value=0.0, step=100.0, format="%.2f")
    _rates = get_exchange_rates()
    if _rates and inr_input > 0:
        amount = inr_input / _rates["INR"]
        st.sidebar.info(f"Converted: KD {amount:.3f}")
    else:
        amount = 0.0
        if not _rates:
            st.sidebar.warning("Live rate unavailable. Switch to KWD.")
else:
    amount = st.sidebar.number_input("Amount (KD)", min_value=0.0, step=1.0, format="%.3f")

note       = st.sidebar.text_input("Note (optional)", placeholder="e.g. Monthly groceries")
entry_date = st.sidebar.date_input("Date", value=date.today())

if st.sidebar.button("Add Entry", type="primary"):
    if amount <= 0:
        st.sidebar.error("Please enter an amount greater than 0.")
    else:
        add_transaction(person=person, type_=entry_type, category=category,
                        amount=amount, note=note, date=str(entry_date))
        st.sidebar.success(f"{entry_type} of KD {amount:.3f} saved!")
        st.rerun()

# ─── KPI HELPER ──────────────────────────────────────────────────────────────
def kpi_card(label, value, accent, note="", inr=None):
    """
    label  - card title
    value  - main KD amount string
    accent - top border color
    note   - small text below value
    inr    - float amount in KD; if given, shows the INR equivalent
    """
    note_html = f'<p style="color:{accent}; font-size:0.74rem; margin:0.3rem 0 0 0;">{note}</p>' if note else ""
    inr_html  = (f'<p style="color:#64748b; font-size:0.74rem; margin:0.25rem 0 0 0;">'
                 f'≈ ₹{inr:,.0f} INR</p>') if inr is not None else ""
    return f"""
    <div style="background:#1e2330; border-top:4px solid {accent}; border-radius:10px;
                padding:1.2rem 1.4rem; height:100%;">
        <p style="color:#94a3b8; font-size:0.78rem; font-weight:600;
                  text-transform:uppercase; letter-spacing:1px; margin:0 0 0.4rem 0;">{label}</p>
        <p style="color:#ffffff; font-size:1.5rem; font-weight:800; margin:0;">{value}</p>
        {note_html}
        {inr_html}
    </div>"""

# ─── BUDGET KPI CARD ─────────────────────────────────────────────────────────
def budget_kpi_card(label, budget, actual, is_expense=True):
    """
    Shows budget vs actual with colour-coded status.
    is_expense=True  → green when actual < budget (under budget is good)
    is_expense=False → green when actual >= budget (hitting target is good)
    """
    if budget == 0:
        border    = "#374151"
        status_html = '<p style="color:#64748b;font-size:0.78rem;margin:0.3rem 0 0 0;">No budget set</p>'
        pct_str   = ""
    else:
        pct = actual / budget * 100
        if is_expense:
            good    = actual <= budget
            diff_kd = budget - actual
            sign    = "✓" if good else "⚠"
            label_d = "under budget" if good else "over budget"
        else:
            good    = actual >= budget
            diff_kd = actual - budget
            sign    = "✓" if good else "⚠"
            label_d = "above target" if good else "below target"
        border      = "#10b981" if good else "#ef4444"
        clr         = "#10b981" if good else "#ef4444"
        pct_clr     = "#10b981" if good else "#ef4444"
        pct_str     = f'<span style="color:{pct_clr};margin-left:0.4rem;">({pct:.0f}%)</span>'
        status_html = (f'<p style="color:{clr};font-size:0.78rem;margin:0.3rem 0 0 0;">'
                       f'{sign} KD {abs(diff_kd):,.3f} {label_d}</p>')
    return f"""
    <div style="background:#1e2330;border-top:4px solid {border};border-radius:10px;
                padding:1.2rem 1.4rem;height:100%;">
        <p style="color:#94a3b8;font-size:0.78rem;font-weight:600;
                  text-transform:uppercase;letter-spacing:1px;margin:0 0 0.4rem 0;">{label}</p>
        <p style="color:#ffffff;font-size:1.4rem;font-weight:800;margin:0;">KD {actual:,.3f}</p>
        <p style="color:#64748b;font-size:0.76rem;margin:0.2rem 0 0 0;">
            Budget: KD {budget:,.3f}{pct_str}</p>
        {status_html}
    </div>"""

# ─── CHART LAYOUT (dark theme) ───────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor="#161b22", plot_bgcolor="#161b22",
    font=dict(color="#ffffff"),
    title_font=dict(color="#e2e8f0", size=14),
    legend=dict(bgcolor="#1e2330", bordercolor="#2d3748", borderwidth=1, font=dict(color="#ffffff")),
    xaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#94a3b8"),
               gridcolor="#2d3748", linecolor="#374151"),
    yaxis=dict(tickfont=dict(color="#ffffff"), title_font=dict(color="#94a3b8"),
               gridcolor="#2d3748", linecolor="#374151"),
)

COLOR_MAP = {
    "Income":     "#10b981",  # Emerald green
    "Expense":    "#f97316",  # Orange
    "Credit":     "#eab308",  # Yellow
    "Saving":     "#3b82f6",  # Blue
    "Withdrawal": "#ec4899",  # Pink
    "Debit":      "#7c3aed",  # Purple
}

# ─── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if df.empty:
    st.info("No entries yet. Add your first entry from the left sidebar!")
else:
    # ── Apply month filter from sidebar radio ─────────────────────────────────
    if sel_month_radio == "All":
        fdf = df.copy()
        sel_months = []
    else:
        _ms = datetime.strptime(sel_month_radio, "%b %Y").strftime("%Y-%m")
        fdf = df[df["month_sort"] == _ms].copy()
        sel_months = [sel_month_radio]

    # ── Period totals — correctly filtered by month ───────────────────────────
    total_income      = fdf[fdf["type"] == "Income"]["amount"].sum()
    total_expense     = fdf[fdf["type"] == "Expense"]["amount"].sum()
    total_credit      = fdf[fdf["type"] == "Credit"]["amount"].sum()
    period_saving     = fdf[fdf["type"] == "Saving"]["amount"].sum()
    period_withdrawal = fdf[fdf["type"] == "Withdrawal"]["amount"].sum()
    # Savings reduce available balance — money set aside is no longer freely spendable
    available         = total_income - total_expense - total_credit - period_saving + period_withdrawal

    # ── Cumulative balances — always from FULL dataset, never month-filtered ──
    # Debt and savings are running balances like a bank account. Filtering by
    # month makes them wrong: debt from January disappears in a March filter.
    def _pot_all(category_name):
        saved = df[(df["type"] == "Saving")     & (df["category"] == category_name)]["amount"].sum()
        taken = df[(df["type"] == "Withdrawal") & (df["category"] == category_name)]["amount"].sum()
        return max(saved - taken, 0)

    emergency_fund   = _pot_all("Emergency Fund")
    travel_fund      = _pot_all("Travel Fund")
    investment_total = _pot_all("Investments")
    net_savings      = max(df[df["type"] == "Saving"]["amount"].sum()
                           - df[df["type"] == "Withdrawal"]["amount"].sum(), 0)
    outstanding_debt = (df[df["type"] == "Debit"]["amount"].sum()
                        - df[(df["type"] == "Expense") & (df["category"] == "Loan Repayment")]["amount"].sum()
                        - df[(df["type"] == "Expense") & (df["category"] == "Credit Card Bill")]["amount"].sum())

    # ── Fetch live rates once — used across all KPI cards ──
    rates   = get_exchange_rates()
    inr_rate = rates["INR"] if rates else None   # e.g. 272.5

    def to_inr(kd_amount):
        """Returns INR float if rate available, else None (card won't show INR line)."""
        return kd_amount * inr_rate if inr_rate else None

    # ── Rate banner ──
    st.subheader("Summary")
    if inr_rate:
        st.caption(f"Live rate (updated hourly):  1 KD = ₹{inr_rate:,.2f} INR  |  1 KD = ${rates['USD']:.4f} USD  (Source: open.er-api.com)")
    else:
        st.warning("Could not fetch live rates — showing KD amounts only. Check your internet connection.")

    # ── Row 1 KPIs: Income | Expenses | Credits ──
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1: st.html(kpi_card("Total Income",      f"KD {total_income:,.3f}",  "#10b981", inr=to_inr(total_income)))
    with r1c2: st.html(kpi_card("Total Expenses",    f"KD {total_expense:,.3f}", "#ef4444", inr=to_inr(total_expense)))
    with r1c3: st.html(kpi_card("Credits Given Out", f"KD {total_credit:,.3f}",  "#f59e0b", "To be returned", inr=to_inr(total_credit)))

    st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)

    # ── Row 2 KPIs: Emergency | Travel | Investments | Total Savings ──
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1: st.html(kpi_card("Emergency Fund",    f"KD {emergency_fund:,.3f}",   "#3b82f6", "In-hand savings",  inr=to_inr(emergency_fund)))
    with r2c2: st.html(kpi_card("Travel Fund",       f"KD {travel_fund:,.3f}",      "#8b5cf6", "Vacation savings", inr=to_inr(travel_fund)))
    with r2c3: st.html(kpi_card("Total Investments", f"KD {investment_total:,.3f}", "#0d9488", "Invested savings", inr=to_inr(investment_total)))
    with r2c4: st.html(kpi_card("Total Savings",     f"KD {net_savings:,.3f}",      "#06b6d4", "All pots combined", inr=to_inr(net_savings)))

    st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)

    # ── Row 3 KPIs: Available Balance | Outstanding Debt ──
    r3c1, r3c2 = st.columns(2)
    bal_color  = "#10b981" if available >= 0 else "#ef4444"
    bal_note   = "Freely available" if available >= 0 else "Overspent"
    debt_note  = "Debt Free!" if outstanding_debt <= 0 else f"KD {outstanding_debt:,.3f} remaining"
    debt_inr   = to_inr(max(outstanding_debt, 0))
    with r3c1: st.html(kpi_card("Available Balance", f"KD {available:,.3f}",         bal_color, bal_note, inr=to_inr(available)))
    with r3c2: st.html(kpi_card("Outstanding Debt",  f"KD {max(outstanding_debt,0):,.3f}", "#ef4444", debt_note, inr=debt_inr))

    # ── Charts ──
    st.subheader("Charts")
    ch1, ch2 = st.columns(2)

    # Expense pie — warm red/orange palette
    with ch1:
        exp_df = fdf[fdf["type"] == "Expense"]
        if not exp_df.empty:
            fig_exp_pie = px.pie(exp_df, names="category", values="amount",
                                 title="Expenses by Category", hole=0.35,
                                 color_discrete_sequence=["#f97316","#ef4444","#eab308",
                                                          "#a855f7","#ec4899","#14b8a6",
                                                          "#fb923c","#6366f1"])
            fig_exp_pie.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_exp_pie, use_container_width=True)
        else:
            st.info("No expense data for pie chart yet.")

    # Savings pie — net per pot (Saving minus Withdrawals), matching KPI cards
    with ch2:
        pot_rows = [{"category": cat, "amount": _pot_all(cat)} for cat in SAVING_CATEGORIES]
        sav_net_df = pd.DataFrame(pot_rows)
        sav_net_df = sav_net_df[sav_net_df["amount"] > 0]
        if not sav_net_df.empty:
            fig_sav_pie = px.pie(sav_net_df, names="category", values="amount",
                                 title="Net Savings by Pot (after Withdrawals)", hole=0.35,
                                 color_discrete_sequence=["#3b82f6","#8b5cf6","#10b981","#06b6d4","#0d9488"])
            fig_sav_pie.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_sav_pie, use_container_width=True)
        else:
            st.info("No savings data yet.")

    # Line chart: over time
    st.subheader("Spending Over Time")
    daily = fdf.groupby(["date", "type"])["amount"].sum().reset_index()
    fig_line = px.line(daily, x="date", y="amount", color="type", markers=True,
                       title="Daily Income, Expenses, Savings & Credits",
                       labels={"amount": "Amount (KD)", "date": "Date"},
                       color_discrete_map=COLOR_MAP)
    fig_line.update_layout(**CHART_LAYOUT)
    fig_line.update_xaxes(tickformat="%b %d")
    st.plotly_chart(fig_line, use_container_width=True)

    # ── Monthly Comparison ──────────────────────────────────────────────────
    st.subheader("Monthly Comparison")

    monthly_raw          = fdf.groupby(["month_sort", "month", "type"])["amount"].sum().reset_index()
    monthly_non_sav_debt = monthly_raw[~monthly_raw["type"].isin(["Saving", "Withdrawal", "Debit"])].copy()
    sav_m  = monthly_raw[monthly_raw["type"] == "Saving"].set_index(["month_sort", "month"])["amount"]
    wdr_m  = monthly_raw[monthly_raw["type"] == "Withdrawal"].set_index(["month_sort", "month"])["amount"]
    dbt_m  = monthly_raw[monthly_raw["type"] == "Debit"].set_index(["month_sort", "month"])["amount"]
    repay_m = fdf[fdf["category"].isin(["Loan Repayment", "Credit Card Bill"])].groupby(["month_sort", "month"])["amount"].sum()
    all_months = monthly_raw[["month_sort", "month"]].drop_duplicates()
    net_sav_m = [
        {"month_sort": r["month_sort"], "month": r["month"], "type": "Net Saving",
         "amount": max(sav_m.get((r["month_sort"], r["month"]), 0)
                       - wdr_m.get((r["month_sort"], r["month"]), 0), 0)}
        for _, r in all_months.iterrows()
    ]
    net_dbt_m = [
        {"month_sort": r["month_sort"], "month": r["month"], "type": "Net Debt",
         "amount": max(dbt_m.get((r["month_sort"], r["month"]), 0)
                       - repay_m.get((r["month_sort"], r["month"]), 0), 0)}
        for _, r in all_months.iterrows()
    ]
    monthly = pd.concat([monthly_non_sav_debt, pd.DataFrame(net_sav_m), pd.DataFrame(net_dbt_m)], ignore_index=True)
    monthly = monthly.sort_values("month_sort")
    monthly_color_map = {**COLOR_MAP, "Net Saving": "#3b82f6", "Net Debt": "#dc2626"}
    fig_monthly = px.bar(monthly, x="month", y="amount", color="type", barmode="group",
                         title="Monthly Income vs Expense vs Net Saving vs Net Debt",
                         labels={"amount": "Amount (KD)", "month": "Month"},
                         color_discrete_map=monthly_color_map)
    fig_monthly.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Monthly summary table
    monthly_pivot = fdf.pivot_table(
        index="month_sort", columns="type", values="amount", aggfunc="sum", fill_value=0
    ).reset_index().rename(columns={"month_sort": "month"})
    for col in ["Income", "Expense", "Credit", "Saving", "Withdrawal", "Debit"]:
        if col not in monthly_pivot.columns:
            monthly_pivot[col] = 0.0
    monthly_pivot["Net Saving (Saving−Withdrawal)"] = (
        monthly_pivot["Saving"] - monthly_pivot["Withdrawal"]
    ).clip(lower=0)
    monthly_pivot["Net (Income−Expense−Credit)"] = (
        monthly_pivot["Income"] - monthly_pivot["Expense"] - monthly_pivot["Credit"]
    )
    st.dataframe(monthly_pivot.round(3), use_container_width=True, hide_index=True)

    # ── Transactions Table + Filter + Export ────────────────────────────────
    with st.expander(f"All Transactions ({len(fdf)} rows — click to expand)", expanded=False):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            filter_person   = st.selectbox("Filter by Person",   ["All", "Neena", "Shobin"])
        with fc2:
            filter_type     = st.selectbox("Filter by Type",     ["All", "Income", "Expense", "Credit", "Saving", "Withdrawal", "Debit"])
        with fc3:
            all_categories  = ["All"] + sorted(fdf["category"].unique().tolist())
            filter_category = st.selectbox("Filter by Category", all_categories)

        filtered_df = fdf.copy()
        if filter_person   != "All": filtered_df = filtered_df[filtered_df["person"]   == filter_person]
        if filter_type     != "All": filtered_df = filtered_df[filtered_df["type"]     == filter_type]
        if filter_category != "All": filtered_df = filtered_df[filtered_df["category"] == filter_category]

        st.dataframe(
            filtered_df[["date", "person", "type", "category", "amount", "note"]],
            use_container_width=True, hide_index=True
        )

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            filtered_df[["date", "person", "type", "category", "amount", "note"]].to_excel(
                writer, index=False, sheet_name="Transactions"
            )
        fname_parts = []
        if filter_category != "All": fname_parts.append(filter_category.replace(" ", "_"))
        if filter_type     != "All": fname_parts.append(filter_type)
        if filter_person   != "All": fname_parts.append(filter_person)
        filename = ("_".join(fname_parts) if fname_parts else "All_Transactions") + ".xlsx"
        st.download_button(
            label=f"Download as Excel  ({len(filtered_df)} rows)",
            data=excel_buffer.getvalue(),
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # filtered_df needed for delete section — default to full fdf if expander not opened
    try:
        filtered_df
    except NameError:
        filtered_df = fdf.copy()
        filter_person = filter_type = filter_category = "All"

    # ── Delete Entry ────────────────────────────────────────────────────────
    st.subheader("Delete an Entry")
    if not filtered_df.empty:
        with st.expander("Show table with ID numbers (use ID to delete)"):
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        # ── Option 1: Delete a single row by ID ──────────────────────────
        st.markdown("**Option 1 — Delete single row by ID**")
        del1, del2 = st.columns([3, 1])
        with del1:
            delete_id = st.number_input("Enter ID", min_value=1, step=1, key="del_single_id")
        with del2:
            st.markdown("<div style='margin-top:1.85rem'></div>", unsafe_allow_html=True)
            if st.button("Delete Row", type="secondary", key="del_single_btn"):
                delete_transaction(int(delete_id))
                st.success(f"Entry #{delete_id} deleted.")
                st.rerun()

        st.markdown("---")

        # ── Option 2: Delete multiple specific rows ───────────────────────
        st.markdown("**Option 2 — Delete specific rows (pick multiple)**")
        id_options = [
            f"ID {row['id']} | {row['person']} | {row['type']} | {row['category']} | KD {row['amount']:.3f}"
            for _, row in filtered_df.iterrows()
        ]
        selected_labels = st.multiselect("Select rows to delete", id_options, key="del_multi_select")
        if selected_labels:
            selected_ids = [int(lbl.split(" | ")[0].replace("ID ", "")) for lbl in selected_labels]
            if st.button(f"Delete {len(selected_ids)} Selected Row(s)", type="secondary", key="del_multi_btn"):
                delete_multiple_transactions(selected_ids)
                st.success(f"{len(selected_ids)} row(s) deleted.")
                st.rerun()

        st.markdown("---")

        # ── Option 3: Delete ALL filtered rows ───────────────────────────
        st.markdown("**Option 3 — Delete ALL filtered rows**")
        n = len(filtered_df)
        confirm_all = st.checkbox(f"Confirm — I want to delete all {n} filtered row(s)", key="del_all_confirm")
        if confirm_all:
            if st.button(f"Delete All {n} Filtered Row(s)", type="secondary", key="del_all_btn"):
                ids = filtered_df["id"].tolist()
                delete_multiple_transactions([int(i) for i in ids])
                st.success(f"{n} row(s) deleted.")
                st.rerun()

    # ── MONTHLY BUDGET ──────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Monthly Budget")

    BUDGET_CATS = ["Income", "Grocery", "Send to India", "Medical",
                   "Shopping", "Entertainment", "Other Expense", "Savings"]

    # Build month list: all months that have data + current month
    all_data_months = sorted(df["month_sort"].unique().tolist(), reverse=True) if not df.empty else []
    current_month_str = datetime.today().strftime("%Y-%m")
    if current_month_str not in all_data_months:
        all_data_months.insert(0, current_month_str)

    # Auto-link to global filter when exactly 1 month is selected
    if len(sel_months) == 1:
        selected_bm = datetime.strptime(sel_months[0], "%b %Y").strftime("%Y-%m")
        st.caption(f"Budget month auto-set to **{sel_months[0]}** from the sidebar filter.")
    else:
        bm_col, _ = st.columns([2, 4])
        with bm_col:
            selected_bm = st.selectbox(
                "Select Month",
                all_data_months,
                format_func=lambda m: datetime.strptime(m, "%Y-%m").strftime("%b %Y"),
                key="budget_month_sel"
            )

    sel_month_label = datetime.strptime(selected_bm, "%Y-%m").strftime("%b %Y")
    existing = get_budgets(selected_bm)

    # ── Budget input form ──
    with st.expander(f"Set / Edit Budget for {sel_month_label}", expanded=not bool(existing)):
        with st.form("budget_form_main"):
            st.markdown(f"**Monthly budget targets for {sel_month_label} (KD)**")
            bc1, bc2 = st.columns(2)
            budget_inputs = {}
            for i, cat in enumerate(BUDGET_CATS):
                with (bc1 if i % 2 == 0 else bc2):
                    budget_inputs[cat] = st.number_input(
                        cat,
                        min_value=0.0,
                        value=float(existing.get(cat, 0.0)),
                        step=10.0,
                        format="%.3f",
                        key=f"bgt_{cat}"
                    )
            if st.form_submit_button("Save Budget", type="primary"):
                for cat, amt in budget_inputs.items():
                    set_budget(selected_bm, cat, amt)
                st.success(f"Budget for {sel_month_label} saved!")
                st.rerun()

    # ── Actuals for selected budget month (always from full dataset, not global filter) ──
    mdf = df[df["month_sort"] == selected_bm] if (not df.empty and "month_sort" in df.columns) else pd.DataFrame()

    def actual_for(cat):
        if mdf.empty:
            return 0.0
        if cat == "Income":
            return float(mdf[mdf["type"] == "Income"]["amount"].sum())
        if cat == "Savings":
            s = mdf[mdf["type"] == "Saving"]["amount"].sum()
            w = mdf[mdf["type"] == "Withdrawal"]["amount"].sum()
            return float(max(s - w, 0))
        if cat == "Other Expense":
            return float(mdf[(mdf["type"] == "Expense") & (mdf["category"] == "Other")]["amount"].sum())
        return float(mdf[(mdf["type"] == "Expense") & (mdf["category"] == cat)]["amount"].sum())

    # ── Budget KPI cards ──
    st.markdown(f"#### Budget vs Actual — {sel_month_label}")

    bk1, bk2, bk3, bk4 = st.columns(4)
    with bk1: st.html(budget_kpi_card("Income",        existing.get("Income", 0),        actual_for("Income"),        is_expense=False))
    with bk2: st.html(budget_kpi_card("Grocery",       existing.get("Grocery", 0),       actual_for("Grocery"),       is_expense=True))
    with bk3: st.html(budget_kpi_card("Send to India", existing.get("Send to India", 0), actual_for("Send to India"), is_expense=True))
    with bk4: st.html(budget_kpi_card("Medical",       existing.get("Medical", 0),       actual_for("Medical"),       is_expense=True))

    st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)

    bk5, bk6, bk7, bk8 = st.columns(4)
    with bk5: st.html(budget_kpi_card("Shopping",      existing.get("Shopping", 0),      actual_for("Shopping"),      is_expense=True))
    with bk6: st.html(budget_kpi_card("Entertainment", existing.get("Entertainment", 0), actual_for("Entertainment"), is_expense=True))
    with bk7: st.html(budget_kpi_card("Other Expense", existing.get("Other Expense", 0), actual_for("Other Expense"), is_expense=True))
    with bk8: st.html(budget_kpi_card("Savings",       existing.get("Savings", 0),       actual_for("Savings"),       is_expense=False))

    # ── Budget vs Actual bar chart ──
    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
    chart_rows = []
    for cat in BUDGET_CATS:
        chart_rows.append({"Category": cat, "Amount": existing.get(cat, 0.0), "Series": "Budget"})
        chart_rows.append({"Category": cat, "Amount": actual_for(cat),        "Series": "Actual"})
    bdf = pd.DataFrame(chart_rows)
    if bdf["Amount"].sum() > 0:
        fig_budget = px.bar(
            bdf, x="Category", y="Amount", color="Series", barmode="group",
            title=f"Budget vs Actual — {sel_month_label}",
            labels={"Amount": "Amount (KD)"},
            color_discrete_map={"Budget": "#374151", "Actual": "#7c3aed"}
        )
        fig_budget.update_layout(**CHART_LAYOUT)
        st.plotly_chart(fig_budget, use_container_width=True)
    else:
        st.info("Set a budget above to see the Budget vs Actual chart.")
