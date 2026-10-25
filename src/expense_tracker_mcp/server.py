"""FastMCP tool definitions for the Expense Tracker."""
from fastmcp import FastMCP

from .database import initialize_database
from . import service

mcp = FastMCP(
    name="Expense Tracker",
    instructions=(
        "Manage a user's local expense records. Use add_expense to record a transaction, "
        "list_expenses to review records, spending_summary or monthly_summary for analytics, "
        "and budget tools to track monthly category limits. Amounts are in INR."
    ),
)


@mcp.tool()
def add_expense(
    amount: float,
    category: str,
    description: str,
    expense_date: str = "",
) -> dict:
    """Record an expense. Amount is in INR and date must be YYYY-MM-DD if supplied."""
    return service.add_expense(amount, category, description, expense_date)


@mcp.tool()
def list_expenses(
    category: str = "",
    start_date: str = "",
    end_date: str = "",
    limit: int = 20,
) -> dict:
    """List expenses with optional category/date filters. Returns records and a Markdown table."""
    return service.list_expenses(category, start_date, end_date, limit)


@mcp.tool()
def update_expense(
    expense_id: int,
    amount: float | None = None,
    category: str = "",
    description: str = "",
    expense_date: str = "",
) -> dict:
    """Update supplied fields on an existing expense; leave other fields empty/omitted."""
    return service.update_expense(expense_id, amount, category, description, expense_date)


@mcp.tool()
def delete_expense(expense_id: int) -> dict:
    """Permanently delete an expense by ID. Confirm the ID with the user before deletion."""
    return service.delete_expense(expense_id)


@mcp.tool()
def spending_summary(start_date: str = "", end_date: str = "") -> dict:
    """Summarize spending by category, including totals, transaction counts and percentage shares."""
    return service.spending_summary(start_date, end_date)


@mcp.tool()
def monthly_summary(month: str = "") -> dict:
    """Summarize a month using YYYY-MM, defaulting to the current month."""
    return service.monthly_summary(month)


@mcp.tool()
def set_category_budget(category: str, month: str, monthly_limit: float) -> dict:
    """Create or replace a category budget. Month is YYYY-MM and limit is in INR."""
    return service.set_category_budget(category, month, monthly_limit)


@mcp.tool()
def budget_status(month: str = "") -> dict:
    """Compare monthly category budgets with actual spending; defaults to the current month."""
    return service.budget_status(month)


initialize_database()

if __name__ == "__main__":
    mcp.run()
