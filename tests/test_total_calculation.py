"""
test_total_calculation.py — FR-4 Total Amount Calculation Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests verifying:
  - Total calculation on empty database equals 0.00
  - Total calculation on multiple expense items accurately sums values
  - Total calculation updates dynamically and accurately after deletion
  - Floating-point decimal arithmetic precision handling (avoiding IEEE 754 float drift)

Covers: FR-4
"""

import pytest
from conftest import http_get, http_post, http_delete, create_expense


def _calculate_total_from_api():
    """
    Helper function to query GET /api/expenses and compute the total sum
    of all active expenses rounded to 2 decimal places.
    """
    status, _, expenses = http_get("/api/expenses")
    assert status == 200, f"Expected 200, got {status}"
    total = sum(e["amount"] for e in expenses)
    return round(total, 2)


def test_total_empty_database_is_zero():
    """
    FR-4 Scenario: Total amount with zero records.
    Given there are no recorded expenses,
    Then the calculated total of all expenses is 0.0.
    """
    status, _, expenses = http_get("/api/expenses")
    assert status == 200
    assert len(expenses) == 0

    total = sum(e["amount"] for e in expenses)
    assert total == 0.0, f"Expected total 0.0, got {total}"


def test_total_sum_multiple_expenses():
    """
    FR-4 Scenario: Dynamic total calculation for multiple expenses.
    Given expenses: $20.00 and $30.50,
    Then total is $50.50.
    When user adds a new expense of $10.25,
    Then total is $60.75.
    """
    # Add initial expenses
    create_expense("User 1", 20.00, "Food")
    create_expense("User 2", 30.50, "Travel")

    assert _calculate_total_from_api() == 50.50

    # Add third expense
    create_expense("User 3", 10.25, "Shopping")
    assert _calculate_total_from_api() == 60.75


def test_total_after_deletion():
    """
    FR-4 Scenario: Dynamic total recalculation on deletion.
    Given expenses: $20.00, $30.50, and $10.25 (Total: $60.75),
    When user deletes the $20.00 expense,
    Then total updates to $40.75.
    """
    e1 = create_expense("Delete Target", 20.00, "Food")
    create_expense("Keep 1", 30.50, "Travel")
    create_expense("Keep 2", 10.25, "Shopping")

    assert _calculate_total_from_api() == 60.75

    # Delete the $20.00 expense
    del_status, _, del_body = http_delete(f"/api/expenses/{e1['id']}")
    assert del_status == 200
    assert del_body.get("success") is True

    # Recalculate
    assert _calculate_total_from_api() == 40.75


def test_total_floating_point_precision():
    """
    FR-4 / Edge: Verify floating-point addition (e.g., 0.10 + 0.20 = 0.30)
    does not suffer from IEEE 754 precision inaccuracies when summed and rounded.
    """
    create_expense("Float User 1", 0.10, "Food")
    create_expense("Float User 2", 0.20, "Food")
    create_expense("Float User 3", 0.30, "Food")

    total = _calculate_total_from_api()
    assert total == 0.60, f"Expected 0.60, got {total}"

