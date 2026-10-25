from datetime import date

import pytest

from expense_tracker_mcp import database, service


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db_file = tmp_path / "test_expenses.db"
    monkeypatch.setenv("EXPENSE_DB_PATH", str(db_file))
    database.initialize_database()


def test_add_list_and_summary():
    created = service.add_expense(850, " Food ", "Lunch", date.today().isoformat())
    assert created["category"] == "food"
    assert created["amount_paise"] == 85000

    listed = service.list_expenses(category="food")
    assert listed["count"] == 1
    assert listed["expenses"][0]["description"] == "Lunch"

    summary = service.spending_summary()
    assert summary["expense_count"] == 1
    assert summary["grand_total"] == "₹850.00"
    assert "food" in summary["table"]


def test_reject_non_positive_amount():
    with pytest.raises(ValueError):
        service.add_expense(0, "food", "Lunch")


def test_update_and_delete():
    created = service.add_expense(100, "food", "Snack")
    updated = service.update_expense(created["id"], amount=125, description="Updated snack")
    assert updated["amount"] == "₹125.00"
    deleted = service.delete_expense(created["id"])
    assert deleted["id"] == created["id"]
    assert service.list_expenses()["count"] == 0


def test_budget_status():
    month = date.today().strftime("%Y-%m")
    service.add_expense(250, "transport", "Metro")
    service.set_category_budget("transport", month, 1000)
    result = service.budget_status(month)
    assert result["budgets"][0]["status"] == "Within budget"
    assert result["budgets"][0]["spent"] == "₹250.00"
