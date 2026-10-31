"""
test_api_get_expenses.py — GET /api/expenses Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests the GET /api/expenses endpoint for:
  - Correct HTTP status and JSON structure
  - Empty database response
  - Required fields on each record
  - Response time within NFR-1 performance threshold

Covers: FR-3, FR-6, NFR-1
"""

import time

from conftest import create_expense, http_get


def test_get_expenses_returns_200():
    """
    FR-3: GET /api/expenses must return HTTP 200 OK.
    """
    status, _, body = http_get("/api/expenses")

    assert status == 200, f"Expected 200, got {status}. Body: {body}"


def test_get_expenses_returns_json_array():
    """
    FR-3: The response body must be a JSON array (even when empty).
    """
    status, _, body = http_get("/api/expenses")

    assert status == 200
    assert isinstance(body, list), (
        f"Expected JSON array, got {type(body).__name__}: {body}"
    )


def test_get_expenses_empty_database():
    """
    FR-3: When no expense records exist, GET must return an empty array [].
    The reset_csv fixture guarantees a header-only CSV before this test.
    """
    status, _, body = http_get("/api/expenses")

    assert status == 200
    assert body == [], f"Expected [], got {body}"


def test_get_expense_record_schema():
    """
    FR-3: Each expense record in the response must contain all four required
    fields: id (str), customer_name (str), amount (float/int), category (str).
    """
    create_expense("Schema Test User", 45.50, "Travel")

    status, _, body = http_get("/api/expenses")
    assert status == 200
    assert len(body) >= 1, "Expected at least one record"

    record = body[0]
    assert "id" in record, f"Missing 'id' field: {record}"
    assert "customer_name" in record, f"Missing 'customer_name' field: {record}"
    assert "amount" in record, f"Missing 'amount' field: {record}"
    assert "category" in record, f"Missing 'category' field: {record}"

    assert isinstance(record["id"], str) and len(record["id"]) > 0
    assert isinstance(record["customer_name"], str) and len(record["customer_name"]) > 0
    assert isinstance(record["amount"], (int, float)) and record["amount"] > 0
    assert isinstance(record["category"], str) and len(record["category"]) > 0


def test_get_all_expenses_returns_all_records():
    """
    FR-3: After creating multiple expense records, GET must return all of them.
    """
    records = [
        create_expense("Alice Brown", 75.20, "Travel"),
        create_expense("Bob Jones", 12.99, "Food"),
        create_expense("Carol White", 200.00, "Shopping"),
    ]
    created_ids = {r["id"] for r in records}

    status, _, body = http_get("/api/expenses")
    assert status == 200
    assert len(body) == 3, f"Expected 3 records, got {len(body)}"

    retrieved_ids = {e["id"] for e in body}
    assert created_ids == retrieved_ids, (
        f"Created IDs {created_ids} do not match retrieved IDs {retrieved_ids}"
    )


def test_get_expenses_response_time():
    """
    NFR-1: GET /api/expenses must respond in < 500 ms under normal local conditions.
    """
    start = time.monotonic()
    status, _, body = http_get("/api/expenses")
    elapsed_ms = (time.monotonic() - start) * 1000

    assert status == 200
    assert elapsed_ms < 500, (
        f"NFR-1 VIOLATION: GET /api/expenses took {elapsed_ms:.1f} ms "
        f"(limit: 500 ms)"
    )


def test_get_expenses_amount_is_numeric():
    """
    FR-3: The 'amount' field in each record must be a JSON number (not a string).
    The SRS specifies amount as Number (Float), 2 decimal places.
    """
    create_expense("Numeric Amount User", 99.99, "Food")

    status, _, body = http_get("/api/expenses")
    assert status == 200
    for expense in body:
        assert isinstance(expense["amount"], (int, float)), (
            f"Amount must be numeric, got {type(expense['amount']).__name__}: "
            f"{expense['amount']}"
        )


def test_get_after_post_reflects_new_record():
    """
    FR-6: A new expense POSTed to the server must immediately appear in a
    subsequent GET request (data is persisted and accessible without reload).
    """
    new_expense = create_expense("Persistence Check User", 33.33, "Shopping")

    status, _, body = http_get("/api/expenses")
    assert status == 200

    ids = [e["id"] for e in body]
    assert new_expense["id"] in ids, (
        f"Newly created expense ID {new_expense['id']} not found in GET response"
    )

