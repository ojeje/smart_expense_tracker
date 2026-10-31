# Bug Reports & Findings
## Smart Expense Tracker — Integration Test Suite

**Author:** SDET, XYZ Software Inc  
**Date:** 2026-10-31  
**Test Suite:** Pytest Integration Suite (`tests/`)  
**Total Tests:** 93  
**Passed:** 93  
**Failed:** 0  

---

### Bug Summary Table

| Bug ID | Title | Priority | Severity | Requirement | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | Sub-cent decimal amount (e.g., `0.001`) normalizes to `0.00` and persists | P2 | Medium | FR-2, NFR-2 | **RESOLVED & VERIFIED** |

---

### BUG-001: Sub-cent decimal amount normalizes to 0.00 and persists

- **Priority:** P2 (High / Medium)
- **Severity:** Medium
- **Req ID:** FR-2 (Validation Matrix), NFR-2 (Data Integrity)
- **Test File:** `tests/test_edge_cases.py::test_ec2_amount_zero_point_zero_zero_one_behavior`
- **Component:** `src/utils/validator.js` & `public/js/validator.js`
- **Status:** **RESOLVED & VERIFIED**

#### Description
In `src/utils/validator.js`, the amount validation rule previously checked:
```javascript
const parsedAmount = Number(amount);
if (amount === undefined || amount === null || amount === '' || isNaN(parsedAmount) || parsedAmount <= 0) {
  return { isValid: false, errorMessage: 'Please enter an amount greater than zero.' };
}
```
When a client sends `amount: 0.001`, `parsedAmount` was `0.001`, which satisfied `parsedAmount > 0`. However, `Math.round(0.001 * 100) / 100` computes to `0.00`, causing an expense with `amount: 0.00` to be persisted.

#### Resolution Applied
Both `src/utils/validator.js` (backend) and `public/js/validator.js` (frontend) were updated to normalize to 2 decimal places prior to checking `roundedAmount <= 0`:
```javascript
const roundedAmount = Math.round(parsedAmount * 100) / 100;
if (roundedAmount <= 0) {
  return { isValid: false, errorMessage: 'Please enter an amount greater than zero.' };
}
```
Sub-cent amounts rounding to `0.00` now return HTTP 400 Bad Request with `"Please enter an amount greater than zero."`. Verified across all test suites.

#### Steps to Reproduce
1. Send an HTTP POST request to `/api/expenses` with the payload:
   ```json
   {
     "customer_name": "Test User",
     "amount": 0.001,
     "category": "Food"
   }
   ```
2. Inspect the HTTP response status and body:
   - Status: `201 Created`
   - Body: `{ "id": "exp-...", "customer_name": "Test User", "amount": 0, "category": "Food" }`
3. Inspect `data/expenses.csv`:
   - A row with amount `0.00` is appended.

#### Expected Behavior
The server should either:
1. Reject sub-cent inputs during validation with HTTP 400 (`"Please enter an amount greater than zero."`), or
2. Enforce the `> 0` check *after* 2-decimal-place rounding in `expenseService.js` / `validator.js`.

#### Actual Behavior
Record is accepted with HTTP 201 and stored with `amount: 0`.

#### Test Coverage
Handled and verified in `tests/test_edge_cases.py::test_ec2_amount_zero_point_zero_zero_one_behavior`.

---

### Non-Functional & Architecture Observations (Passed)

1. **NFR-1 (Performance):**
   - `GET /api/expenses` latency: ~2-5 ms (well below 500 ms ceiling).
   - `POST /api/expenses` latency: ~4-8 ms (well below 500 ms ceiling).

2. **NFR-2 (Data Safety & Mutex Serialization):**
   - 5 rapid sequential writes (`test_rapid_sequential_writes_maintain_integrity`) completed without corruption or missing entries.
   - Header row was preserved even when all data rows were deleted (`test_csv_header_preserved_after_delete`).
   - Server restart data durability verified (`test_data_survives_server_restart`).

3. **NFR-3 (Static File Serving):**
   - All static assets (`index.html`, `styles.css`, `app.js`, `state.js`, `api.js`, `ui.js`, `validator.js`) served with correct MIME types and caching headers.

4. **NFR-4 (Security & Injection):**
   - All formula injection prefixes (`=`, `+`, `-`, `@`) neutralized with `'` prefix.
   - Path traversal attempts (`/../package.json`, `%2e%2e%2f`, nested traversal) blocked.
   - 1 MB payload DoS ceiling enforced by server socket termination.

