"""
database.py
-----------
Handles all data storage.

LOCAL  (on your computer): uses SQLite — a single file called splitwise.db
HOSTED (on Streamlit Cloud): uses PostgreSQL — a free cloud database from Supabase

How it decides which one to use:
  - If DATABASE_URL is set in Streamlit secrets → use PostgreSQL
  - Otherwise → use SQLite (local file)
"""

import os
import sqlite3
import pandas as pd
import streamlit as st


# ─── DETECT ENVIRONMENT ──────────────────────────────────────────────────────
# st.secrets is where Streamlit Cloud stores your secret keys safely.
# When running locally, this will just be empty, so we fall back to SQLite.
def _get_database_url():
    try:
        return st.secrets["DATABASE_URL"]   # Set this in Streamlit Cloud secrets
    except Exception:
        return None

DATABASE_URL = _get_database_url()
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    import psycopg2

# ─── CONNECTION ───────────────────────────────────────────────────────────────
def get_connection():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect("splitwise.db")

# ─── CREATE TABLE ─────────────────────────────────────────────────────────────
def create_table():
    conn = get_connection()
    if USE_POSTGRES:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id       SERIAL PRIMARY KEY,
                person   TEXT NOT NULL,
                type     TEXT NOT NULL,
                category TEXT NOT NULL,
                amount   REAL NOT NULL,
                note     TEXT,
                date     TEXT NOT NULL
            )
        """)
        conn.commit()
        cur.close()
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                person   TEXT NOT NULL,
                type     TEXT NOT NULL,
                category TEXT NOT NULL,
                amount   REAL NOT NULL,
                note     TEXT,
                date     TEXT NOT NULL
            )
        """)
        conn.commit()
    conn.close()

# ─── ADD TRANSACTION ──────────────────────────────────────────────────────────
def add_transaction(person, type_, category, amount, note, date):
    conn = get_connection()
    if USE_POSTGRES:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transactions (person, type, category, amount, note, date) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (person, type_, category, amount, note, date)
        )
        conn.commit()
        cur.close()
    else:
        conn.execute(
            "INSERT INTO transactions (person, type, category, amount, note, date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (person, type_, category, amount, note, date)
        )
        conn.commit()
    conn.close()

# ─── GET ALL TRANSACTIONS ─────────────────────────────────────────────────────
def get_all_transactions():
    conn = get_connection()
    if USE_POSTGRES:
        df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    return df

# ─── DELETE TRANSACTION ───────────────────────────────────────────────────────
def delete_transaction(transaction_id):
    conn = get_connection()
    if USE_POSTGRES:
        cur = conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
        conn.commit()
        cur.close()
    else:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
    conn.close()

# ─── DELETE MULTIPLE TRANSACTIONS ─────────────────────────────────────────────
def delete_multiple_transactions(ids: list):
    if not ids:
        return
    conn = get_connection()
    if USE_POSTGRES:
        cur = conn.cursor()
        cur.execute(
            f"DELETE FROM transactions WHERE id IN ({','.join(['%s'] * len(ids))})",
            ids
        )
        conn.commit()
        cur.close()
    else:
        conn.execute(
            f"DELETE FROM transactions WHERE id IN ({','.join(['?'] * len(ids))})",
            ids
        )
        conn.commit()
    conn.close()
