import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")

STAGE_10_DEPOSIT     = "10% Deposit"
STAGE_50_DEPOSIT     = "50% Deposit"
STAGE_REMAINING      = "Remaining Balance"
STAGE_CAB_INSTALL    = "Cabinet Balance + 50% Install"
STAGE_REMAINING_INST = "Remaining Install"

ALL_STAGES = [
    STAGE_10_DEPOSIT,
    STAGE_50_DEPOSIT,
    STAGE_REMAINING,
    STAGE_CAB_INSTALL,
    STAGE_REMAINING_INST,
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        # Drop old schema if it doesn't match
        try:
            conn.execute("SELECT project_name FROM invoice_emails LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("DROP TABLE IF EXISTS invoice_emails")
            conn.execute("DROP TABLE IF EXISTS projects")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_emails (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                stage        TEXT NOT NULL,
                pdf_filename TEXT NOT NULL,
                sent_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def log_invoice_email(project_name, stage, pdf_filename):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO invoice_emails (project_name, stage, pdf_filename) VALUES (?, ?, ?)",
            (project_name, stage, pdf_filename),
        )
        conn.commit()


def get_recent_invoices(limit=30):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM invoice_emails ORDER BY sent_at DESC LIMIT ?", (limit,)
        ).fetchall()


def get_invoices_for_project(project_name):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM invoice_emails WHERE project_name = ? ORDER BY sent_at DESC",
            (project_name,),
        ).fetchall()
