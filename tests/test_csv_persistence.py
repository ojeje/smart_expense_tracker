"""
test_csv_persistence.py — FR-6 CSV Lifecycle & NFR-2 Data Integrity Tests
Smart Expense Tracker — Pytest Integration Suite

Tests verifying:
  - POST appends a row to expenses.csv
  - DELETE removes the row from expenses.csv
  - CSV header row is correctly formatted
  - Data survives a full server restart (durability)
  - Rapid sequential writes maintain CSV integrity (NFR-2)
  - CSV header preserved after all data rows are deleted

Covers: FR-6, NFR-2
"""

import time

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
# CSV Header verification
# ---------------------------------------------------------------------------

def test_csv_file_has_correct_header_row():
    """
    FR-6 / SRS §3.2: The expenses.csv file must have the header row
    "id,customer_name,amount,category" as its first line, using CRLF endings.
    """
    raw = CSV_FILE.read_bytes()

    assert raw.startswith(b"id,customer_name,amount,category\r\n"), (
        f"CSV does not start with the expected RFC 4180 CRLF header. "
        f"First 60 bytes: {raw[:60]!r}"
    )


# ---------------------------------------------------------------------------
# POST → CSV append
# ---------------------------------------------------------------------------

def test_post_appends_row_to_csv():
    """
    FR-6: A successful POST must append a new data row to expenses.csv.
    The row must contain the correct id, customer_name, amount, and category.
    """
    expense = create_expense("CSV Append User", 42.00, "Travel")

    raw = CSV_FILE.read_bytes().decode("utf-8")
    lines = [l for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]

    # First line is header; second line should be our expense
    assert len(lines) == 2, f"Expected 2 lines (header + 1 record), got {len(lines)}"

    data_line = lines[1]
    assert expense["id"] in data_line, f"ID {expense['id']} not found in CSV row"
    assert "CSV Append User" in data_line
    # Amount stored as 2-dp string by toFixed(2)
    assert "42.00" in data_line
    assert "Travel" in data_line


def test_post_multiple_records_appends_multiple_rows():
    """
    FR-6: Each POST must append exactly one row to the CSV.
    Three POSTs must result in a CSV with 1 header row + 3 data rows.
    """
    create_expense("Multi CSV A", 10.00, "Food")
    create_expense("Multi CSV B", 20.00, "Travel")
    create_expense("Multi CSV C", 30.00, "Shopping")

    raw = CSV_FILE.read_bytes().decode("utf-8")
    lines = [l for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]

    assert len(lines) == 4, (
        f"Expected 4 lines (1 header + 3 data rows), got {len(lines)}"
    )


# ---------------------------------------------------------------------------
# DELETE → CSV row removal
# ---------------------------------------------------------------------------

def test_delete_removes_row_from_csv():
    """
    FR-6: A successful DELETE must remove the corresponding row from expenses.csv.
    The remaining rows must be intact.
    """
    e1 = create_expense("CSV Delete User A", 10.00, "Food")
    e2 = create_expense("CSV Delete User B", 20.00, "Travel")

    # Delete e1
    http_delete(f"/api/expenses/{e1['id']}")
    time.sleep(0.05)  # Allow atomic rename to complete

    raw = CSV_FILE.read_bytes().decode("utf-8")
    lines = [l for l in raw.replace("\r\n", "\n").split("\n") if l.strip()]

    # Header + e2 remaining
    assert len(lines) == 2, (
        f"Expected 2 lines (header + 1 remaining), got {len(lines)}"
    )
    assert e1["id"] not in raw, f"Deleted record {e1['id']} still in CSV"
    assert e2["id"] in raw, f"Remaining record {e2['id']} missing from CSV"


def test_csv_header_preserved_after_delete():
    """
    NFR-2: After deleting all expense records, the CSV file must still
    contain the correct header row (not become empty or corrupted).
    """
    expense = create_expense("Last Record User", 15.00, "Food")
    http_delete(f"/api/expenses/{expense['id']}")
    time.sleep(0.05)

    raw = CSV_FILE.read_bytes()
    assert raw.startswith(b"id,customer_name,amount,category\r\n"), (
        f"Header missing or corrupted after deleting all records. "
        f"First 60 bytes: {raw[:60]!r}"
    )

    # Verify no data rows remain
    decoded = raw.decode("utf-8")
    lines = [l for l in decoded.replace("\r\n", "\n").split("\n") if l.strip()]
    assert len(lines) == 1, (
        f"Expected only the header row after full delete, got {len(lines)} lines"
    )


# ---------------------------------------------------------------------------
# NFR-2: Rapid sequential writes
# ---------------------------------------------------------------------------

def test_rapid_sequential_writes_maintain_integrity():
    """
    NFR-2: Five rapid sequential POSTs must all be persisted without
    corruption, missing rows, or duplicate rows.

    This validates the server's mutex write queue ensures serialised,
    atomic file operations even under rapid sequential load.
    """
    ids = []
    for i in range(1, 6):
        expense = create_expense(f"Rapid Write User {i}", float(i * 5), "Food")
        ids.append(expense["id"])

    time.sleep(0.1)  # Allow all queued writes to flush

    # Check via API
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200
    assert len(expenses) == 5, f"Expected 5 records after rapid writes, got {len(expenses)}"

    retrieved_ids = {e["id"] for e in expenses}
    for eid in ids:
        assert eid in retrieved_ids, f"Record {eid} missing after rapid write"

    # Cross-check via CSV file directly
    raw = CSV_FILE.read_bytes().decode("utf-8")
    data_lines = [
        l for l in raw.replace("\r\n", "\n").split("\n")
        if l.strip() and not l.startswith("id,")
    ]
    assert len(data_lines) == 5, (
        f"Expected 5 data rows in CSV, found {len(data_lines)}"
    )


# ---------------------------------------------------------------------------
# FR-6: Data durability across server restart
# ---------------------------------------------------------------------------

def test_data_survives_server_restart(server):
    """
    FR-6 Scenario: Persistence across page refresh and session restart.

    Steps:
      1. POST 3 expense records using the running server.
      2. Stop the current server process.
      3. Start a fresh server process pointing at the same expenses.csv.
      4. GET /api/expenses from the new server — all 3 records must be present.

    Covers: FR-6 (data durability)
    """
    # Step 1: Create 3 expenses
    e1 = create_expense("Restart User Alpha", 100.00, "Food")
    e2 = create_expense("Restart User Beta", 200.00, "Travel")
    e3 = create_expense("Restart User Gamma", 300.00, "Shopping")
    expected_ids = {e1["id"], e2["id"], e3["id"]}

    # Step 2: Stop the running server
    _stop_server(server["proc"])

    # Step 3: Start a fresh server (same project root → same expenses.csv)
    new_proc = _start_server()
    server["proc"] = new_proc  # Update context so session teardown cleans up
    _wait_for_server()

    # Step 4: Verify data persisted
    status, _, expenses = http_get("/api/expenses")
    assert status == 200, f"Expected 200 from restarted server, got {status}"
    assert len(expenses) == 3, (
        f"Expected 3 expenses after restart, got {len(expenses)}"
    )

    retrieved_ids = {e["id"] for e in expenses}
    assert expected_ids == retrieved_ids, (
        f"Records mismatch after restart.\n"
        f"Expected: {expected_ids}\n"
        f"Got:      {retrieved_ids}"
    )

    # Verify field values are intact
    alpha = next(e for e in expenses if e["id"] == e1["id"])
    assert alpha["customer_name"] == "Restart User Alpha"
    assert alpha["amount"] == 100.00
    assert alpha["category"] == "Food"

