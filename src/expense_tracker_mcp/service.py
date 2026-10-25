"""Expense domain operations. Kept separate from MCP transport code."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sqlite3

from .database import get_connection
from .formatting import inr_from_paise, markdown_table


def amount_to_paise(amount: float | int | str) -> int:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number.") from None
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    if value > Decimal("1000000000"):
        raise ValueError("Amount is above the supported limit.")
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def normalize_category(category: str) -> str:
    normalized = " ".join(category.strip().lower().split())
    if not normalized:
        raise ValueError("Category is required.")
    if len(normalized) > 60:
        raise ValueError("Category must be 60 characters or fewer.")
    return normalized


def validate_text(value: str, field: str, max_length: int = 500) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} is required.")
    if len(cleaned) > max_length:
        raise ValueError(f"{field} must be {max_length} characters or fewer.")
    return cleaned


def parse_date(value: str | None, field: str = "date") -> date | None:
    if value is None or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f"{field} must use YYYY-MM-DD format.") from None


def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: str | None = None,
) -> dict:
    paise = amount_to_paise(amount)
    category = normalize_category(category)
    description = validate_text(description, "Description")
    day = parse_date(expense_date, "Expense date") or date.today()

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO expenses (amount_paise, category, description, expense_date)
               VALUES (?, ?, ?, ?)""",
            (paise, category, description, day.isoformat()),
        )
        expense_id = cursor.lastrowid

    return {
        "id": expense_id,
        "amount": inr_from_paise(paise),
        "amount_paise": paise,
        "category": category,
        "description": description,
        "expense_date": day.isoformat(),
        "message": "Expense recorded successfully.",
    }


def list_expenses(
    category: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = 20,
) -> dict:
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")
    category = normalize_category(category) if category.strip() else ""
    start = parse_date(start_date, "Start date")
    end = parse_date(end_date, "End date")
    if start and end and start > end:
        raise ValueError("Start date must not be after end date.")

    clauses, params = [], []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if start:
        clauses.append("expense_date >= ?")
        params.append(start.isoformat())
    if end:
        clauses.append("expense_date <= ?")
        params.append(end.isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""SELECT id, amount_paise, category, description, expense_date, created_at
                FROM expenses{where}
                ORDER BY expense_date DESC, id DESC LIMIT ?""",
            [*params, limit],
        ).fetchall()

    result = [
        {
            "id": row["id"],
            "amount": inr_from_paise(row["amount_paise"]),
            "amount_paise": row["amount_paise"],
            "category": row["category"],
            "description": row["description"],
            "expense_date": row["expense_date"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    table = markdown_table(
        ["ID", "Date", "Category", "Description", "Amount"],
        [[r["id"], r["expense_date"], r["category"], r["description"], r["amount"]] for r in result],
    )
    return {"count": len(result), "expenses": result, "table": table}


def update_expense(
    expense_id: int,
    amount: float | None = None,
    category: str = "",
    description: str = "",
    expense_date: str = "",
) -> dict:
    if expense_id < 1:
        raise ValueError("Expense ID must be a positive integer.")
    updates, params = [], []
    if amount is not None:
        updates.append("amount_paise = ?")
        params.append(amount_to_paise(amount))
    if category.strip():
        updates.append("category = ?")
        params.append(normalize_category(category))
    if description.strip():
        updates.append("description = ?")
        params.append(validate_text(description, "Description"))
    if expense_date.strip():
        parsed = parse_date(expense_date, "Expense date")
        updates.append("expense_date = ?")
        params.append(parsed.isoformat())

    if not updates:
        raise ValueError("Provide at least one field to update.")

    params.append(expense_id)
    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        if cursor.rowcount == 0:
            raise ValueError(f"No expense found with ID {expense_id}.")
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()

    return {
        "id": row["id"],
        "amount": inr_from_paise(row["amount_paise"]),
        "category": row["category"],
        "description": row["description"],
        "expense_date": row["expense_date"],
        "message": "Expense updated successfully.",
    }


def delete_expense(expense_id: int) -> dict:
    if expense_id < 1:
        raise ValueError("Expense ID must be a positive integer.")
    with get_connection() as conn:
        row = conn.execute("SELECT id, description FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if row is None:
            raise ValueError(f"No expense found with ID {expense_id}.")
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    return {"id": expense_id, "description": row["description"], "message": "Expense deleted successfully."}


def spending_summary(start_date: str = "", end_date: str = "") -> dict:
    start = parse_date(start_date, "Start date")
    end = parse_date(end_date, "End date")
    if start and end and start > end:
        raise ValueError("Start date must not be after end date.")
    clauses, params = [], []
    if start:
        clauses.append("expense_date >= ?")
        params.append(start.isoformat())
    if end:
        clauses.append("expense_date <= ?")
        params.append(end.isoformat())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""

    with get_connection() as conn:
        rows = conn.execute(
            f"""SELECT category, COUNT(*) AS count, SUM(amount_paise) AS total_paise
                FROM expenses{where}
                GROUP BY category ORDER BY total_paise DESC, category ASC""",
            params,
        ).fetchall()
    total = sum(row["total_paise"] for row in rows)
    output_rows = []
    categories = []
    for row in rows:
        share = (row["total_paise"] / total * 100) if total else 0
        categories.append({
            "category": row["category"],
            "expense_count": row["count"],
            "total": inr_from_paise(row["total_paise"]),
            "total_paise": row["total_paise"],
            "share_percent": round(share, 2),
        })
        output_rows.append([
            row["category"], row["count"], inr_from_paise(row["total_paise"]), f"{share:.2f}%"
        ])
    return {
        "period": {
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
        },
        "grand_total": inr_from_paise(total),
        "expense_count": sum(row["count"] for row in rows),
        "categories": categories,
        "table": markdown_table(["Category", "Transactions", "Total", "Share"], output_rows)
            if output_rows else "No expenses found for this period.",
    }


def monthly_summary(month: str = "") -> dict:
    month = month.strip() or date.today().strftime("%Y-%m")
    try:
        parsed = date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.") from None
    if parsed.strftime("%Y-%m") != month:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.")
    start = parsed.isoformat()
    if parsed.month == 12:
        next_month = date(parsed.year + 1, 1, 1)
    else:
        next_month = date(parsed.year, parsed.month + 1, 1)

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT category, COUNT(*) AS count, SUM(amount_paise) AS total_paise
               FROM expenses WHERE expense_date >= ? AND expense_date < ?
               GROUP BY category ORDER BY total_paise DESC, category""",
            (start, next_month.isoformat()),
        ).fetchall()
    total = sum(row["total_paise"] for row in rows)
    count = sum(row["count"] for row in rows)
    table_rows = [
        [row["category"], row["count"], inr_from_paise(row["total_paise"]),
         f"{(row['total_paise'] / total * 100):.2f}%" if total else "0.00%"]
        for row in rows
    ]
    return {
        "month": month,
        "total": inr_from_paise(total),
        "expense_count": count,
        "average_expense": inr_from_paise(round(total / count)) if count else "₹0.00",
        "categories": [
            {"category": row["category"], "count": row["count"],
             "total": inr_from_paise(row["total_paise"])}
            for row in rows
        ],
        "table": markdown_table(["Category", "Transactions", "Total", "Share"], table_rows)
            if table_rows else f"No expenses recorded for {month}.",
    }


def set_category_budget(category: str, month: str, monthly_limit: float) -> dict:
    category = normalize_category(category)
    if len(month) != 7:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.")
    try:
        parsed = date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.") from None
    if parsed.strftime("%Y-%m") != month:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.")
    limit_paise = amount_to_paise(monthly_limit)

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO budgets(category, month, limit_paise) VALUES (?, ?, ?)
               ON CONFLICT(category, month) DO UPDATE SET limit_paise = excluded.limit_paise""",
            (category, month, limit_paise),
        )
    return {
        "category": category,
        "month": month,
        "monthly_limit": inr_from_paise(limit_paise),
        "message": "Budget saved successfully.",
    }


def budget_status(month: str = "") -> dict:
    month = month.strip() or date.today().strftime("%Y-%m")
    try:
        parsed = date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.") from None
    if parsed.strftime("%Y-%m") != month:
        raise ValueError("Month must use YYYY-MM format, for example 2026-10.")

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT b.category, b.limit_paise,
                      COALESCE(SUM(e.amount_paise), 0) AS spent_paise
               FROM budgets b
               LEFT JOIN expenses e
                 ON e.category = b.category
                AND e.expense_date >= b.month || '-01'
                AND e.expense_date < date(b.month || '-01', '+1 month')
               WHERE b.month = ?
               GROUP BY b.category, b.limit_paise
               ORDER BY b.category""",
            (month,),
        ).fetchall()
    results = []
    table_rows = []
    for row in rows:
        remaining = row["limit_paise"] - row["spent_paise"]
        status = "Over budget" if remaining < 0 else ("At limit" if remaining == 0 else "Within budget")
        results.append({
            "category": row["category"],
            "budget": inr_from_paise(row["limit_paise"]),
            "spent": inr_from_paise(row["spent_paise"]),
            "remaining": inr_from_paise(remaining),
            "status": status,
        })
        table_rows.append([
            row["category"], inr_from_paise(row["limit_paise"]),
            inr_from_paise(row["spent_paise"]), inr_from_paise(remaining), status
        ])
    return {
        "month": month,
        "budgets": results,
        "table": markdown_table(["Category", "Budget", "Spent", "Remaining", "Status"], table_rows)
            if table_rows else f"No budgets configured for {month}.",
    }
