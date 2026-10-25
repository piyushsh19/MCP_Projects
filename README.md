# Expense Tracker MCP Server

A modular Python MCP server for managing expenses through AI assistants. Built with FastMCP, SQLite, and `uv`.

## Features

- Add, list, update, and delete expenses
- Filter records by category and inclusive date range
- Category-wise spending summary with totals, transaction counts, and percentage shares
- Monthly summary with totals and average transaction amount
- Set monthly category budgets and check remaining budget
- SQLite persistence, input validation, parameterized SQL, and integer-paise currency storage
- MCP Inspector support and automated tests

> This is a local learning project. It is not connected to bank accounts and is not a multi-user financial system.

## Requirements

- Python 3.12+
- `uv`

## Setup

```bash
uv sync
```

The default database is created at `data/expenses.db`. To choose another path, copy `.env.example` to `.env` and set `EXPENSE_DB_PATH`, or export the variable in your shell. The application does not automatically load `.env`; export the variable or add a dotenv loader if you choose to use `.env`.

## Run the server

```bash
uv run python -m expense_tracker_mcp.server
```

## Inspect tools

```bash
uv run fastmcp dev inspector src/expense_tracker_mcp/server.py
```

## Available MCP tools

| Tool | Purpose |
|---|---|
| `add_expense` | Record an expense |
| `list_expenses` | Filter and list records |
| `update_expense` | Update selected fields |
| `delete_expense` | Delete a record by ID |
| `spending_summary` | Category totals and percentage shares in a Markdown table |
| `monthly_summary` | Monthly category breakdown and average expense |
| `set_category_budget` | Create or update a monthly category budget |
| `budget_status` | Compare actual spending against budgets |

Amounts are in INR. Dates use `YYYY-MM-DD`; monthly reports and budgets use `YYYY-MM`.

## Example prompts

- "Record ₹850 for lunch under food today."
- "List my transport expenses for this month."
- "Summarize my spending by category."
- "Show my monthly report for 2026-10."
- "Set a ₹5,000 food budget for 2026-10."
- "Show my budget status for 2026-10."

## Run tests

```bash
uv run pytest
```

## Project structure

```text
src/expense_tracker_mcp/
├── __init__.py
├── database.py    # SQLite connection and schema
├── formatting.py  # Currency and Markdown table helpers
├── service.py     # Business logic and validation
└── server.py      # FastMCP tool registration
tests/
└── test_service.py
```

## Security and limitations

- Local database only; no authentication or per-user access control.
- Deleting an expense is permanent.
- Keep local database files and secrets out of Git.
- Back up the database before experimenting with important records.
- For production deployment, add identity/access control, audit logging, backups, migrations, monitoring, and an appropriate hosted database.
