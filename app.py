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
from datetime import date
from database import create_table, add_transaction, get_all_transactions, delete_transaction

# ─── APP SETUP ───────────────────────────────────────────────────────────────
create_table()

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

/* ── Login form label colors ── */
.stTextInput label p,
.stTextInput label,
.stForm label,
.stForm label p {
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
# Load credentials from config.yaml
with open("config.yaml", encoding="utf-8") as f:
    auth_config = yaml.load(f, Loader=SafeLoader)

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

# ─── CATEGORIES ──────────────────────────────────────────────────────────────
EXPENSE_CATEGORIES  = ["Bakala", "Rent / EMI", "Send to India", "Transport",
                        "Medical", "Shopping", "Entertainment", "Investments", "Other"]
INCOME_CATEGORIES   = ["Salary", "Freelance", "Business", "Other"]
CREDIT_CATEGORIES   = ["Lent to Friend", "Lent to Family", "Advance Given", "Other"]
# Saving = money set aside; stays with you but in a dedicated pot
SAVING_CATEGORIES   = ["Emergency Fund", "Travel Fund", "Other Savings"]

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
entry_type = st.sidebar.radio("Type", ["Income", "Expense", "Credit", "Saving"])

if entry_type == "Income":
    category = st.sidebar.selectbox("Category", INCOME_CATEGORIES)
elif entry_type == "Credit":
    category = st.sidebar.selectbox("Category", CREDIT_CATEGORIES)
elif entry_type == "Saving":
    category = st.sidebar.selectbox("Category", SAVING_CATEGORIES)
    st.sidebar.caption("Saving = money you set aside (emergency cash, travel fund). It stays with you.")
else:
    category = st.sidebar.selectbox("Category", EXPENSE_CATEGORIES)

amount     = st.sidebar.number_input("Amount (KD)", min_value=0.0, step=1.0, format="%.3f")
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

# ─── LOAD DATA ────────────────────────────────────────────────────────────────
df = get_all_transactions()

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
    "Income":  "#10b981",  # Green
    "Expense": "#ef4444",  # Red
    "Credit":  "#f59e0b",  # Orange
    "Saving":  "#3b82f6",  # Blue
}

# ─── MAIN DASHBOARD ──────────────────────────────────────────────────────────
if df.empty:
    st.info("No entries yet. Add your first entry from the left sidebar!")
else:
    # ── Totals ──
    total_income    = df[df["type"] == "Income"]["amount"].sum()
    total_expense   = df[df["type"] == "Expense"]["amount"].sum()
    total_credit    = df[df["type"] == "Credit"]["amount"].sum()
    total_saving    = df[df["type"] == "Saving"]["amount"].sum()
    emergency_fund  = df[(df["type"] == "Saving") & (df["category"] == "Emergency Fund")]["amount"].sum()
    travel_fund     = df[(df["type"] == "Saving") & (df["category"] == "Travel Fund")]["amount"].sum()
    # Available balance = income minus what was spent, given out, or set aside
    available       = total_income - total_expense - total_credit - total_saving

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

    # ── Row 2 KPIs: Emergency | Travel | Available Balance ──
    r2c1, r2c2, r2c3 = st.columns(3)
    bal_color = "#10b981" if available >= 0 else "#ef4444"
    bal_note  = "Freely available" if available >= 0 else "Overspent"
    with r2c1: st.html(kpi_card("Emergency Fund",    f"KD {emergency_fund:,.3f}", "#3b82f6", "In-hand savings",  inr=to_inr(emergency_fund)))
    with r2c2: st.html(kpi_card("Travel Fund",       f"KD {travel_fund:,.3f}",    "#8b5cf6", "Vacation savings", inr=to_inr(travel_fund)))
    with r2c3: st.html(kpi_card("Available Balance", f"KD {available:,.3f}",      bal_color, bal_note,           inr=to_inr(available)))

    # ── Charts ──
    st.subheader("Charts")
    ch1, ch2 = st.columns(2)

    # Expense pie — warm red/orange palette
    with ch1:
        exp_df = df[df["type"] == "Expense"]
        if not exp_df.empty:
            fig_exp_pie = px.pie(exp_df, names="category", values="amount",
                                 title="Expenses by Category", hole=0.35,
                                 color_discrete_sequence=["#ef4444","#f97316","#eab308",
                                                          "#ec4899","#f43f5e","#fb923c",
                                                          "#fbbf24","#a855f7"])
            fig_exp_pie.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_exp_pie, use_container_width=True)
        else:
            st.info("No expense data for pie chart yet.")

    # Savings pie — cool blue/teal/green palette
    with ch2:
        sav_df = df[df["type"] == "Saving"]
        if not sav_df.empty:
            fig_sav_pie = px.pie(sav_df, names="category", values="amount",
                                 title="Savings Breakdown", hole=0.35,
                                 color_discrete_sequence=["#3b82f6","#8b5cf6","#10b981"])
            fig_sav_pie.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig_sav_pie, use_container_width=True)
        else:
            st.info("No savings data yet.")

    # Bar chart: Income vs Expense vs Credit vs Saving per person
    summary = df.groupby(["person", "type"])["amount"].sum().reset_index()
    fig_bar = px.bar(summary, x="person", y="amount", color="type", barmode="group",
                     title="Income vs Expense vs Credit vs Saving by Person",
                     labels={"amount": "Amount (KD)", "person": "Person"},
                     color_discrete_map=COLOR_MAP)
    fig_bar.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Line chart: over time
    st.subheader("Spending Over Time")
    daily = df.groupby(["date", "type"])["amount"].sum().reset_index()
    fig_line = px.line(daily, x="date", y="amount", color="type", markers=True,
                       title="Daily Income, Expenses, Savings & Credits",
                       labels={"amount": "Amount (KD)", "date": "Date"},
                       color_discrete_map=COLOR_MAP)
    fig_line.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_line, use_container_width=True)

    # ── Monthly Comparison ──────────────────────────────────────────────────
    st.subheader("Monthly Comparison")

    # Convert date column to datetime, extract year-month as string e.g. "2025-03"
    df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

    monthly = df.groupby(["month", "type"])["amount"].sum().reset_index()
    fig_monthly = px.bar(monthly, x="month", y="amount", color="type", barmode="group",
                         title="Monthly Income vs Expense vs Saving vs Credit",
                         labels={"amount": "Amount (KD)", "month": "Month"},
                         color_discrete_map=COLOR_MAP)
    fig_monthly.update_layout(**CHART_LAYOUT)
    st.plotly_chart(fig_monthly, use_container_width=True)

    # Monthly summary table
    monthly_pivot = df.pivot_table(
        index="month", columns="type", values="amount", aggfunc="sum", fill_value=0
    ).reset_index()
    # Add a net column if key columns exist
    for col in ["Income", "Expense", "Credit", "Saving"]:
        if col not in monthly_pivot.columns:
            monthly_pivot[col] = 0.0
    monthly_pivot["Net (Income−Expense−Credit−Saving)"] = (
        monthly_pivot["Income"] - monthly_pivot["Expense"]
        - monthly_pivot["Credit"] - monthly_pivot["Saving"]
    )
    st.dataframe(monthly_pivot.round(3), use_container_width=True, hide_index=True)

    # ── Transactions Table + Filter + Export ────────────────────────────────
    st.subheader("All Transactions")

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_person   = st.selectbox("Filter by Person",   ["All", "Neena", "Shobin"])
    with fc2:
        filter_type     = st.selectbox("Filter by Type",     ["All", "Income", "Expense", "Credit", "Saving"])
    with fc3:
        all_categories  = ["All"] + sorted(df["category"].unique().tolist())
        filter_category = st.selectbox("Filter by Category", all_categories)

    filtered_df = df.copy()
    if filter_person   != "All": filtered_df = filtered_df[filtered_df["person"]   == filter_person]
    if filter_type     != "All": filtered_df = filtered_df[filtered_df["type"]     == filter_type]
    if filter_category != "All": filtered_df = filtered_df[filtered_df["category"] == filter_category]

    st.dataframe(
        filtered_df[["date", "person", "type", "category", "amount", "note"]],
        use_container_width=True, hide_index=True
    )

    # ── Excel Export ────────────────────────────────────────────────────────
    # Create the Excel file in memory (no temp file needed)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtered_df[["date", "person", "type", "category", "amount", "note"]].to_excel(
            writer, index=False, sheet_name="Transactions"
        )

    # Build a descriptive filename based on active filters
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

    # ── Delete Entry ────────────────────────────────────────────────────────
    st.subheader("Delete an Entry")
    if not filtered_df.empty:
        with st.expander("Show table with ID numbers (use ID to delete)"):
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        delete_id = st.number_input("Enter ID to delete", min_value=1, step=1)
        if st.button("Delete Entry", type="secondary"):
            delete_transaction(int(delete_id))
            st.success(f"Entry #{delete_id} deleted.")
            st.rerun()
