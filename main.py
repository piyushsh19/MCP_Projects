
from datetime import date
from pathlib import Path
import sqlite3

from fastmcp import FastMCP

mcp = FastMCP("Expense Tracker")

DB_PATH = Path(__file__).parent / "expenses.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                expense_date TEXT NOT NULL
            )
        """)


@mcp.tool()
def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: str = "",
) -> dict:
    """Record an expense. Amount must be positive."""

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    category = category.strip().lower()
    description = description.strip()

    if not category or not description:
        raise ValueError("Category and description are required.")

    day = date.fromisoformat(expense_date) if expense_date else date.today()
    expense_day = day.isoformat()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO expenses
                (amount, category, description, expense_date)
            VALUES (?, ?, ?, ?)
            """,
            (amount, category, description, expense_day),
        )
        expense_id = cursor.lastrowid

    return {
        "id": expense_id,
        "amount": amount,
        "category": category,
        "description": description,
        "expense_date": expense_day,
        "message": "Expense recorded successfully.",
    }


@mcp.tool()
def list_expenses(category: str = "", limit: int = 20) -> list[dict]:
    """List recent expenses, optionally filtered by category."""

    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    with get_connection() as conn:
        if category.strip():
            rows = conn.execute(
                """
                SELECT * FROM expenses
                WHERE category = ?
                ORDER BY expense_date DESC, id DESC
                LIMIT ?
                """,
                (category.strip().lower(), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM expenses
                ORDER BY expense_date DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

    return [dict(row) for row in rows]


@mcp.tool()
def get_total_spending(
    category: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    """Calculate spending within an inclusive date range."""

    start = date.fromisoformat(start_date) if start_date else None
    end = date.fromisoformat(end_date) if end_date else None

    if start and end and start > end:
        raise ValueError("Start date must not be after end date.")

    conditions = []
    params = []

    if category.strip():
        conditions.append("category = ?")
        params.append(category.strip().lower())

    if start:
        conditions.append("expense_date >= ?")
        params.append(start.isoformat())

    if end:
        conditions.append("expense_date <= ?")
        params.append(end.isoformat())

    where = " WHERE " + " AND ".join(conditions) if conditions else ""

    with get_connection() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) AS count, "
            f"COALESCE(SUM(amount), 0) AS total "
            f"FROM expenses{where}",
            params,
        ).fetchone()

    return {
        "category": category.strip().lower() or "all",
        "expense_count": row["count"],
        "total": round(row["total"], 2),
        "currency": "INR",
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
    }


initialize_database()

if __name__ == "__main__":
    mcp.run()