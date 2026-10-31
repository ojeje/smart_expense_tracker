"""
test_edge_cases.py — Edge Case Integration Tests (EC-1 through EC-18)
Smart Expense Tracker — Pytest Integration Suite

These tests are intentionally run FIRST (alphabetically before all other
test modules) as required by the test plan.  They probe boundary conditions,
malformed input, and system-level limits that functional happy-path tests do
not cover.

Requirements covered: FR-1, FR-2, FR-3, FR-5, FR-6, NFR-2, NFR-4
"""

import json
import time

import pytest

from conftest import (
    CSV_FILE,
    CSV_HEADER_BYTES,
    _start_server,
    _stop_server,
    _wait_for_server,
    create_expense,
    http_delete,
    http_get,
    http_post,
)


# ---------------------------------------------------------------------------
# EC-1: GET on completely empty database (header-only CSV)
# ---------------------------------------------------------------------------


def test_ec1_get_empty_database_returns_empty_array():
    """
    EC-1: When expenses.csv contains only the header row, GET /api/expenses
    must return HTTP 200 with an empty JSON array [].

    Covers: FR-3 (empty-state), FR-6 (data lifecycle)
    """
    # reset_csv fixture guarantees header-only CSV before this test
    status, _, body = http_get("/api/expenses")

    assert status == 200, f"Expected 200, got {status}"
    assert isinstance(body, list), f"Expected list, got {type(body).__name__}: {body}"
    assert len(body) == 0, f"Expected empty list but got {len(body)} record(s)"


# ---------------------------------------------------------------------------
# EC-2: Amount that rounds to 0.00 after normalization
# ---------------------------------------------------------------------------


def test_ec2_amount_zero_point_zero_zero_one_behavior():
    """
    EC-2: Amount 0.001 is a positive sub-cent decimal that rounds to 0.00
    after 2-decimal normalization. The validator must reject sub-cent amounts
    with HTTP 400 Bad Request to guarantee all stored expenses have amount > 0.

    Covers: FR-2 (validation), NFR-2 (data integrity)
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "EC-2 Boundary User",
            "amount": 0.001,
            "category": "Food",
        },
    )

    assert (
        status == 400
    ), f"Expected 400 for sub-cent amount rounding to 0.00, got {status}. Body: {body}"
    assert body.get("error") == "Please enter an amount greater than zero."


# ---------------------------------------------------------------------------
# EC-3: Minimum valid amount (0.01)
# ---------------------------------------------------------------------------


def test_ec3_minimum_valid_amount():
    """
    EC-3: Amount = 0.01 is the smallest valid expense amount (> 0, 2 dp).
    The server must accept it and return 201.

    Covers: FR-1, FR-2
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "EC-3 Min Amount User",
            "amount": 0.01,
            "category": "Food",
        },
    )

    assert (
        status == 201
    ), f"Expected 201 for minimum valid amount, got {status}. Body: {body}"
    assert body.get("amount") == 0.01
    assert body.get("customer_name") == "EC-3 Min Amount User"
    assert body.get("category") == "Food"
    assert "id" in body


# ---------------------------------------------------------------------------
# EC-4: Very large amount (999999.99)
# ---------------------------------------------------------------------------


def test_ec4_very_large_amount():
    """
    EC-4: Amount = 999,999.99 is a large but valid value.
    The server must accept it without overflow or formatting errors.

    Covers: FR-1, FR-2
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "EC-4 Large Amount User",
            "amount": 999999.99,
            "category": "Shopping",
        },
    )

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert body.get("amount") == 999999.99
    assert body.get("category") == "Shopping"


# ---------------------------------------------------------------------------
# EC-5: Amount with more than 2 decimal places (rounded on storage)
# ---------------------------------------------------------------------------


def test_ec5_amount_three_decimal_places_rounded():
    """
    EC-5: Amount = 45.678 has 3 decimal places.
    SRS requires amounts normalised to 2 decimal places.
    Math.round(45.678 * 100) / 100 = 45.68.

    Covers: FR-1, FR-2 (validation matrix — 2-dp rule)
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "EC-5 Rounding User",
            "amount": 45.678,
            "category": "Travel",
        },
    )

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert (
        body.get("amount") == 45.68
    ), f"Expected 45.68 (rounded), got {body.get('amount')}"


# ---------------------------------------------------------------------------
# EC-6: Customer name with leading and trailing whitespace (trimmed on save)
# ---------------------------------------------------------------------------


def test_ec6_customer_name_whitespace_trimmed():
    """
    EC-6: Customer name "  Alice  " (padded with spaces) must be trimmed to
    "Alice" before storage and returned trimmed in the response.

    Covers: FR-1, FR-6, SRS §6 whitespace trimming
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "  Alice  ",
            "amount": 25.00,
            "category": "Food",
        },
    )

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert (
        body.get("customer_name") == "Alice"
    ), f"Expected trimmed name 'Alice', got '{body.get('customer_name')}'"


# ---------------------------------------------------------------------------
# EC-7: Customer name containing a comma (RFC 4180 quoting)
# ---------------------------------------------------------------------------


def test_ec7_customer_name_with_comma_stored_correctly():
    """
    EC-7: A customer name containing a comma (e.g. "Doe, John") must be
    stored correctly using RFC 4180 CSV quoting, and the GET response must
    return the name without any extra escaping.

    Covers: FR-6, NFR-4 (CSV structure integrity)
    """
    name_with_comma = "Doe, John"
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": name_with_comma,
            "amount": 15.00,
            "category": "Travel",
        },
    )

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert body.get("customer_name") == name_with_comma

    # Verify GET also returns the name correctly (CSV round-trip)
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    names = [e["customer_name"] for e in expenses]
    assert (
        name_with_comma in names
    ), f"Name with comma not found after GET. Got: {names}"


# ---------------------------------------------------------------------------
# EC-8: Customer name containing double-quote characters (RFC 4180 escaping)
# ---------------------------------------------------------------------------


def test_ec8_customer_name_with_double_quotes():
    """
    EC-8: A customer name containing double-quote characters must be stored
    using RFC 4180 double-quote escaping (\"\" inside quoted fields) and
    returned correctly via GET.

    Covers: FR-6, NFR-4
    """
    name_with_quotes = 'Alice "The Boss" Smith'
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": name_with_quotes,
            "amount": 50.00,
            "category": "Shopping",
        },
    )

    assert status == 201, f"Expected 201, got {status}. Body: {body}"
    assert body.get("customer_name") == name_with_quotes

    # Verify round-trip through CSV parse
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    names = [e["customer_name"] for e in expenses]
    assert (
        name_with_quotes in names
    ), f"Quoted name not found after CSV round-trip. Got: {names}"


# ---------------------------------------------------------------------------
# EC-9: DELETE the only record — GET must return empty array
# ---------------------------------------------------------------------------


def test_ec9_delete_only_record_returns_empty_list():
    """
    EC-9: After deleting the only expense record in the database, a subsequent
    GET must return an empty array [].

    Covers: FR-5, FR-3 (empty state after deletion)
    """
    expense = create_expense("EC-9 Sole User", 10.00, "Food")
    exp_id = expense["id"]

    # Delete the only record
    del_status, _, del_body = http_delete(f"/api/expenses/{exp_id}")
    assert del_status == 200, f"Delete failed with {del_status}. Body: {del_body}"
    assert del_body.get("success") is True

    # Database must now be empty
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    assert isinstance(expenses, list)
    assert len(expenses) == 0, f"Expected empty list, got {expenses}"


# ---------------------------------------------------------------------------
# EC-10: Double DELETE — second attempt must return 404
# ---------------------------------------------------------------------------


def test_ec10_double_delete_returns_404():
    """
    EC-10: Attempting to delete an expense that has already been deleted must
    return HTTP 404 Not Found.

    Covers: FR-5
    """
    expense = create_expense("EC-10 Double Delete", 20.00, "Travel")
    exp_id = expense["id"]

    # First delete — succeeds
    del1_status, _, _ = http_delete(f"/api/expenses/{exp_id}")
    assert del1_status == 200

    # Second delete — must fail with 404
    del2_status, _, del2_body = http_delete(f"/api/expenses/{exp_id}")
    assert (
        del2_status == 404
    ), f"Expected 404 on second delete, got {del2_status}. Body: {del2_body}"
    assert "error" in del2_body


# ---------------------------------------------------------------------------
# EC-11: DELETE with empty/blank ID segment
# ---------------------------------------------------------------------------


def test_ec11_delete_with_empty_id_is_rejected():
    """
    EC-11: DELETE /api/expenses/ (missing ID) should return 400 or 404.
    The server must not crash or silently succeed.

    Covers: FR-5
    """
    # Use a path that results in an empty or very short id segment
    status, _, body = http_delete("/api/expenses/ ")

    assert status in (
        400,
        404,
        405,
    ), f"Expected 400, 404, or 405 for blank ID, got {status}. Body: {body}"


# ---------------------------------------------------------------------------
# EC-12: POST with completely empty JSON body {}
# ---------------------------------------------------------------------------


def test_ec12_post_empty_body_returns_400():
    """
    EC-12: POSTing an empty JSON object {} must return 400 Bad Request
    because customer_name is missing, triggering the name validation rule.

    Covers: FR-2
    """
    status, _, body = http_post("/api/expenses", {})

    assert status == 400, f"Expected 400 for empty body, got {status}. Body: {body}"
    assert "error" in body, f"Expected 'error' key in response. Got: {body}"


# ---------------------------------------------------------------------------
# EC-13: POST with null values in all fields
# ---------------------------------------------------------------------------


def test_ec13_post_null_fields_returns_400():
    """
    EC-13: POSTing a JSON body where all fields are explicitly null must
    return 400 Bad Request.

    Covers: FR-2
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": None,
            "amount": None,
            "category": None,
        },
    )

    assert status == 400, f"Expected 400 for null fields, got {status}. Body: {body}"
    assert "error" in body


# ---------------------------------------------------------------------------
# EC-14: 5 rapid sequential POSTs — all records persisted
# ---------------------------------------------------------------------------


def test_ec14_rapid_sequential_posts_all_persisted():
    """
    EC-14: Submitting 5 POST requests in rapid succession must result in all
    5 records being persisted and returned by a subsequent GET.

    Covers: FR-1, FR-6, NFR-2 (rapid write integrity)
    """
    posted_ids = []
    for i in range(1, 6):
        expense = create_expense(f"EC-14 User {i}", float(i * 10), "Food")
        posted_ids.append(expense["id"])

    # Small pause for file system to stabilise
    time.sleep(0.1)

    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    assert len(expenses) == 5, f"Expected 5 records, found {len(expenses)}"

    retrieved_ids = {e["id"] for e in expenses}
    for pid in posted_ids:
        assert pid in retrieved_ids, f"POST'd record {pid} not found in GET response"


# ---------------------------------------------------------------------------
# EC-15: POST Custom category with whitespace-only custom_category
# ---------------------------------------------------------------------------


def test_ec15_custom_category_whitespace_only_returns_400():
    """
    EC-15: When category="Custom" but custom_category contains only whitespace,
    the server must return 400 Bad Request with the appropriate error message.

    Covers: FR-2 (validation rule 4)
    """
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": "EC-15 User",
            "amount": 30.00,
            "category": "Custom",
            "custom_category": "   ",
        },
    )

    assert status == 400, f"Expected 400, got {status}. Body: {body}"
    assert (
        body.get("error") == "Please enter a custom category name."
    ), f"Wrong error message: '{body.get('error')}'"


# ---------------------------------------------------------------------------
# EC-16: GET unknown route
# ---------------------------------------------------------------------------


def test_ec16_get_unknown_route_returns_404():
    """
    EC-16: A GET request to an undefined route (e.g. /api/unknown) must
    return HTTP 404.  The server must not crash.

    Covers: Application robustness
    """
    status, _, body = http_get("/api/unknown")

    assert status == 404, f"Expected 404 for unknown route, got {status}"


# ---------------------------------------------------------------------------
# EC-17: POST to mistyped endpoint
# ---------------------------------------------------------------------------


def test_ec17_post_to_wrong_endpoint_returns_404_or_405():
    """
    EC-17: POSTing to a mistyped endpoint (/api/expense instead of /api/expenses)
    must return 404 (Not Found) or 405 (Method Not Allowed by static fallback).
    The server must not silently accept or crash.

    Covers: Application robustness
    """
    status, _, body = http_post(
        "/api/expense",
        {
            "customer_name": "EC-17 Typo User",
            "amount": 10.00,
            "category": "Food",
        },
    )

    assert status in (404, 405), f"Expected 404 or 405 for wrong endpoint, got {status}"


# ---------------------------------------------------------------------------
# EC-18: Payload exceeding the 1 MB DoS safety ceiling
# ---------------------------------------------------------------------------


def test_ec18_oversized_payload_rejected():
    """
    EC-18: A request body larger than the server's MAX_PAYLOAD_BYTES limit
    (1 MB) must be rejected.  The server must return 413 or 400, not crash.

    Covers: NFR-2 (file safety / DoS protection), architecture MAX_PAYLOAD_BYTES
    """
    # Construct a payload well above 1 MB
    oversized_name = "A" * (1024 * 1024 + 512)
    status, _, body = http_post(
        "/api/expenses",
        {
            "customer_name": oversized_name,
            "amount": 10.00,
            "category": "Food",
        },
    )

    assert status in (
        400,
        413,
        500,
    ), f"Expected 400/413/500 for oversized payload, got {status}"
    # Confirm the record was NOT persisted
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    assert all(
        len(e.get("customer_name", "")) < 1024 * 1024 for e in expenses
    ), "Oversized record should NOT have been persisted"
