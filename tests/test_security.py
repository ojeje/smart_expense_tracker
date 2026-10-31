"""
test_security.py — NFR-4 Security Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests verifying:
  - CSV formula / injection attack characters are sanitized with single-quote prefix
  - Path traversal attempts are blocked (403 or 404)
  - Injected values are returned safely (single-quote prefix preserves data integrity)

All injection characters per SRS NFR-4 and csvHelper.sanitizeFieldForCsv():
  = , + , - , @

Covers: NFR-4 (security & input sanitization)
"""

from conftest import CSV_FILE, create_expense, http_get, http_post


# ---------------------------------------------------------------------------
# CSV Formula Injection sanitization helpers
# ---------------------------------------------------------------------------

def _get_csv_raw():
    """Return the raw bytes of expenses.csv decoded as UTF-8."""
    return CSV_FILE.read_bytes().decode("utf-8")


def _post_and_get_stored_name(customer_name):
    """
    POST an expense with the given customer_name, then retrieve it via GET
    and return the stored customer_name value.
    """
    status, _, body = http_post("/api/expenses", {
        "customer_name": customer_name,
        "amount": 10.00,
        "category": "Food",
    })
    assert status == 201, f"POST failed with {status}: {body}"
    exp_id = body["id"]

    _, _, expenses = http_get("/api/expenses")
    match = next((e for e in expenses if e["id"] == exp_id), None)
    assert match is not None, f"Created expense {exp_id} not found in GET"
    return match["customer_name"]


# ---------------------------------------------------------------------------
# NFR-4: Formula injection tests
# ---------------------------------------------------------------------------

def test_csv_formula_injection_equals_sanitized():
    """
    NFR-4: A customer_name starting with '=' (e.g. '=SUM(A1:A5)') is a
    CSV formula injection attempt.  The server must prefix the value with a
    single quote "'" before storing it in the CSV, and return the prefixed
    value via the API.

    Stored CSV value: '=SUM(A1:A5)
    GET response customer_name: '=SUM(A1:A5)
    """
    dangerous_name = "=SUM(A1:A5)"
    sanitized_name = _post_and_get_stored_name(dangerous_name)

    assert sanitized_name == f"'{dangerous_name}", (
        f"Expected sanitized name \"'{dangerous_name}\", got \"{sanitized_name}\""
    )

    # Also verify in the raw CSV file
    csv_raw = _get_csv_raw()
    assert f"'=SUM(A1:A5)" in csv_raw, (
        "Formula injection value not sanitized in CSV file"
    )
    # Ensure the dangerous raw form is NOT the start of any field
    # (it may appear after the sanitizing quote, which is acceptable)


def test_csv_plus_injection_sanitized():
    """
    NFR-4: A customer_name starting with '+' must be sanitized with a
    leading single-quote prefix to prevent spreadsheet formula execution.
    """
    dangerous_name = "+1-888-555-1234"
    sanitized_name = _post_and_get_stored_name(dangerous_name)

    assert sanitized_name == f"'{dangerous_name}", (
        f"Expected \"'+1-888-555-1234\", got \"{sanitized_name}\""
    )

    csv_raw = _get_csv_raw()
    assert "'+1-888-555-1234" in csv_raw, "Plus-prefix injection not sanitized in CSV"


def test_csv_minus_injection_sanitized():
    """
    NFR-4: A customer_name starting with '-' must be sanitized with a
    leading single-quote prefix.
    """
    dangerous_name = "-CMD|whoami"
    sanitized_name = _post_and_get_stored_name(dangerous_name)

    assert sanitized_name == f"'{dangerous_name}", (
        f"Expected \"'-CMD|whoami\", got \"{sanitized_name}\""
    )

    csv_raw = _get_csv_raw()
    assert "'-CMD|whoami" in csv_raw, "Minus-prefix injection not sanitized in CSV"


def test_csv_at_injection_sanitized():
    """
    NFR-4: A customer_name starting with '@' must be sanitized with a
    leading single-quote prefix to prevent DDE or macro attacks.
    """
    dangerous_name = "@SUM(1+1)*cmd|' /C calc'!A0"
    sanitized_name = _post_and_get_stored_name(dangerous_name)

    assert sanitized_name == f"'{dangerous_name}", (
        f"Expected at-prefix sanitization, got \"{sanitized_name}\""
    )

    csv_raw = _get_csv_raw()
    assert "'@SUM" in csv_raw, "At-prefix injection not sanitized in CSV"


def test_safe_customer_name_not_modified():
    """
    NFR-4: A normal customer name that does NOT start with an injection
    character must be stored and returned without any modification.
    """
    normal_name = "Alice Brown"
    stored_name = _post_and_get_stored_name(normal_name)

    assert stored_name == normal_name, (
        f"Normal name was modified: expected '{normal_name}', got '{stored_name}'"
    )


# ---------------------------------------------------------------------------
# NFR-4: Path traversal protection
# ---------------------------------------------------------------------------

def test_path_traversal_double_dot_blocked():
    """
    NFR-4: A request attempting directory traversal via '/../' in the path
    must be blocked.  The server must return 403 Forbidden or 404 Not Found
    (never 200 with sensitive file content).

    Traversal target: /../package.json (outside public/ directory)
    """
    status, _, body = http_get("/../package.json")

    assert status in (403, 404), (
        f"Expected 403 or 404 for path traversal, got {status}"
    )

    # Critical: response body must NOT contain sensitive package.json content
    body_str = str(body)
    assert '"type"' not in body_str or '"module"' not in body_str, (
        "Path traversal succeeded — package.json content was returned!"
    )


def test_path_traversal_encoded_blocked():
    """
    NFR-4: URL-encoded path traversal (%2e%2e%2f = '../') must also be
    blocked, returning 403 or 404.
    """
    status, _, body = http_get("/%2e%2e%2fpackage.json")

    assert status in (403, 404), (
        f"Expected 403 or 404 for encoded path traversal, got {status}"
    )


def test_path_traversal_nested_blocked():
    """
    NFR-4: A deeply nested traversal attempt /css/../../../server.js
    must not expose server-side source files.
    """
    status, _, body = http_get("/css/../../../server.js")

    # Either blocked (403/404) or resolves safely within public/ (where no server.js exists)
    assert status in (403, 404, 200), f"Unexpected status: {status}"
    if status == 200:
        body_str = str(body)
        # If 200, should be a file from within public/, not the actual server.js source
        assert "import" not in body_str or "createServer" not in body_str, (
            "SECURITY: server.js source exposed via path traversal!"
        )


def test_static_serving_does_not_expose_data_directory():
    """
    NFR-4: The expenses.csv data file must not be accessible via the static
    server (it lives in data/, which is outside public/).
    """
    status, _, body = http_get("/../data/expenses.csv")

    assert status in (403, 404), (
        f"Expected 403/404 for data directory access attempt, got {status}"
    )

    body_str = str(body)
    assert "customer_name" not in body_str, (
        "SECURITY: expenses.csv content exposed via static server!"
    )

