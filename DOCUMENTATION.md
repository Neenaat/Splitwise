# SPLIT_WISE — Complete Project Documentation

**Project:** Family Expense Tracker Web App
**Built for:** Neena & Shobin
**Currency:** Kuwaiti Dinar (KWD) with live INR conversion
**Last updated:** March 2026 (v3.0)

---

## Table of Contents

1. [What is SPLIT_WISE?](#1-what-is-split_wise)
2. [Technology Stack — What We Used and Why](#2-technology-stack)
3. [Project Folder Structure](#3-project-folder-structure)
4. [Step 1 — Setting Up the Project Locally](#4-step-1--setting-up-the-project-locally)
5. [Step 2 — The Database Layer (database.py)](#5-step-2--the-database-layer)
6. [Step 3 — Password & Login System](#6-step-3--password--login-system)
7. [Step 4 — The Main App (app.py)](#7-step-4--the-main-app)
8. [Step 5 — Pushing Code to GitHub](#8-step-5--pushing-code-to-github)
9. [Step 6 — Setting Up Supabase (Cloud Database)](#9-step-6--setting-up-supabase-cloud-database)
10. [Step 7 — Deploying on Streamlit Community Cloud](#10-step-7--deploying-on-streamlit-community-cloud)
11. [Security Checklist](#11-security-checklist)
12. [How to Make Changes in the Future](#12-how-to-make-changes-in-the-future)
13. [Troubleshooting Common Errors](#13-troubleshooting-common-errors)

---

## 1. What is SPLIT_WISE?

SPLIT_WISE is a private, password-protected family finance dashboard built entirely in Python. It lets Neena and Shobin:

- Record **Income**, **Expense**, **Credit** (money lent out), **Saving**, **Withdrawal** (from savings), and **Debit** (money borrowed)
- Enter amounts in **KWD or INR** — INR is auto-converted to KWD at the live rate before saving
- See all amounts in **Kuwaiti Dinar (KWD)** with live **INR conversion** on every KPI card
- View interactive **charts** — pie charts, bar charts, line graphs, monthly comparison
- **Filter** transactions by person, type, or category
- **Export** filtered data to Excel
- **Delete** entries — single row by ID, multiple specific rows, or all filtered rows at once
- Access the app from **any device** (mobile + desktop) simultaneously

---

## 2. Technology Stack

### What We Used and Why

| Tool | What it is | Why we chose it |
|------|-----------|-----------------|
| **Python** | Programming language | User wanted Python only |
| **Streamlit** | Web app framework | Turns Python scripts into web apps with no HTML/JS knowledge needed |
| **SQLite** | Local database (file-based) | Zero setup — just a file on your computer. Used for local development |
| **PostgreSQL / Supabase** | Cloud database | Used when the app is hosted online so data persists and is shared between users |
| **Plotly Express** | Charts library | Beautiful interactive charts with one line of Python |
| **Pandas** | Data tables | Reads database results into tables, does filtering and grouping |
| **streamlit-authenticator** | Login/password system | Handles login forms and bcrypt password checking |
| **bcrypt** | Password hashing | Converts plain passwords into irreversible hash codes so no one can read them |
| **PyYAML** | Read config files | Reads the `config.yaml` credentials file |
| **openpyxl** | Excel files | Needed by Pandas to write `.xlsx` files |
| **requests** | HTTP calls | Fetches live exchange rates from the internet |
| **open.er-api.com** | Exchange rate API | Free, no API key, supports KWD (Frankfurter.app does NOT support KWD) |

### How the pieces connect

```
Browser (you)
     ↓
Streamlit (app.py)          ← Python web framework
     ↓
streamlit-authenticator     ← Checks your username/password
     ↓
database.py                 ← Reads/writes transactions
     ↓
SQLite (local) OR Supabase (hosted)
```

---

## 3. Project Folder Structure

```
Split_Wise/
│
├── app.py                      ← Main web app — run this to start
├── database.py                 ← All database read/write logic
├── requirements.txt            ← List of Python packages to install
├── generate_passwords.py       ← One-time tool to create password hashes
├── DOCUMENTATION.md            ← This file
├── .gitignore                  ← Tells Git which files to NOT upload to GitHub
│
├── config.yaml                 ← [SECRET] Login credentials (NOT on GitHub)
│
├── .streamlit/
│   └── secrets.toml            ← [SECRET] Supabase URL + cloud credentials (NOT on GitHub)
│
├── venv/                       ← [LOCAL ONLY] Virtual environment (NOT on GitHub)
└── splitwise.db                ← [LOCAL ONLY] SQLite database file (NOT on GitHub)
```

### What goes to GitHub vs what stays local

| File | On GitHub? | Reason |
|------|-----------|--------|
| `app.py` | YES | Safe — no secrets inside |
| `database.py` | YES | Safe — no secrets inside |
| `requirements.txt` | YES | Safe — just package names |
| `generate_passwords.py` | YES | Safe — placeholder passwords only |
| `DOCUMENTATION.md` | YES | Safe — no secrets |
| `.gitignore` | YES | Safe — just rules |
| `config.yaml` | **NO** | Contains password hashes and cookie key |
| `.streamlit/secrets.toml` | **NO** | Contains Supabase URL and credentials |
| `splitwise.db` | **NO** | Your real financial data |
| `venv/` | **NO** | Huge folder — anyone can reinstall with pip |

---

## 4. Step 1 — Setting Up the Project Locally

### 4.1 Install Python

Download Python from python.org. Make sure to tick "Add Python to PATH" during installation.

### 4.2 Create the project folder

```
C:\Users\Lenovo\Documents\Split_Wise\
```

### 4.3 Create a Virtual Environment

A virtual environment is an isolated Python installation just for this project. This means packages installed here don't interfere with other Python projects.

```powershell
# Open PowerShell, navigate to the project folder
cd "C:\Users\Lenovo\Documents\Split_Wise"

# Create the virtual environment
python -m venv venv

# Activate it (you must do this every time you open a new terminal)
.\venv\Scripts\activate

# If PowerShell blocks it, run this once first:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

When activated, your terminal prompt shows `(venv)` at the start.

### 4.4 Install all required packages

```powershell
pip install -r requirements.txt
```

This installs everything listed in `requirements.txt` into your virtual environment.

### 4.5 Run the app locally

```powershell
streamlit run app.py
```

This opens the app in your browser at `http://localhost:8501`

---

## 5. Step 2 — The Database Layer

**File:** `database.py`

### What it does

This file handles all reading and writing of transaction data. The rest of the app never talks to the database directly — it always goes through these functions.

### Dual Database Design

The app automatically switches between two database systems:

```
Is DATABASE_URL set in secrets?
         ↓
    YES → Use Supabase (PostgreSQL) — for hosted/cloud use
    NO  → Use SQLite local file (splitwise.db) — for local development
```

```python
# This is how the detection works in database.py
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]
    USE_POSTGRES = True
except:
    USE_POSTGRES = False
```

### Key difference: SQL placeholder syntax

SQLite and PostgreSQL use different syntax for inserting values:

| Database | Placeholder syntax |
|----------|--------------------|
| SQLite | `?` |
| PostgreSQL | `%s` |

Our code handles this automatically.

### Functions in database.py

| Function | What it does |
|----------|-------------|
| `create_table()` | Creates the transactions table if it doesn't exist. Called once at app startup |
| `add_transaction(person, type_, category, amount, note, date)` | Inserts one new row |
| `get_all_transactions()` | Returns all rows as a Pandas DataFrame |
| `delete_transaction(id)` | Deletes one row by its ID number |
| `delete_multiple_transactions(ids)` | Deletes a list of rows by their ID numbers in a single query |

### The transactions table structure

| Column | Type | Example |
|--------|------|---------|
| `id` | Auto-number | 1, 2, 3... |
| `person` | Text | "Neena" or "Shobin" |
| `type` | Text | "Income", "Expense", "Credit", "Saving", "Withdrawal", "Debit" |
| `category` | Text | "Salary", "Grocery", "Emergency Fund"... |
| `amount` | Decimal | 125.500 (always stored in KWD) |
| `note` | Text | "Monthly groceries" |
| `date` | Text | "2026-03-14" |

---

## 6. Step 3 — Password & Login System

### Why we need password hashing

You must NEVER store plain passwords like `"Cool@2026"` in any file. If someone reads the file, they immediately know the password. Instead, we store a **hash** — a scrambled one-way code.

Example:
```
Plain password:  Secure@2026
Stored hash:     $2b$12$sr7wy/aRead8Q.vsXwAG9OD/RepywAv5...
```

The hash cannot be reversed back to `Secure@2026`. When you log in, bcrypt hashes what you typed and compares it to the stored hash.

### Step-by-step: How to set or change passwords

**Step 1:** Open `generate_passwords.py` and type your new password:
```python
NEENA_PASSWORD  = "YourNewPassword"
SHOBIN_PASSWORD = "YourNewPassword"
```

**Step 2:** Run it:
```powershell
python generate_passwords.py
```

**Step 3:** It prints two hashes. Copy them into `config.yaml`:
```yaml
credentials:
  usernames:
    neena:
      password: $2b$12$PASTE_NEENA_HASH_HERE
    shobin:
      password: $2b$12$PASTE_SHOBIN_HASH_HERE
```

**Step 4:** Also update `.streamlit/secrets.toml` with the same hashes.

**Step 5:** On Streamlit Cloud, go to App Settings → Secrets and update the hashes there too.

**IMPORTANT:** After pasting the hashes, clear the plain password from `generate_passwords.py` (replace with `"your_password_here"`) before committing to GitHub.

### How the login system works in app.py

```python
# 1. Load credentials from secrets (cloud) or config.yaml (local)
auth_config = load_auth_config()

# 2. Create the authenticator object
authenticator = stauth.Authenticate(
    auth_config["credentials"],      # usernames and hashed passwords
    auth_config["cookie"]["name"],   # cookie name stored in browser
    auth_config["cookie"]["key"],    # secret key to sign the cookie
    auth_config["cookie"]["expiry_days"],  # how long to stay logged in
)

# 3. Show the login form
name, authentication_status, username = authenticator.login(...)

# 4. Block the app if not logged in
if authentication_status is False:
    st.error("Incorrect username or password.")
    st.stop()   # stops the rest of the app from loading
elif authentication_status is None:
    st.info("Please enter your username and password.")
    st.stop()   # stops the rest of the app from loading
```

### config.yaml structure

```yaml
credentials:
  usernames:
    neena:                           ← this is the username to type at login
      name: Neena                    ← display name (shown after login)
      email: neena@example.com       ← not used for login, just metadata
      password: $2b$12$...           ← bcrypt hash of the password
    shobin:
      name: Shobin
      email: shobin@example.com
      password: $2b$12$...

cookie:
  name: splitwise_auth               ← name of the browser cookie
  key: SplitWise_ShoNee_2024_...    ← secret key to sign the cookie (keep private)
  expiry_days: 30                    ← stay logged in for 30 days
```

---

## 7. Step 4 — The Main App

**File:** `app.py`

### App structure (top to bottom)

```
1.  Imports
2.  create_table() — ensure DB exists
3.  st.set_page_config() — browser tab title and layout
4.  CSS injection — dark theme, mobile responsive styles, white label fix
5.  Authentication — login gate (reads secrets or config.yaml)
6.  Category lists
7.  Exchange rate fetch (cached 1 hour)
8.  Header banner (SPLIT_WISE logo + welcome + quote)
9.  Sidebar — Add New Entry form (type, category, KWD/INR currency, amount, note, date)
10. Load all data from database
11. KPI cards (8 cards in 3 rows)
12. Charts (expense pie, savings pie, bar by person, line over time, monthly bar)
13. Monthly comparison table
14. Transactions table with filters
15. Excel export button
16. Delete entry section (3 options)
```

### The 6 transaction types

| Type | What it means | Example |
|------|--------------|---------|
| **Income** | Money coming in | Salary, freelance payment |
| **Expense** | Money spent | Grocery, rent, medical |
| **Credit** | Money lent out | Lent to a friend — to be returned |
| **Saving** | Money set aside into a pot | Emergency Fund, Travel Fund, Investments |
| **Withdrawal** | Taking money OUT of a savings pot | Reducing Emergency Fund balance |
| **Debit** | Money borrowed that must be repaid | Loan taken, credit card debt |

### Categories

```python
EXPENSE_CATEGORIES  = ["Grocery", "Rent", "Send to India", "Transport",
                        "Medical", "Shopping", "Entertainment",
                        "Loan Repayment", "Credit Card Bill", "Other"]

INCOME_CATEGORIES   = ["Salary", "Freelance", "Business", "Other"]

CREDIT_CATEGORIES   = ["Lent to Friend", "Lent to Family", "Advance Given", "Other"]

SAVING_CATEGORIES   = ["Emergency Fund", "Travel Fund", "Investments", "Chitty", "Other Savings"]

WITHDRAWAL_CATEGORIES = SAVING_CATEGORIES   # same pots — picks which one to reduce

DEBIT_CATEGORIES    = ["Borrowed from Friend", "Loan Taken", "Credit Card Debt", "Other"]
```

### Entering amounts in INR

Every entry type has a "Currency" radio: **KWD** or **INR**.

- If you pick **KWD** → enter the amount directly in Kuwaiti Dinar
- If you pick **INR** → enter the rupee amount → app fetches live rate → shows converted KD value → saves in KWD

All amounts are **always stored in KWD** in the database. INR conversion is only at entry time and for display on KPI cards.

### The 8 KPI Cards (3 rows)

**Row 1 — Money flow:**
| Card | Border | Formula |
|------|--------|---------|
| Total Income | Green | Sum of all Income entries |
| Total Expenses | Red | Sum of all Expense entries |
| Credits Given Out | Orange | Sum of all Credit entries ("To be returned") |

**Row 2 — Savings pots (all show net = saved − withdrawn):**
| Card | Border | Formula |
|------|--------|---------|
| Emergency Fund | Blue | Saving(Emergency Fund) − Withdrawal(Emergency Fund) |
| Travel Fund | Purple | Saving(Travel Fund) − Withdrawal(Travel Fund) |
| Total Investments | Teal | Saving(Investments) − Withdrawal(Investments) |
| Total Savings | Cyan | All Saving entries − All Withdrawal entries |

**Row 3 — Financial position:**
| Card | Border | Formula |
|------|--------|---------|
| Available Balance | Green/Red | Income − Expenses − Credits |
| Outstanding Debt | Red | Total Debit − Loan Repayment expenses − Credit Card Bill expenses |

> **Note:** Savings do NOT reduce Available Balance — savings money stays with you, just in a dedicated pot.

### Available Balance formula

```
Available = Income − Expenses − Credits Given Out
```

Savings are excluded because saving money stays with you — it's not spent, just set aside.

### Outstanding Debt formula

```
Outstanding Debt = Total Debit entries
                 − Expense entries in "Loan Repayment" category
                 − Expense entries in "Credit Card Bill" category
```

When Outstanding Debt reaches zero or less, the card shows **"Debt Free!"**

### Delete options (3 ways)

**Option 1 — Single row by ID:**
Enter the ID number → click "Delete Row"

**Option 2 — Multiple specific rows:**
A multiselect dropdown shows every row in the filtered table with details like:
`ID 5 | Neena | Expense | Grocery | KD 10.500`
Pick any number of rows → click "Delete X Selected Row(s)"

**Option 3 — All filtered rows:**
Tick the confirmation checkbox → click "Delete All X Filtered Row(s)"
Use the filter dropdowns above (Person, Type, Category) to narrow down what gets deleted.

### Live Currency Conversion

```python
@st.cache_data(ttl=3600)   # cache for 1 hour so we don't spam the API
def get_exchange_rates():
    r = requests.get("https://open.er-api.com/v6/latest/KWD", timeout=5)
    return r.json()["rates"]   # returns {"INR": 272.5, "USD": 3.26, ...}
```

- We use `open.er-api.com` (free, no API key, supports KWD)
- `@st.cache_data(ttl=3600)` means the rate is fetched once and reused for 1 hour
- If the internet is unavailable, cards show KWD only (no crash)
- INR entry conversion in sidebar also uses this same cached rate

### Charts

| Chart | Type | What it shows |
|-------|------|---------------|
| Expenses by Category | Donut pie | Which expense categories cost most (raw expense amounts) |
| Net Savings by Pot | Donut pie | Remaining balance per savings pot after withdrawals (matches KPI cards) |
| By Person | Grouped bar | Income, Expense, Credit, **Net Saving**, **Net Debt** for Neena vs Shobin |
| Over Time | Line | Daily totals per type (x-axis: "Mar 14" format) |
| Monthly Comparison | Grouped bar | Month-by-month with **Net Saving** and **Net Debt** (x-axis: "Mar 2026" format) |

### Why charts show "Net Saving" and "Net Debt" instead of raw values

The dashboard uses **net values** in charts so they always match the KPI cards.

**Net Saving** = Total Saving entries − Total Withdrawal entries (per person / per month)
- Prevents the chart from showing inflated savings that ignore withdrawals
- Matches the "Total Savings" and individual pot KPI cards exactly

**Net Debt** = Total Debit entries − Loan Repayment expenses − Credit Card Bill expenses (per person / per month)
- Shows outstanding debt, not just what was borrowed
- Matches the "Outstanding Debt" KPI card exactly

**Example:**
```
You borrowed: KD 100   (Debit entry)
You repaid:   KD 30    (Expense → Loan Repayment)

KPI card shows:  Outstanding Debt = KD 70
Chart bar shows: Net Debt = KD 70     ← same number, consistent
```

Without this fix, the chart would show KD 100 while the KPI shows KD 70 — confusing and wrong.

The same logic applies to savings:
```
You saved:     KD 200 into Emergency Fund   (Saving entry)
You withdrew:  KD 50 from Emergency Fund    (Withdrawal entry)

KPI card shows:  Emergency Fund = KD 150
Pie chart shows: Emergency Fund = KD 150    ← same number, consistent
```

### Secrets loading (cloud vs local)

```python
def load_auth_config():
    try:
        # Streamlit Cloud: reads from App Settings → Secrets
        return {
            "credentials": _secrets_to_dict(st.secrets["credentials"]),
            "cookie":       _secrets_to_dict(st.secrets["cookie"]),
            ...
        }
    except:
        # Local development: reads from config.yaml
        with open("config.yaml", encoding="utf-8") as f:
            return yaml.load(f, Loader=SafeLoader)
```

---

## 8. Step 5 — Pushing Code to GitHub

### Why GitHub?

- Keeps a backup of your code
- Streamlit Cloud needs to read your code from GitHub to deploy it
- Tracks all changes with commit history

### One-time setup

```powershell
cd "C:\Users\Lenovo\Documents\Split_Wise"

git init
git add app.py database.py requirements.txt generate_passwords.py .gitignore DOCUMENTATION.md
git commit -m "Initial commit - SPLIT_WISE family expense tracker"
git branch -M main
git remote add origin https://github.com/Neenaat/Splitwise.git
git push -u origin main           # requires PAT token as password
```

### Personal Access Token (PAT)

GitHub no longer accepts passwords in the terminal. You need a PAT:

1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate new token → tick "repo" → copy the token
3. Use it as your password when Git asks:
   ```
   Username: Neenaat
   Password: ghp_yourTokenHere
   ```

### Pushing future changes

```powershell
git add app.py                    # stage the changed file
git commit -m "Describe what changed"
git push                          # push to GitHub
```

If push is rejected (remote has newer changes):
```powershell
git pull --rebase
git push
```

### What the .gitignore file does

The `.gitignore` file lists files that Git should never track or upload:

```
venv/                    ← huge, anyone can reinstall it
splitwise.db             ← your real financial data
.streamlit/secrets.toml  ← Supabase URL and credentials
config.yaml              ← password hashes and cookie key
__pycache__/             ← Python cache files
*.pyc                    ← compiled Python files
.env                     ← environment variables
```

---

## 9. Step 6 — Setting Up Supabase (Cloud Database)

### Why Supabase?

When the app runs locally, data is stored in `splitwise.db` (a file on your laptop). But when it runs on Streamlit Cloud, there is no persistent filesystem — every deployment starts fresh. We need a real cloud database.

Supabase is a free PostgreSQL database hosted in the cloud.

### Step-by-step setup

**Step 1:** Go to supabase.com → Sign up (free)

**Step 2:** Click "New Project" → name it `splitwise` → set a strong database password → Create

**Step 3:** Once created, go to:
```
Settings → Database → Connection string → URI
```
Copy the URI that looks like:
```
postgresql://postgres:YourPassword@db.abcdefgh.supabase.co:5432/postgres
```

**Step 4:** Paste it into `.streamlit/secrets.toml`:
```toml
DATABASE_URL = "postgresql://postgres:YourPassword@db.abcdefgh.supabase.co:5432/postgres"
```

**Step 5:** Also add it to Streamlit Cloud → App Settings → Secrets (see next section)

### How database.py uses it

```python
try:
    DATABASE_URL = st.secrets["DATABASE_URL"]   # found → use Supabase
    USE_POSTGRES = True
except:
    USE_POSTGRES = False                         # not found → use local SQLite
```

The table is created automatically on first run (`create_table()` is called at the top of `app.py`).

---

## 10. Step 7 — Deploying on Streamlit Community Cloud

### What is Streamlit Community Cloud?

Free hosting for Streamlit apps. It reads your code from GitHub and runs it on their servers. URL format: `https://yourapp.streamlit.app`

### Step-by-step deployment

**Step 1:** Go to share.streamlit.io → Sign in with your GitHub account (Neenaat)

**Step 2:** Click "New app"

**Step 3:** Fill in:
- Repository: `Neenaat/Splitwise`
- Branch: `main`
- Main file path: `app.py`

**Step 4:** Click "Advanced settings" → "Secrets" → paste the full contents of your `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://postgres:YourPassword@db.abcdefgh.supabase.co:5432/postgres"

[credentials.usernames.neena]
name     = "Neena"
email    = "neena@example.com"
password = "$2b$12$PASTE_NEENA_HASH_HERE"

[credentials.usernames.shobin]
name     = "Shobin"
email    = "shobin@example.com"
password = "$2b$12$PASTE_SHOBIN_HASH_HERE"

[cookie]
name        = "splitwise_auth"
key         = "PASTE_YOUR_COOKIE_SECRET_KEY_HERE"
expiry_days = 30
```

**Step 5:** Click "Deploy"

Streamlit Cloud will:
1. Pull your code from GitHub
2. Install packages from `requirements.txt`
3. Run `app.py`
4. Give you a public URL

### Updating the hosted app

Every time you push code to GitHub, Streamlit Cloud automatically redeploys. If it shows an old error after a push, go to **Manage app → Reboot app**.

---

## 11. Security Checklist

| Item | Status | Notes |
|------|--------|-------|
| Passwords stored as bcrypt hashes | DONE | Irreversible one-way hash |
| config.yaml not on GitHub | DONE | In .gitignore |
| secrets.toml not on GitHub | DONE | In .gitignore |
| splitwise.db not on GitHub | DONE | In .gitignore |
| Plain passwords not in any committed file | DONE | generate_passwords.py has placeholders only |
| Old password removed from git history | DONE | git filter-branch rewrote all commits; force-pushed |
| App requires login to view any data | DONE | st.stop() blocks unauthenticated access |
| Cookie signed with secret key | DONE | key in config.yaml / secrets |
| Supabase URL kept in secrets only | DONE | Never hardcoded in app.py |
| SQL queries use parameterized inputs | DONE | No SQL injection risk |

### What "bcrypt hash" means

A bcrypt hash like `$2b$12$sr7wy/aRead8Q.vsXwAG9OD/...` contains:

- `$2b$` — algorithm version
- `$12$` — cost factor (how many times it's hashed — higher = slower = harder to crack)
- The remaining characters — the scrambled hash

Nobody can reverse this back to `Secure@2026`. Even if someone reads `config.yaml`, they cannot log in without knowing the original password.

---

## 12. How to Make Changes in the Future

### Change a password

1. Open `generate_passwords.py`, set your new password, run it
2. Copy the printed hash into `config.yaml`
3. Copy same hash into `.streamlit/secrets.toml`
4. Update Streamlit Cloud → App Settings → Secrets
5. Clear the plain password from `generate_passwords.py`

### Add a new expense category

Open `app.py`, find `EXPENSE_CATEGORIES` and add your category:

```python
EXPENSE_CATEGORIES = ["Grocery", "Rent", ..., "Your New Category"]
```

Then push: `git add app.py && git commit -m "Add new category" && git push`

### Add a new savings pot

Add it to `SAVING_CATEGORIES` in `app.py`. Since `WITHDRAWAL_CATEGORIES = SAVING_CATEGORIES`, it automatically appears in both Saving and Withdrawal dropdowns. If you want its own KPI card, add a new `_pot("Your Pot Name")` calculation and a new `st.html(kpi_card(...))` in the dashboard section.

### Add a new person (a third user)

1. Add them to `config.yaml` with a bcrypt hash
2. Add them to `.streamlit/secrets.toml`
3. Update Streamlit Cloud secrets
4. In `app.py`, update the person selectbox:
   ```python
   person = st.sidebar.selectbox("Who are you?", ["Neena", "Shobin", "NewPerson"])
   ```

### Remove a secret accidentally committed to GitHub

If you ever accidentally commit a password or secret to GitHub, follow these steps immediately:

**Step 1:** Change the password immediately (even before cleaning git). An exposed password must be treated as compromised.

**Step 2:** Rewrite git history to remove it from all commits:
```powershell
# Replace "secret_value" with the text you want removed
git filter-branch --force --tree-filter 'python -c "
import os
f = \"filename.py\"
if os.path.exists(f):
    with open(f, encoding=\"utf-8\", errors=\"ignore\") as r: content = r.read()
    content = content.replace(\"secret_value\", \"placeholder\")
    with open(f, \"w\", encoding=\"utf-8\") as w: w.write(content)
"' --tag-name-filter cat -- --all
```

**Step 3:** Remove git's backup of the old history:
```powershell
git for-each-ref --format="%(refname)" refs/original/ | xargs -I {} git update-ref -d {}
git reflog expire --expire=now --all
git gc --prune=now
```

**Step 4:** Force push to GitHub:
```powershell
git push origin main --force
```

> This is exactly what was done in March 2026 to remove `Cool@2026` from the initial commit.

### Run locally after a break

```powershell
cd "C:\Users\Lenovo\Documents\Split_Wise"
.\venv\Scripts\activate
streamlit run app.py
```

---

## 13. Troubleshooting Common Errors

### "streamlit is not recognized"
The virtual environment is not activated.
```powershell
.\venv\Scripts\activate
```

### "ModuleNotFoundError: No module named 'X'"
A package is not installed.
```powershell
pip install -r requirements.txt
```

### "UnicodeDecodeError" when loading config.yaml
The file has special characters. Make sure `open()` uses `encoding="utf-8"`.

### "Incorrect username or password" on login
The password hash in `config.yaml` doesn't match what you typed. Re-run `generate_passwords.py` and update `config.yaml`.

### venv activation blocked in PowerShell
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Live exchange rate not showing
Either the internet is unavailable or the API is down. The app continues working — KWD amounts show but without INR conversion.

### GitHub push asks for password and fails
GitHub no longer accepts account passwords in terminal. Use a Personal Access Token (PAT) instead.

### GitHub push rejected ("fetch first")
The remote has a newer commit. Pull first:
```powershell
git pull --rebase
git push
```

### Streamlit Cloud shows "ImportError" or old error after a push
Streamlit Cloud may be showing a cached error. Go to:
**Manage app (bottom right) → Reboot app**
This forces it to pull the latest code from GitHub and restart fresh.

### Streamlit Cloud shows "Secrets not found" error
The app is trying to read `st.secrets["credentials"]` but you haven't added secrets yet. Go to your app on share.streamlit.io → Settings → Secrets and paste your `secrets.toml` contents.

---

---

### What changed in each version

| Version | Changes |
|---------|---------|
| v1.0 | Initial app — Income, Expense, Credit types; SQLite + Supabase; login system |
| v2.0 | Added Saving, Withdrawal, Debit types; 8 KPI cards; INR entry for all types; multi-row delete; monthly chart format; CSS label fix; Grocery rename |
| v3.0 | Fixed charts to show Net Saving and Net Debt matching KPI cards; savings pie shows net per pot; old password removed from git history |

*End of documentation — SPLIT_WISE v3.0*
