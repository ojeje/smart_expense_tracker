"""
test_api_create_expense.py — POST /api/expenses Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests the POST /api/expenses endpoint for:
  - Successful expense creation with predefined and custom categories
  - Correct response shape (201, id, customer_name, amount, category)
  - custom_category resolved into category field
  - Amount precision and whitespace trimming
  - Response time within NFR-1 threshold

Covers: FR-1, NFR-1
"""

import time

from conftest import create_expense, http_get, http_post


def test_create_expense_predefined_category():
    """
    FR-1 Scenario: Successful expense creation with a predefined category.

    Given: customer_name="John Doe", amount=45.50, category="Food"
    When:  POST /api/expenses
    Then:  HTTP 201 returned; record saved with unique ID, correct fields
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 45.50,
        "category": "Food",
    })

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert body.get("customer_name") == "John Doe"
    assert body.get("amount") == 45.50
    assert body.get("category") == "Food"
    assert "id" in body and isinstance(body["id"], str) and len(body["id"]) > 0


def test_create_expense_custom_category():
    """
    FR-1 Scenario: Successful expense creation with a Custom category.

    When category="Custom" and custom_category="Software Subscription",
    the server must resolve the category to "Software Subscription" in the
    stored record and HTTP response.

    Covers: FR-1 (custom category support)
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "Jane Smith",
        "amount": 120.00,
        "category": "Custom",
        "custom_category": "Software Subscription",
    })

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert body.get("customer_name") == "Jane Smith"
    assert body.get("amount") == 120.00
    # custom_category must be resolved into the category field
    assert body.get("category") == "Software Subscription", (
        f"Expected category='Software Subscription', got '{body.get('category')}'"
    )


def test_custom_category_resolved_in_response():
    """
    FR-1: The response body must contain the resolved category string (i.e.
    the custom_category value), NOT the literal string "Custom".
    The field "custom_category" must NOT appear in the response body.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "Resolver Test",
        "amount": 55.00,
        "category": "Custom",
        "custom_category": "Gadgets",
    })

    assert status == 201
    assert body.get("category") == "Gadgets", (
        f"custom_category should resolve to 'Gadgets', got '{body.get('category')}'"
    )
    assert body.get("category") != "Custom", (
        "The literal 'Custom' must not remain as the category after resolution"
    )
    assert "custom_category" not in body, (
        "The 'custom_category' field must not appear in the server response"
    )


def test_create_expense_response_fields():
    """
    FR-1: The POST response must include all four SRS data model fields:
    id, customer_name, amount, category.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "Fields Test User",
        "amount": 10.00,
        "category": "Travel",
    })

    assert status == 201
    assert "id" in body
    assert "customer_name" in body
    assert "amount" in body
    assert "category" in body


def test_create_expense_generates_unique_id():
    """
    FR-1 / SRS §3.1: Each newly created expense must have a unique, non-empty
    string identifier.  Two consecutive POSTs must yield different IDs.
    """
    expense_a = create_expense("Unique ID User A", 10.00, "Food")
    expense_b = create_expense("Unique ID User B", 20.00, "Travel")

    assert expense_a["id"] != expense_b["id"], (
        f"Duplicate IDs generated: {expense_a['id']}"
    )
    assert isinstance(expense_a["id"], str) and len(expense_a["id"]) > 0
    assert isinstance(expense_b["id"], str) and len(expense_b["id"]) > 0


def test_create_expense_amount_normalized_to_two_decimal_places():
    """
    FR-1 / SRS §3.1: amount must be stored and returned as a float with
    exactly 2 decimal places worth of precision.
    Math.round(45.678 * 100) / 100 → 45.68
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "Rounding User",
        "amount": 45.678,
        "category": "Shopping",
    })

    assert status == 201
    stored_amount = body.get("amount")
    assert stored_amount == 45.68, (
        f"Expected 45.68 after rounding 45.678, got {stored_amount}"
    )


def test_create_expense_customer_name_whitespace_trimmed():
    """
    FR-1 / SRS: Leading and trailing whitespace in customer_name must be
    stripped before storage.  "  Alice  " must be stored as "Alice".
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "  Alice  ",
        "amount": 25.00,
        "category": "Food",
    })

    assert status == 201
    assert body.get("customer_name") == "Alice", (
        f"Expected trimmed name 'Alice', got '{body.get('customer_name')}'"
    )


def test_create_expense_appears_in_subsequent_get():
    """
    FR-1 / FR-3: After a successful POST, the new record must be immediately
    visible in the response to GET /api/expenses.
    """
    expense = create_expense("Visibility User", 88.00, "Travel")

    status, _, expenses = http_get("/api/expenses")
    assert status == 200

    matching = [e for e in expenses if e["id"] == expense["id"]]
    assert len(matching) == 1, (
        f"Newly created expense {expense['id']} not found in GET response"
    )
    record = matching[0]
    assert record["customer_name"] == "Visibility User"
    assert record["amount"] == 88.00
    assert record["category"] == "Travel"


def test_create_expense_all_predefined_categories():
    """
    FR-1: All four predefined categories (Food, Travel, Shopping, Custom-resolved)
    must be accepted by the server.
    """
    categories = ["Food", "Travel", "Shopping"]
    for cat in categories:
        status, _, body = http_post("/api/expenses", {
            "customer_name": f"Category Test {cat}",
            "amount": 10.00,
            "category": cat,
        })
        assert status == 201, (
            f"Expected 201 for category='{cat}', got {status}. Body: {body}"
        )
        assert body.get("category") == cat


def test_create_expense_response_time():
    """
    NFR-1: POST /api/expenses must respond in < 500 ms under normal local conditions.
    """
    start = time.monotonic()
    status, _, body = http_post("/api/expenses", {
        "customer_name": "Perf Test User",
        "amount": 15.00,
        "category": "Food",
    })
    elapsed_ms = (time.monotonic() - start) * 1000

    assert status == 201
    assert elapsed_ms < 500, (
        f"NFR-1 VIOLATION: POST /api/expenses took {elapsed_ms:.1f} ms "
        f"(limit: 500 ms)"
    )

