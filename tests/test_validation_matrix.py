"""
test_validation_matrix.py — FR-2 Input Validation Matrix Tests
Smart Expense Tracker — Pytest Integration Suite

Verifies all 4 backend validation rules defined in SRS §6 (Input Validation Matrix):
  Rule 1: Customer Name — non-empty, non-whitespace-only
  Rule 2: Amount — numeric, > 0
  Rule 3: Category — non-empty, not the default prompt
  Rule 4: Custom Category — non-empty when Category = "Custom"

All exact error message strings are copied from the SRS and verified verbatim.

Covers: FR-2
"""

import pytest

from conftest import http_post


# ---------------------------------------------------------------------------
# Rule 1: Customer Name validation
# ---------------------------------------------------------------------------

def test_validation_empty_name_returns_400():
    """
    FR-2 Rule 1: An empty string for customer_name must return HTTP 400 with
    the exact SRS error message.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "",
        "amount": 25.00,
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter a valid customer name.", (
        f"Wrong error for empty name: '{body.get('error')}'"
    )


def test_validation_whitespace_only_name_returns_400():
    """
    FR-2 Rule 1: A string consisting solely of whitespace must be treated as
    empty and rejected with the customer name error message.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "   ",
        "amount": 25.00,
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter a valid customer name.", (
        f"Wrong error for whitespace name: '{body.get('error')}'"
    )


def test_validation_missing_name_field_returns_400():
    """
    FR-2 Rule 1: A request body with no customer_name field must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "amount": 25.00,
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter a valid customer name."


# ---------------------------------------------------------------------------
# Rule 2: Amount validation
# ---------------------------------------------------------------------------

def test_validation_missing_amount_returns_400():
    """
    FR-2 Rule 2: A request body without an amount field must be rejected
    with the amount error message.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter an amount greater than zero.", (
        f"Wrong error for missing amount: '{body.get('error')}'"
    )


def test_validation_zero_amount_returns_400():
    """
    FR-2 Rule 2: Amount of exactly 0 (zero) must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 0,
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter an amount greater than zero.", (
        f"Wrong error for zero amount: '{body.get('error')}'"
    )


def test_validation_negative_amount_returns_400():
    """
    FR-2 Rule 2: A negative amount must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": -15.50,
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter an amount greater than zero.", (
        f"Wrong error for negative amount: '{body.get('error')}'"
    )


def test_validation_non_numeric_amount_string_returns_400():
    """
    FR-2 Rule 2: A non-numeric string value for amount must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": "not-a-number",
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter an amount greater than zero."


def test_validation_empty_string_amount_returns_400():
    """
    FR-2 Rule 2: An empty string for amount must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": "",
        "category": "Food",
    })

    assert status == 400
    assert body.get("error") == "Please enter an amount greater than zero."


# ---------------------------------------------------------------------------
# Rule 3: Category validation
# ---------------------------------------------------------------------------

def test_validation_default_category_string_returns_400():
    """
    FR-2 Rule 3: When category is the literal string "default" (the value
    used for the disabled default prompt option), the request must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 25.00,
        "category": "default",
    })

    assert status == 400
    assert body.get("error") == "Please select a category.", (
        f"Wrong error for default category: '{body.get('error')}'"
    )


def test_validation_empty_category_returns_400():
    """
    FR-2 Rule 3: An empty string for category must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 25.00,
        "category": "",
    })

    assert status == 400
    assert body.get("error") == "Please select a category."


def test_validation_missing_category_field_returns_400():
    """
    FR-2 Rule 3: A request body with no category field must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 25.00,
    })

    assert status == 400
    assert body.get("error") == "Please select a category."


# ---------------------------------------------------------------------------
# Rule 4: Custom Category validation
# ---------------------------------------------------------------------------

def test_validation_blank_custom_category_returns_400():
    """
    FR-2 Rule 4: When category = "Custom" but custom_category is empty or
    absent, the request must be rejected with the custom category error message.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 25.00,
        "category": "Custom",
    })

    assert status == 400
    assert body.get("error") == "Please enter a custom category name.", (
        f"Wrong error for blank custom category: '{body.get('error')}'"
    )


def test_validation_whitespace_custom_category_returns_400():
    """
    FR-2 Rule 4: A whitespace-only custom_category with category = "Custom"
    must be rejected.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": "John Doe",
        "amount": 25.00,
        "category": "Custom",
        "custom_category": "   ",
    })

    assert status == 400
    assert body.get("error") == "Please enter a custom category name."


# ---------------------------------------------------------------------------
# Parametrized comprehensive validation matrix (SRS §6 Examples)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("payload, expected_error", [
    # Name errors
    (
        {"customer_name": "", "amount": 25.00, "category": "Food"},
        "Please enter a valid customer name.",
    ),
    (
        {"customer_name": "   ", "amount": 25.00, "category": "Food"},
        "Please enter a valid customer name.",
    ),
    # Amount errors
    (
        {"customer_name": "John Doe", "amount": "", "category": "Food"},
        "Please enter an amount greater than zero.",
    ),
    (
        {"customer_name": "John Doe", "amount": 0, "category": "Food"},
        "Please enter an amount greater than zero.",
    ),
    (
        {"customer_name": "John Doe", "amount": -15.50, "category": "Food"},
        "Please enter an amount greater than zero.",
    ),
    # Category errors
    (
        {"customer_name": "John Doe", "amount": 25.00, "category": "default"},
        "Please select a category.",
    ),
    # Custom category error
    (
        {"customer_name": "John Doe", "amount": 25.00, "category": "Custom"},
        "Please enter a custom category name.",
    ),
])
def test_validation_error_messages_exact_text(payload, expected_error):
    """
    FR-2: Parametrized test covering all SRS §6 validation matrix rows.
    Verifies that each invalid input combination returns HTTP 400 and the
    exact error message string specified in the SRS.
    """
    status, _, body = http_post("/api/expenses", payload)

    assert status == 400, (
        f"Expected 400 for payload {payload}, got {status}"
    )
    assert body.get("error") == expected_error, (
        f"Payload: {payload}\n"
        f"Expected error: '{expected_error}'\n"
        f"Actual error:   '{body.get('error')}'"
    )

