"""Formatting helpers for tool responses."""
from __future__ import annotations


def inr_from_paise(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")
    header = "| " + " | ".join(cell(h) for h in headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows]
    return "\n".join([header, separator, *body])
