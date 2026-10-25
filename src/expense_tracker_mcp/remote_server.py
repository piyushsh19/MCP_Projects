
"""Remote HTTP entry point for the Expense Tracker MCP server."""
import os

from expense_tracker_mcp.server import mcp


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    mcp.run(
        transport="http",
        host=host,
        port=port,
    )
