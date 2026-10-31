"""
test_api_delete_expense.py — DELETE /api/expenses/:id Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests the DELETE /api/expenses/:id endpoint for:
  - Successful deletion by ID (200, correct response shape)
  - Record removed from subsequent GET
  - 404 for unknown / already-deleted IDs
  - Deletion targets only the specific record; duplicates unaffected

Covers: FR-5
"""

from conftest import create_expense, http_delete, http_get, http_post


def test_delete_removes_record_from_get():
    """
    FR-5 Scenario: Confirm expense deletion.
    After deleting an expense by ID, a subsequent GET must NOT include that record.
    """
    expense = create_expense("Jane Doe", 50.00, "Travel")
    exp_id = expense["id"]

    # Confirm it's there
    status_before, _, before = http_get("/api/expenses")
    assert status_before == 200
    assert any(e["id"] == exp_id for e in before), "Record should exist before delete"

    # Delete it
    del_status, _, del_body = http_delete(f"/api/expenses/{exp_id}")
    assert del_status == 200, f"Expected 200, got {del_status}. Body: {del_body}"

    # Confirm it's gone
    status_after, _, after = http_get("/api/expenses")
    assert status_after == 200
    assert not any(e["id"] == exp_id for e in after), (
        f"Deleted expense {exp_id} should not appear in GET response"
    )


def test_delete_response_shape():
    """
    FR-5: A successful DELETE must return HTTP 200 with body
    { "success": true, "deletedId": "<id>" }.
    """
    expense = create_expense("Delete Shape User", 30.00, "Shopping")
    exp_id = expense["id"]

    del_status, _, del_body = http_delete(f"/api/expenses/{exp_id}")

    assert del_status == 200, f"Expected 200, got {del_status}"
    assert del_body.get("success") is True, (
        f"Expected success=true, got {del_body.get('success')}"
    )
    assert del_body.get("deletedId") == exp_id, (
        f"Expected deletedId='{exp_id}', got '{del_body.get('deletedId')}'"
    )


def test_delete_unknown_id_returns_404():
    """
    FR-5: Attempting to delete a non-existent expense ID must return HTTP 404
    with an error response body.
    """
    fake_id = "exp-nonexistent-00000000"

    del_status, _, del_body = http_delete(f"/api/expenses/{fake_id}")

    assert del_status == 404, f"Expected 404, got {del_status}. Body: {del_body}"
    assert "error" in del_body, f"Expected 'error' key in body. Got: {del_body}"


def test_delete_targets_specific_id_not_duplicates():
    """
    FR-5: Deletion must target ONLY the record matching the specified ID.
    Two records with identical name/amount/category but different IDs must
    result in only one being removed.
    """
    # Create two records with identical field values
    expense_a = create_expense("Duplicate Name", 50.00, "Travel")
    expense_b = create_expense("Duplicate Name", 50.00, "Travel")

    assert expense_a["id"] != expense_b["id"], "Precondition: IDs must differ"

    # Delete only expense_a
    del_status, _, del_body = http_delete(f"/api/expenses/{expense_a['id']}")
    assert del_status == 200
    assert del_body.get("deletedId") == expense_a["id"]

    # expense_b must still be present
    get_status, _, expenses = http_get("/api/expenses")
    assert get_status == 200

    ids = [e["id"] for e in expenses]
    assert expense_a["id"] not in ids, "Deleted record should not appear in GET"
    assert expense_b["id"] in ids, (
        "Non-targeted duplicate record must remain after targeted deletion"
    )


def test_delete_with_valid_expense_returns_success_true():
    """
    FR-5: The 'success' field in the delete response must be boolean True,
    not a truthy string or integer.
    """
    expense = create_expense("Boolean Check User", 40.00, "Food")

    del_status, _, del_body = http_delete(f"/api/expenses/{expense['id']}")

    assert del_status == 200
    assert del_body.get("success") is True and isinstance(
        del_body.get("success"), bool
    ), f"'success' must be boolean True, got {del_body.get('success')!r}"


def test_delete_decreases_expense_count():
    """
    FR-5 / FR-3: After deleting one record from a list of three, GET must
    return exactly two records.
    """
    e1 = create_expense("Count User A", 10.00, "Food")
    e2 = create_expense("Count User B", 20.00, "Travel")
    e3 = create_expense("Count User C", 30.00, "Shopping")

    # Verify 3 records exist
    status, _, before = http_get("/api/expenses")
    assert status == 200
    assert len(before) == 3, f"Expected 3 records before delete, got {len(before)}"

    # Delete one
    http_delete(f"/api/expenses/{e2['id']}")

    # Verify 2 remain
    status, _, after = http_get("/api/expenses")
    assert status == 200
    assert len(after) == 2, f"Expected 2 records after delete, got {len(after)}"

    remaining_ids = {e["id"] for e in after}
    assert e1["id"] in remaining_ids
    assert e2["id"] not in remaining_ids
    assert e3["id"] in remaining_ids

