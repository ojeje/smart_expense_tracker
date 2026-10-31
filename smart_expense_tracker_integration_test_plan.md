# Integration Test Plan
## Smart Expense Tracker — Pytest Suite

**Client:** ABC & Co Inc  
**Vendor:** XYZ Software Inc  
**Author:** SDET, XYZ Software Inc  
**Version:** 1.0  
**Status:** Pending Approval  

---

## 1. Purpose and Scope

This document defines the integration test strategy, test environment, test cases, and acceptance-criteria traceability for the **Smart Expense Tracker** application. All tests are implemented exclusively using the **Pytest Python testing framework** (v9.1.1). No browser-automation or third-party testing frameworks are used.

### 1.1 In Scope

| Layer | What Is Tested |
|-------|---------------|
| REST API — Backend | All HTTP endpoints: GET `/api/expenses`, POST `/api/expenses`, DELETE `/api/expenses/:id` |
| Input Validation | All 4 SRS validation rules (FR-2) exercised via HTTP |
| CSV Persistence | File creation, append, atomic-rename delete, data durability across server restarts |
| Static File Serving | Index HTML, CSS, and JS modules served with correct MIME types and status codes |
| Path Traversal Security | Directory escape attempts blocked (NFR-4) |
| CSV Injection / Formula Injection | Dangerous field prefixes neutralised before CSV write (NFR-4) |
| Edge Cases | Empty database, large amounts, boundary amounts, concurrent rapid writes |

### 1.2 Out of Scope

- Browser DOM interaction (no Selenium/Playwright — Pytest only)
- JavaScript unit tests (already covered by `test_frontend_units.js`)
- Multi-user / concurrent session scenarios
- Cloud storage or external databases
- Authentication / authorisation

---

## 2. Test Environment

### 2.1 Runtime Dependencies

| Dependency | Version | Notes |
|-----------|---------|-------|
| Python | 3.14.8 | Available in environment |
| pytest | 9.1.1 | Available in environment |
| urllib | stdlib | Used for HTTP calls (no `requests` library) |
| Node.js | LTS (>=18) | Must be on `PATH`; server started by fixture |

### 2.2 Server Startup Strategy

A **session-scoped pytest fixture** (`server`) in `tests/conftest.py` will:

1. Launch `node server.js` via `subprocess.Popen` from the project root.
2. Poll `GET http://localhost:3000/api/expenses` with a 2-second retry loop (max 10 attempts) to confirm the server is accepting connections.
3. Yield control to the test session.
4. On teardown: send `SIGTERM` to the process and `wait()`.

The test server will use the **default port 3000**. If `PORT` is already in use, tests fail fast with a clear error.

### 2.3 CSV Reset Strategy

A **function-scoped autouse fixture** (`reset_csv`) in `tests/conftest.py` will:

- **Before each test:** Overwrite `data/expenses.csv` with the clean header: `id,customer_name,amount,category\r\n`
- **After each test:** Same reset (teardown) so no test pollutes the next.

### 2.4 Directory Layout

```
smart_expense_tracker/
├── tests/
│   ├── conftest.py                     # Shared fixtures (server, reset_csv, helpers)
│   ├── test_edge_cases.py              # Edge cases (run first per constraint)
│   ├── test_validation_matrix.py       # FR-2: All 4 SRS validation rules
│   ├── test_api_get_expenses.py        # FR-3, FR-6: GET all expenses
│   ├── test_api_create_expense.py      # FR-1: POST expense (valid paths)
│   ├── test_api_delete_expense.py      # FR-5: DELETE expense
│   ├── test_csv_persistence.py         # FR-6: CSV lifecycle & durability
│   ├── test_static_serving.py          # Architecture: static file serving, MIME types
│   ├── test_security.py               # NFR-4: injection, path traversal
│   └── test_total_calculation.py       # FR-4: Total amount arithmetic accuracy
└── pytest.ini                          # pytest configuration
```

---

## 3. Acceptance Criteria Traceability Matrix

| Req ID | Requirement Summary | Test File | Test Name(s) |
|--------|--------------------|-----------|----|
| FR-1 | Expense creation with predefined category | `test_api_create_expense.py` | `test_create_expense_predefined_category` |
| FR-1 | Expense creation with custom category | `test_api_create_expense.py` | `test_create_expense_custom_category` |
| FR-1 | Response contains all required fields | `test_api_create_expense.py` | `test_create_expense_response_fields` |
| FR-1 | `custom_category` resolved into `category` on response | `test_api_create_expense.py` | `test_custom_category_resolved_in_response` |
| FR-2 | Empty customer name rejected (400) | `test_validation_matrix.py` | `test_validation_empty_name` |
| FR-2 | Whitespace-only customer name rejected (400) | `test_validation_matrix.py` | `test_validation_whitespace_name` |
| FR-2 | Missing amount rejected (400) | `test_validation_matrix.py` | `test_validation_missing_amount` |
| FR-2 | Zero amount rejected (400) | `test_validation_matrix.py` | `test_validation_zero_amount` |
| FR-2 | Negative amount rejected (400) | `test_validation_matrix.py` | `test_validation_negative_amount` |
| FR-2 | Default/empty category rejected (400) | `test_validation_matrix.py` | `test_validation_default_category` |
| FR-2 | Custom selected but blank custom_category rejected (400) | `test_validation_matrix.py` | `test_validation_blank_custom_category` |
| FR-2 | Exact SRS error message strings verified | `test_validation_matrix.py` | `test_validation_error_messages_exact_text` |
| FR-3 | GET returns all expenses as JSON array | `test_api_get_expenses.py` | `test_get_all_expenses_returns_list` |
| FR-3 | Empty DB returns empty JSON array | `test_api_get_expenses.py` | `test_get_expenses_empty_database` |
| FR-3 | Each record has required fields (id, customer_name, amount, category) | `test_api_get_expenses.py` | `test_get_expense_record_schema` |
| FR-4 | Total amount = sum of amounts (verified via GET) | `test_total_calculation.py` | `test_total_sum_multiple_expenses` |
| FR-4 | Total after deletion is recalculated correctly | `test_total_calculation.py` | `test_total_after_deletion` |
| FR-4 | Empty database: all amounts sum to 0.0 | `test_total_calculation.py` | `test_total_empty_database_is_zero` |
| FR-5 | DELETE by ID removes record from GET response | `test_api_delete_expense.py` | `test_delete_removes_record` |
| FR-5 | DELETE returns `{success: true, deletedId}` | `test_api_delete_expense.py` | `test_delete_response_shape` |
| FR-5 | DELETE unknown ID returns 404 | `test_api_delete_expense.py` | `test_delete_unknown_id_returns_404` |
| FR-5 | DELETE targets exact record by ID; duplicates unaffected | `test_api_delete_expense.py` | `test_delete_targets_specific_id` |
| FR-6 | POST appends row to CSV file | `test_csv_persistence.py` | `test_post_appends_row_to_csv` |
| FR-6 | DELETE removes row from CSV file | `test_csv_persistence.py` | `test_delete_removes_row_from_csv` |
| FR-6 | CSV created on server start with header row | `test_csv_persistence.py` | `test_csv_file_has_header_row` |
| FR-6 | Data survives server restart | `test_csv_persistence.py` | `test_data_survives_server_restart` |
| NFR-1 | GET /api/expenses responds in < 500 ms | `test_api_get_expenses.py` | `test_get_expenses_response_time` |
| NFR-1 | POST /api/expenses responds in < 500 ms | `test_api_create_expense.py` | `test_create_expense_response_time` |
| NFR-2 | Rapid sequential writes maintain CSV integrity | `test_csv_persistence.py` | `test_rapid_sequential_writes_maintain_integrity` |
| NFR-2 | CSV header preserved after all rows deleted | `test_csv_persistence.py` | `test_csv_header_preserved_after_delete` |
| NFR-3 | Static HTML served at GET `/` (200, text/html) | `test_static_serving.py` | `test_root_serves_html` |
| NFR-3 | CSS served with correct MIME type | `test_static_serving.py` | `test_css_served_with_correct_mime_type` |
| NFR-3 | JS module served with correct MIME type | `test_static_serving.py` | `test_js_served_with_correct_mime_type` |
| NFR-4 | Formula injection `=SUM()` is sanitized in CSV | `test_security.py` | `test_csv_formula_injection_sanitized` |
| NFR-4 | Leading `+` injection sanitized in CSV | `test_security.py` | `test_csv_plus_injection_sanitized` |
| NFR-4 | Leading `-` injection sanitized in CSV | `test_security.py` | `test_csv_minus_injection_sanitized` |
| NFR-4 | Leading `@` injection sanitized in CSV | `test_security.py` | `test_csv_at_injection_sanitized` |
| NFR-4 | Path traversal `/../` blocked (403/404) | `test_security.py` | `test_path_traversal_blocked` |

---

## 4. Test Categories and Priority

### 4.1 Edge Cases (Highest Priority — Created First)

| # | Edge Case | Expected Outcome |
|---|----------|-----------------|
| EC-1 | GET on completely empty database (header-only CSV) | 200 `[]` |
| EC-2 | POST with amount = 0.001 (rounds to 0.00, invalid) | 400 Bad Request |
| EC-3 | POST with amount = 0.01 (minimum valid) | 201 Created |
| EC-4 | POST with amount = 999999.99 (very large) | 201 Created |
| EC-5 | POST with amount having 3+ decimal places (e.g. 45.678) | 201, amount rounded to 2 dp (45.68) |
| EC-6 | POST with whitespace-padded customer name ("  Alice  ") | 201, name trimmed to "Alice" |
| EC-7 | POST with customer name containing comma | 201, CSV field properly quoted |
| EC-8 | POST with customer name containing double quotes | 201, RFC 4180 double-quote escaping applied |
| EC-9 | DELETE the only record — then GET returns empty array | 200 delete, 200 GET `[]` |
| EC-10 | DELETE an already-deleted ID (double delete) | 404 Not Found |
| EC-11 | DELETE with empty string / blank ID | 400 or 404 |
| EC-12 | POST with completely empty JSON body `{}` | 400 (name validation fires) |
| EC-13 | POST with null values in all fields | 400 |
| EC-14 | Rapid sequential 5 POSTs — all records persisted | 201 each; GET returns all 5 |
| EC-15 | POST category="Custom", custom_category whitespace-only | 400 |
| EC-16 | GET unknown route `/api/unknown` | 404 |
| EC-17 | POST to mistyped endpoint `/api/expense` | 404 |
| EC-18 | Request payload > 1 MB (DoS ceiling) | 413 or 400 |

### 4.2 Functional Tests (FR-1 through FR-6)

Standard happy-path and error-path tests mapped to acceptance criteria in Section 3.

### 4.3 Non-Functional Tests (NFR-1 through NFR-4)

Performance timing (< 500 ms), security sanitization, correct MIME types for static assets.

---

## 5. Bug Reporting Template

```
BUG-XXX: <Short Title>
Priority:  P1 | P2 | P3
Severity:  Critical | High | Medium | Low
Req ID:    FR-X / NFR-X
Test File: test_xxx.py::test_function_name
Steps:
  1. ...
Expected:  ...
Actual:    ...
Status:    Open | Fixed | Won't Fix
```

### Priority Classification

| Priority | Criteria |
|---------|---------|
| **P1 — Critical** | Data loss, data corruption, server crash, security vulnerability, or complete feature failure blocking core use |
| **P2 — High** | Incorrect response codes, wrong error messages, validation bypass, CSV structure broken |
| **P3 — Medium / Low** | Minor formatting issues, non-blocking edge cases, cosmetic discrepancies |

---

## 6. Coverage Target

- **Target:** >= 90% of acceptance criteria (FR-1 to FR-6, NFR-1 to NFR-4) covered by at least one passing test.
- Coverage is measured by acceptance-criteria traceability (Section 3), not Python line coverage (production code is Node.js).

---

## 7. Test Execution

### 7.1 Commands

```bash
# From the project root
cd "/Users/olusolajeje/AI Vibe Coding Course Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker"

# Run all integration tests (server auto-started by session fixture)
pytest tests/ -v --tb=short

# Run only edge cases first
pytest tests/test_edge_cases.py -v --tb=short

# Run a specific test file
pytest tests/test_validation_matrix.py -v

# Run a specific test
pytest tests/test_api_create_expense.py::test_create_expense_predefined_category -v
```

### 7.2 Pass Criteria

All tests must pass (exit code 0). Any failure causes the suite to be reported as **FAILED**. P1/P2 bugs found must be documented in a `BUGS.md` file and flagged for immediate resolution before sign-off.

---

## 8. Assumptions

1. `node` is available on `PATH` and the server starts successfully on port 3000.
2. The `data/` directory is writable by the test process.
3. No other process occupies port 3000 during the test run.
4. `urllib` (Python stdlib) is used for all HTTP calls; the `requests` library is not available.
5. Performance tests (NFR-1) are run on the local development machine under normal load.
6. Frontend DOM behaviour (keyboard accessibility, visual layout) is out of scope: no browser automation is permitted under the Pytest-only constraint.

