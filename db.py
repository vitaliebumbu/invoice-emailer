import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")

STAGE_10_DEPOSIT = "10% Deposit"
STAGE_50_CABINET_DEPOSIT = "50% Cabinet Deposit"
STAGE_CAB_REMAINING_INSTALL = "Cabinet Remaining Balance + 50% Install"
STAGE_CAB_REMAINING = "Cabinet Remaining Balance"
STAGE_FINAL_INVOICE = "Final Invoice"

ALL_STAGES = [
    STAGE_10_DEPOSIT,
    STAGE_50_CABINET_DEPOSIT,
    STAGE_CAB_REMAINING_INSTALL,
    STAGE_CAB_REMAINING,
    STAGE_FINAL_INVOICE,
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        try:
            conn.execute("SELECT project_name FROM invoice_emails LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute("DROP TABLE IF EXISTS invoice_emails")
            conn.execute("DROP TABLE IF EXISTS projects")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_emails (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT NOT NULL DEFAULT '',
                project_name TEXT NOT NULL,
                stage        TEXT NOT NULL,
                amount       REAL NOT NULL DEFAULT 0,
                pdf_filename TEXT NOT NULL,
                sent_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        columns = {
            row["name"]: row
            for row in conn.execute("PRAGMA table_info(invoice_emails)").fetchall()
        }
        if "project_code" not in columns:
            conn.execute("ALTER TABLE invoice_emails ADD COLUMN project_code TEXT NOT NULL DEFAULT ''")
        if "amount" not in columns:
            conn.execute("ALTER TABLE invoice_emails ADD COLUMN amount REAL NOT NULL DEFAULT 0")
        conn.commit()


def log_invoice_email(project_name, stage, pdf_filename, project_code=""):
    with get_conn() as conn:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(invoice_emails)").fetchall()
        }

        insert_columns = ["project_name", "stage", "pdf_filename"]
        values = [project_name, stage, pdf_filename]

        if "project_code" in columns:
            insert_columns.insert(0, "project_code")
            values.insert(0, project_code or "")
        if "amount" in columns:
            insert_columns.append("amount")
            values.append(0)

        placeholders = ", ".join("?" for _ in insert_columns)
        conn.execute(
            f"INSERT INTO invoice_emails ({', '.join(insert_columns)}) VALUES ({placeholders})",
            values,
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
