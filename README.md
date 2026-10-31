# Smart Expense Tracker

**Client:** ABC & Co Inc  
**Vendor:** XYZ Software Inc  
**Authors:** Full-Stack Developer & Software Development Engineer in Test (SDET), XYZ Software Inc  
**Version:** 1.0.0 (Production Ready)  
**License:** Proprietary (ABC & Co Inc)

---

## Table of Contents
1. [Application Overview & Features](#1-application-overview--features)
2. [Architecture & Technology Stack](#2-architecture--technology-stack)
3. [Implementation Details](#3-implementation-details)
   - [Original Implementation](#31-original-implementation)
   - [Engineering Improvements & Code Review Remediations](#32-engineering-improvements--code-review-remediations)
4. [Testing & Quality Assurance](#4-testing--quality-assurance)
   - [Testing Strategy](#41-testing-strategy)
   - [Frontend Unit Tests](#42-frontend-unit-tests)
   - [Backend In-Memory Integration Tests](#43-backend-in-memory-integration-tests)
   - [Pytest Integration Test Suite](#44-pytest-integration-test-suite)
   - [Acceptance Criteria Traceability Matrix](#45-acceptance-criteria-traceability-matrix)
5. [Setup & Execution Guide](#5-setup--execution-guide)
6. [Areas for Further Improvement (Future Roadmap)](#6-areas-for-further-improvement-future-roadmap)

---

## 1. Application Overview & Features

The **Smart Expense Tracker** is a lightweight, responsive, and resilient single-page web application engineered for ABC & Co Inc to track and manage daily operational expenses. It enables users to record transactions, view an interactive summary and itemized log, delete records with confirmation, and persist all data safely to a local CSV file (`expenses.csv`).

### Core Features
- **Expense Data Entry (FR-1):** Intuitive top-of-page entry form capturing **Customer Name**, **Amount in USD ($)**, and **Category**.
- **Dynamic Custom Category (FR-1):** Category dropdown featuring predefined choices (`Food`, `Travel`, `Shopping`) and a `Custom` option that dynamically reveals a dedicated text field for bespoke categories.
- **Strict Input Validation (FR-2):** Synchronized client-side and server-side validation matrix displaying clear, user-friendly error messages while preserving valid inputs.
- **Line-by-Line Expense List (FR-3):** Tabular display of all active records formatted with currency symbols, aligned columns, and an empty-state notification (`"No expenses recorded yet."`).
- **Dynamic Total Calculation (FR-4):** Immediate, real-time summation of all active expenses, formatted as USD currency (`$X.XX`), accurate to the cent with zero floating-point accumulation drift.
- **Targeted Deletion with Confirmation (FR-5):** Individual record removal guarded by a native confirmation prompt (`"Are you sure you want to delete this expense?"`), deleting strictly by unique identifier even when identical names, amounts, or categories exist.
- **Durable CSV Persistence (FR-6):** Seamless synchronization with a local `data/expenses.csv` file adhering strictly to RFC 4180 standards across server reboots and browser refreshes.
- **Enterprise Security (NFR-4):**
  - **CSV Formula Injection Defense:** Prefixes dangerous leading characters (`=`, `+`, `-`, `@`) with a single quote (`'`) to neutralize spreadsheet command execution.
  - **Cross-Site Scripting (XSS) Prevention:** Strict DOM injection using native `textContent` nodes, avoiding `innerHTML` vulnerabilities.
  - **Path Traversal Protection:** Canonical path validation preventing directory escapes beyond the public web root.
  - **DoS Protection:** 1 MB payload size limit on incoming JSON request bodies.

---

## 2. Architecture & Technology Stack

The application strictly implements a **zero-dependency philosophy** for the production runtime, utilizing only native Node.js standard libraries and standard web browser APIs.

```
smart_expense_tracker/
├── server.js                          # HTTP server entry point & graceful shutdown
├── src/                               # Backend Node.js ES Modules
│   ├── app.js                         # Top-level request dispatcher
│   ├── config.js                      # Environment and path configurations
│   ├── staticHandler.js               # Static asset streaming & security sandbox
│   ├── routes/
│   │   └── expenseRoutes.js           # REST endpoint router
│   ├── controllers/
│   │   └── expenseController.js       # HTTP request/response handling
│   ├── services/
│   │   └── expenseService.js          # Business logic, UUID generation & normalization
│   ├── repositories/
│   │   └── csvExpenseRepository.js    # Concurrency mutex queue & atomic file I/O
│   └── utils/
│       ├── csvHelper.js               # RFC 4180 state-machine parser & serializer
│       ├── httpHelper.js              # JSON streaming & response helpers
│       └── validator.js               # Backend validation matrix enforcement
├── public/                            # Frontend Single Page Application
│   ├── index.html                     # Semantic, accessible HTML5 layout
│   ├── css/
│   │   └── styles.css                 # Modern CSS with custom design tokens
│   └── js/
│       ├── app.js                     # Main UI controller & DOM event orchestrator
│       ├── ui.js                      # DOM rendering, row injection & modals
│       ├── state.js                   # In-memory reactive state & cent accumulator
│       ├── api.js                     # Fetch API client wrapper
│       └── validator.js               # Client-side validation matrix enforcement
├── data/
│   └── expenses.csv                   # RFC 4180 CSV persistent storage
├── tests/                             # SDET Pytest Integration Test Suite (93 tests)
│   ├── conftest.py                    # Session fixtures & HTTP helpers
│   ├── test_edge_cases.py             # Boundary, payload & concurrency edge cases
│   ├── test_validation_matrix.py      # SRS §6 validation matrix test suite
│   ├── test_api_create_expense.py     # POST endpoint functional tests
│   ├── test_api_delete_expense.py     # DELETE endpoint functional tests
│   ├── test_api_get_expenses.py       # GET endpoint functional tests
│   ├── test_csv_persistence.py        # CSV append, delete & reboot durability tests
│   ├── test_static_serving.py         # Static asset MIME & caching tests
│   ├── test_security.py               # Path traversal & CSV injection tests
│   └── test_total_calculation.py      # Floating point & sum precision tests
├── test_smart_expense_tracker.js      # Backend in-memory integration test suite (43 tests)
├── test_frontend_units.js             # Frontend unit test suite (22 tests)
├── BUGS.md                            # Documented findings & resolution records
├── package.json                       # Project metadata & npm test/start scripts
└── pytest.ini                         # Pytest configuration
```

### Technology Matrix

| Layer | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Runtime** | Node.js (LTS v18+) | Native ES Modules (`import`/`export`), high-performance async I/O. |
| **Backend Dependencies** | **None (Zero npm packages)** | Standard modules only: `node:http`, `node:fs/promises`, `node:path`, `node:crypto`. |
| **Data Persistence** | RFC 4180 CSV (`expenses.csv`) | Flat-file storage with mutex-serialized writes and atomic file renames. |
| **Frontend Runtime** | Vanilla ES6+ JavaScript | Fast, native SPA execution with ES modules in modern browsers. |
| **Frontend Styling** | Modern CSS3 | Custom CSS variables (Design Tokens), flexbox, grid, mobile-first responsive layout. |
| **Testing Frameworks** | Node.js Test Runners + **Pytest (Python 3.10+)** | Dual testing: fast in-process JS tests + independent HTTP integration tests via Pytest. |

---

## 3. Implementation Details

### 3.1 Original Implementation

The baseline implementation established a clean, layered architecture separating HTTP routing, business logic, persistence, and presentation:

1. **Native HTTP Server (`server.js`):**
   - Initializes storage directories and ensures `expenses.csv` exists with headers upon boot.
   - Listens on `PORT` (default `3000`, configurable via environment variable).
   - Handles `SIGINT` and `SIGTERM` signals for clean server shutdown.

2. **RFC 4180 State-Machine Parser (`src/utils/csvHelper.js`):**
   - Implements a robust character-by-character scanner handling multi-line quoted fields, embedded commas, double-escaped quotation marks (`""`), and CRLF (`\r\n`) line terminations.
   - Sanitizes formula injection characters (`=`, `+`, `-`, `@`) with an opening `'` escape.

3. **Mutex Concurrency Queue & Atomic Renames (`src/repositories/csvExpenseRepository.js`):**
   - Serializes file-mutating operations through an asynchronous Promise queue (`enqueueWrite`).
   - Implements atomic deletion by writing remaining rows to a temporary file (`expenses.csv.tmp`) and atomically replacing the target via `fs.rename()`, preventing read corruption during writes.

4. **Normalized Expense Business Service (`src/services/expenseService.js`):**
   - Generates collision-resistant unique identifiers: `exp-<timestamp>-<uuid8>`.
   - Normalizes amounts to 2 decimal places using `Math.round(amount * 100) / 100`.
   - Trims leading and trailing whitespace from customer names and category fields.
   - Resolves `category: "Custom"` to the user-supplied custom category label.

5. **Single-Page Application Client (`public/js/`):**
   - **`state.js`:** Centralized state repository storing active records and formatting USD currency using `Intl.NumberFormat`.
   - **`ui.js`:** Renders elements safely via `document.createElement` and `.textContent` to guarantee zero XSS vulnerability.
   - **`validator.js`:** Pure client-side validation library implementing the SRS Validation Matrix.
   - **`api.js`:** Clean Fetch API wrapper with JSON error unpacking.
   - **`app.js`:** Main controller wiring DOM event listeners (submit, delete delegation, category toggles).

---

### 3.2 Engineering Improvements & Code Review Remediations

During technical lead code review and edge case verification, six critical architectural, reliability, and security findings were identified and remediated:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             ENGINEERING IMPROVEMENTS                             │
├─────────┬──────────────┬─────────────────────────────────────────────────────────┤
│ Finding │ Component    │ Nature of Problem & Applied Solution                    │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ SEC-01  │ staticHandler│ Sibling directory traversal vulnerability fixed by      │
│         │              │ enforcing `filePath.startsWith(PUBLIC_DIR + path.sep)`. │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ BUG-01  │ validator.js │ Positive sub-cent inputs (e.g. 0.001) normalized to     │
│         │ (Client & API│ 0.00, saving invalid $0.00 expenses. Fixed by rounding  │
│         │              │ to 2 decimals before enforcing `roundedAmount > 0`.     │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ REL-01  │ httpHelper   │ Immediate `req.destroy()` during oversized requests     │
│         │              │ reset TCP socket before HTTP 413 headers sent. Fixed by │
│         │              │ pausing stream and detaching listeners gracefully.      │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ MEM-01  │ csvExpense   │ Mutex write queue retained unpruned promise closures.   │
│         │ Repository   │ Decoupled queue tail with `.catch(() => {})`.           │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ ROU-01  │ expenseRoutes│ Trailing slash on `/api/expenses/` returned 404. Added   │
│         │              │ path normalization to accept trailing slashes cleanly.  │
├─────────┼──────────────┼─────────────────────────────────────────────────────────┤
│ NUM-01  │ state.js     │ Aggregated floating-point math suffered IEEE 754 drift. │
│         │              │ Refactored accumulator to sum integer cents before      │
│         │              │ dividing by 100.                                        │
└─────────┴──────────────┴─────────────────────────────────────────────────────────┘
```

#### Detailed Remediation Breakdown:
1. **SEC-01 (Path Traversal Boundary Collision):**
   - *Previous:* `filePath.startsWith(PUBLIC_DIR)` allowed sibling folders like `/app/public_private/file.txt` to pass the check.
   - *Fix:* Updated boundary check to require `filePath.startsWith(PUBLIC_DIR + path.sep) || filePath === PUBLIC_DIR`.
2. **BUG-01 (Sub-Cent Decimal Rounding Bug):**
   - *Previous:* `amount: 0.001` passed `amount > 0` validation, but `Math.round(0.001 * 100) / 100` resulted in `0.00`, storing an invalid `$0.00` expense.
   - *Fix:* Enforced 2-decimal rounding prior to checking `roundedAmount <= 0` in both backend and frontend validators. Sub-cent amounts now return HTTP 400 (`"Please enter an amount greater than zero."`).
3. **REL-01 (Clean HTTP 413 Error Delivery):**
   - *Previous:* In `parseJsonBody()`, calling `req.destroy()` abruptly severed the TCP connection before `sendError(res, 413, ...)` could write headers.
   - *Fix:* Replaced `req.destroy()` with `req.pause()` and `req.removeAllListeners('data')`, allowing the 413 Payload Too Large response to transmit cleanly.
4. **MEM-01 (Promise Queue Memory Leak Prevention):**
   - *Previous:* Chaining `this.writeQueue = this.writeQueue.then(task, task)` retained all previous promise closures in V8 heap memory.
   - *Fix:* Detached the tail via `const next = this.writeQueue.then(() => task(), () => task()); this.writeQueue = next.catch(() => {}); return next;`.
5. **ROU-01 (Trailing Slash Resiliency):**
   - *Previous:* Requesting `GET /api/expenses/` returned 404 because of an exact string mismatch.
   - *Fix:* Stripped trailing slashes dynamically (`normalizedPath`), routing cleanly to the controller.
6. **NUM-01 (IEEE 754 Precision Accumulator):**
   - *Previous:* Summing floats like `0.10 + 0.20` resulted in `0.30000000000000004`.
   - *Fix:* Converted amounts to integer cents (`Math.round(val * 100)`), summed them, and divided by 100.

---

## 4. Testing & Quality Assurance

### 4.1 Testing Strategy

A rigorous test strategy was established across three independent layers, providing complete functional and non-functional test coverage:

```
                            ▲
                           / \
                          /   \
                         /     \
                        / Pytest \          93 Integration Tests
                       /Integration\        (Live HTTP Server, RFC 4180, Security,
                      /    Tests    \        Performance, Edge Cases EC-1 to EC-18)
                     /───────────────\
                    /  In-Memory JS   \     43 Sandboxed Integration Tests
                   / Integration Tests \    (Simulated Streams, Controllers, Repos)
                  /─────────────────────\
                 /  Frontend Unit Tests  \  22 Client Unit Tests
                /─────────────────────────\ (State Manager, Client Validator)
```

---

### 4.2 Frontend Unit Tests (`test_frontend_units.js`)
- **Scope:** Verifies the client-side validation engine (`validator.js`) and reactive state management (`state.js`).
- **Test Count:** 22 passing tests.
- **Key Assertions:**
  - Valid predefined category entries (`Food`, `Travel`, `Shopping`).
  - Valid custom category entries (`Custom` + label).
  - Validation failures for empty and whitespace-only customer names.
  - Rejection of missing, zero, negative, non-numeric, and sub-cent amounts.
  - Rejection of the unselected default category prompt (`"default"`).
  - Rejection of blank custom categories when `"Custom"` is selected.
  - State management calculations, currency formatting (`$1,250.50`), and deletion recalculation.

---

### 4.3 Backend In-Memory Integration Tests (`test_smart_expense_tracker.js`)
- **Scope:** Fast, sandboxed integration testing verifying `app(req, res)` dispatch, controllers, services, and repositories without binding real TCP network sockets.
- **Test Count:** 43 passing tests.
- **Key Assertions:**
  - Auto-initialization of `expenses.csv` with header rows.
  - CRUD REST lifecycle via mocked `Readable` request streams and `EventEmitter` responses.
  - CSV escaping of commas and quotation marks.
  - Automatic whitespace trimming of customer names.
  - Formula injection escaping with prepended `'` prefix.
  - 404 response on unknown expense IDs.
  - Static file serving and path traversal rejection.

---

### 4.4 Pytest Integration Test Suite (`tests/`)
- **Scope:** End-to-end integration tests written in Python using `pytest 9.1.1` and standard library `urllib`, running against the live running Node.js HTTP server.
- **Total Test Cases:** **93 passed in 21.18s (100% pass rate)**.
- **Fixture Strategy (`conftest.py`):**
  - `server`: Session-scoped fixture that finds a free OS ephemeral port dynamically, launches `node server.js` as a subprocess, polls `/api/expenses` until ready, and shuts down gracefully upon completion.
  - `reset_csv`: Autouse function-scoped fixture that overwrites `data/expenses.csv` with a clean RFC 4180 header row (`id,customer_name,amount,category\r\n`) before and after every individual test.

#### Test File Structure:

| Test File | Target Requirement | Test Count | Key Scenarios |
| :--- | :--- | :---: | :--- |
| [`test_edge_cases.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_edge_cases.py) | **EC-1 to EC-18** | 18 | Header-only empty database, sub-cent rounding, minimum valid amount (`$0.01`), large amounts (`$999,999.99`), 3+ decimal rounding (`45.678` -> `45.68`), comma/quote names, double deletion, empty/null JSON bodies, rapid sequential writes, oversized 1 MB payload rejection. |
| [`test_validation_matrix.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_validation_matrix.py) | **FR-2 (SRS §6)** | 20 | Verifies exact error message copy for every validation failure condition across 4 core rules. |
| [`test_api_create_expense.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_api_create_expense.py) | **FR-1, NFR-1** | 10 | Successful creation with predefined categories, custom category resolution, unique ID generation, whitespace trimming, response time < 500 ms. |
| [`test_api_delete_expense.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_api_delete_expense.py) | **FR-5** | 6 | Deletion by ID, response payload `{success: true, deletedId}`, 404 on unknown ID, precise ID targeting leaving duplicate records intact. |
| [`test_api_get_expenses.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_api_get_expenses.py) | **FR-3, NFR-1** | 8 | Empty database list `[]`, complete list retrieval, numeric type verification for `amount`, response time < 500 ms. |
| [`test_csv_persistence.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_csv_persistence.py) | **FR-6, NFR-2** | 7 | Row appending, row removal, header preservation upon full deletion, rapid sequential writes, data durability across full server reboot. |
| [`test_total_calculation.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_total_calculation.py) | **FR-4** | 4 | Zero state `$0.00`, dynamic total after adding expenses, dynamic recalculation after deletion, floating-point precision (`0.10 + 0.20 = 0.30`). |
| [`test_static_serving.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_static_serving.py) | **NFR-3** | 11 | SPA root delivery, MIME types (`text/html`, `text/css`, `application/javascript`), cache control headers, 404 for missing assets. |
| [`test_security.py`](file:///Users/olusolajeje/AI%20Vibe%20Coding%20Course%20Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker/tests/test_security.py) | **NFR-4** | 9 | Formula injection sanitization for `=`, `+`, `-`, `@`, path traversal rejection (`/../`, `%2e%2e%2f`), data directory isolation. |

---

### 4.5 Acceptance Criteria Traceability Matrix

| Requirement ID | Specification Summary | Automated Test File | Pass Rate |
| :--- | :--- | :--- | :---: |
| **FR-1** | Expense Data Entry & Custom Category Support | `test_api_create_expense.py` | 100% |
| **FR-2** | Input Validation & Error Messaging (SRS §6) | `test_validation_matrix.py` | 100% |
| **FR-3** | Line-by-Line Expense List Display | `test_api_get_expenses.py` | 100% |
| **FR-4** | Dynamic Total Amount Spent Calculation | `test_total_calculation.py` | 100% |
| **FR-5** | Targeted Deletion with Confirmation | `test_api_delete_expense.py` | 100% |
| **FR-6** | RFC 4180 CSV Persistence & Server Reboot Durability | `test_csv_persistence.py` | 100% |
| **NFR-1** | API Performance (< 500ms response time) | `test_api_get_expenses.py` & `test_api_create_expense.py` | 100% |
| **NFR-2** | Concurrency Safety & Atomic File Writes | `test_csv_persistence.py` & `test_edge_cases.py` | 100% |
| **NFR-3** | Responsive UI Layout & Static Asset MIME Types | `test_static_serving.py` | 100% |
| **NFR-4** | XSS Prevention, Formula Sanitization & Traversal Defense | `test_security.py` | 100% |

---

## 5. Setup & Execution Guide

### 5.1 Prerequisites
- **Node.js:** LTS v18.0.0 or higher (`node --version`)
- **Python:** Python 3.10 or higher with `pytest` installed (`pytest --version`)

---

### 5.2 Starting the Application

1. **Clone or navigate to the repository:**
   ```bash
   cd "/Users/olusolajeje/AI Vibe Coding Course Assignments/Day15_Prompting_For_Developers_20261022/smart_expense_tracker"
   ```

2. **Start the Node.js server:**
   ```bash
   npm start
   # or run directly:
   node server.js
   ```

3. **Access the web interface:**
   Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

*(To run on an alternate port, pass the `PORT` environment variable: `PORT=8080 node server.js`)*

---

### 5.3 Running the Tests

#### Run All Unit and In-Memory Tests (Node.js):
```bash
npm test
```
*Executes both `test_smart_expense_tracker.js` (43 tests) and `test_frontend_units.js` (22 tests).*

#### Run the Complete Pytest Integration Suite (Python):
```bash
# Runs all 93 integration tests against auto-launched Node.js server
pytest tests/ -v --tb=short
```

#### Run Specific Test Modules:
```bash
# Run edge cases only
pytest tests/test_edge_cases.py -v

# Run validation matrix tests only
pytest tests/test_validation_matrix.py -v

# Run security and injection tests only
pytest tests/test_security.py -v
```

---

## 6. Areas for Further Improvement (Future Roadmap)

While the application completely fulfills all client requirements for this release, the following architectural enhancements are identified for future enterprise iterations:

1. **Client-Side CSV Export:** Add an `"Export to CSV"` button in the table header enabling users to download their active transactions directly from the browser.
2. **Interactive Search & Filtering:** Implement dynamic table search by customer name, filter by category dropdown, and sorting by amount or date.
3. **Transaction Date Tracking:** Enhance the data dictionary to capture expense timestamps (`date_created`) with an intuitive date picker in the UI.
4. **Pagination / Virtual Scrolling:** For enterprise deployments scaling to thousands of records, introduce backend cursor-based pagination or DOM virtual scrolling to maintain <100ms render speeds.
5. **Multi-User Authentication:** Introduce session-based or JWT authentication with role-based access control (RBAC), allowing multiple users to maintain segregated expense logs.
6. **Pluggable Database Adapter:** Provide an optional relational database storage adapter (e.g. SQLite / PostgreSQL) behind the `CsvExpenseRepository` interface for high-concurrency environments.

