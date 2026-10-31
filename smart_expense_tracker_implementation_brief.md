# Smart Expense Tracker - Implementation Brief & Execution Plan

**Author:** Full-Stack Developer, XYZ Software Inc  
**Client:** ABC & Co Inc  
**Target Reviewers & Approvers:** Product Owner, Software Architect, Frontend Developer, Backend Developer  
**Governing Documents Reviewed & Aligned:**
1. `smart_expense_tracker_specification.md` (Client Product Specification)
2. `smart_expense_tracker_requirements.md` (Software Requirements Specification - SRS v1.0)
3. `smart_expense_tracker_software_architecture.md` (Converged Software Architecture Document v2.0)
4. `smart_expense_tracker_backend_design.md` (Backend Technical Design Document v2.0)
5. `smart_expense_tracker_frontend_design.md` (Frontend Technical Design Document v1.0)  
**Version:** 1.0  
**Status:** Awaiting Approval to Begin Implementation  

---

## 1. Executive Summary & Verification of Stakeholder Documents

As the Full-Stack Developer assigned to implement the **Smart Expense Tracker**, I have conducted an exhaustive, cross-disciplinary audit of all five project specification, architecture, and design documents.

### 1.1 Cross-Document Consistency Audit
- **Architecture & Runtime Model:** Both frontend and backend design documents adhere strictly to the Converged Software Architecture. Pure native Node.js (LTS v18+) backend with zero external dependencies and native ES Modules (`"type": "module"`), paired with a zero-build Vanilla HTML5/CSS3/ES6+ SPA frontend.
- **Data Persistence & Format:** Data is persisted to `data/expenses.csv` with standard RFC 4180 CRLF (`\r\n`) row delimiters, managed through a sequential promise mutex queue and atomic file rename (`expenses.csv.tmp` $\rightarrow$ `expenses.csv`).
- **REST API & Schema Contracts:** Interface contracts for `GET /api/expenses`, `POST /api/expenses`, and `DELETE /api/expenses/:id` are perfectly synchronized between `api.js` and `expenseRoutes.js`/`expenseController.js`.
- **Validation Matrix Consistency:** Exact error strings and validation rules match across the SRS, architecture, backend validator, and frontend validator.
- **Security & Integrity:** Sanitization against Cross-Site Scripting (XSS) via `textContent` DOM nodes, formula injection neutralization via prepended single quote (`'`), path traversal guards on static asset requests, and a 1MB payload DoS buffer guard are uniformly defined.

### 1.2 Status of Stakeholder Questions
All previous architectural and design questions have been fully answered and confirmed by the respective stakeholders:
- **Product Owner:** Confirmed pure native Node.js (no Express), browser `window.confirm()` dialog, whitespace trimming, and `data/expenses.csv` data segregation.
- **Software Architect:** Confirmed native ES Modules (`import`/`export`) and RFC 4180 CRLF line delimiters.
- **Frontend Developer:** Confirmed client-side `state.js` currency formatting, dynamic custom category toggling, and `public/` directory asset layout.
- **Backend Developer:** Confirmed JSON number `amount` format, `{ category: "Custom", custom_category: "..." }` payload structure, and atomic file safety.

**Conclusion:** No unresolved ambiguities or discrepancies remain. The implementation plan is ready for final sign-off.

---

## 2. Target File Structure & Module Responsibilities

The codebase will be constructed strictly according to the approved directory map:

```
smart_expense_tracker/
├── package.json                                 # Manifest with "type": "module" and start script (zero dependencies)
├── server.js                                    # Application bootstrap, CSV repo initialization, HTTP server listener
├── src/                                         # Native Node.js Backend Tier
│   ├── app.js                                   # Top-level HTTP request dispatcher (Static files vs. REST API routes)
│   ├── config.js                                # System constants (PORT, file paths, header schemas, CRLF)
│   ├── staticHandler.js                         # Secure static asset streamer with MIME mapping & path traversal guards
│   ├── routes/
│   │   └── expenseRoutes.js                     # REST API route matcher for /api/expenses
│   ├── controllers/
│   │   └── expenseController.js                 # HTTP request payload extraction, validation dispatch, status output
│   ├── services/
│   │   └── expenseService.js                    # Domain logic, UUID assignment via node:crypto, decimal normalization
│   ├── repositories/
│   │   └── csvExpenseRepository.js             # Mutex promise queue, RFC 4180 parsing/serializing, atomic file rewrite
│   └── utils/
│       ├── httpHelper.js                        # JSON request body reader with 1MB DoS guard & standard JSON response helpers
│       ├── csvHelper.js                         # RFC 4180 parser/serializer & spreadsheet formula injection sanitizer
│       └── validator.js                         # Server-side validation enforcing the exact SRS Validation Matrix
├── public/                                      # Browser Frontend Tier (Zero-Build Vanilla SPA)
│   ├── index.html                               # Semantic single-page HTML layout
│   ├── css/
│   │   └── styles.css                           # Responsive CSS styling (Grid/Flexbox, Form, Table, Badges, Media queries)
│   └── js/
│       ├── app.js                               # Application bootstrap & DOM event orchestrator
│       ├── api.js                               # Fetch API wrapper for /api/expenses
│       ├── state.js                             # In-memory reactive state store, USD formatter & real-time total calculator
│       ├── ui.js                                # DOM rendering engine, error alerts, custom category toggle, confirm dialog
│       └── validator.js                         # Client-side input validator enforcing the exact SRS Validation Matrix
├── data/                                        # Data Isolation Directory
│   └── expenses.csv                             # Persistent CSV data storage (auto-initialized on startup if missing)
├── smart_expense_tracker_specification.md        # Customer Functional Specification
├── smart_expense_tracker_requirements.md         # Software Requirements Specification (SRS v1.0)
├── smart_expense_tracker_software_architecture.md # Converged Software Architecture Document (v2.0)
├── smart_expense_tracker_backend_design.md       # Backend Technical Design Document (v2.0)
├── smart_expense_tracker_frontend_design.md      # Frontend Technical Design Document (v1.0)
└── smart_expense_tracker_implementation_brief.md # Implementation Brief & Execution Plan (this document)
```

---

## 3. Implementation Specifications by Tier

### 3.1 Backend Tier Implementation Plan

1. **`package.json`:**
   - Define `"type": "module"`.
   - Script: `"start": "node server.js"`.
   - Empty `"dependencies": {}`.
2. **`src/config.js`:**
   - Resolve absolute paths using `fileURLToPath(import.meta.url)` and `path.dirname()`.
   - Define `PORT = parseInt(process.env.PORT, 10) || 3000`.
   - Define `DATA_DIR`, `CSV_FILE_PATH`, `TMP_CSV_FILE_PATH`, `PUBLIC_DIR`, `MAX_PAYLOAD_BYTES` (1MB), `CSV_HEADERS` (`id,customer_name,amount,category`), and `CRLF` (`\r\n`).
3. **`src/utils/httpHelper.js`:**
   - `parseJsonBody(req, maxBytes)`: Buffer stream with 1MB threshold; reject with `413 Payload Too Large` if exceeded; safely parse JSON or reject with `400 Bad Request`.
   - `sendJson(res, statusCode, data)`: Send UTF-8 JSON with `Content-Type` and `Content-Length`.
   - `sendError(res, statusCode, message)`: Envelope `{ "error": message }`.
4. **`src/utils/csvHelper.js`:**
   - `sanitizeFieldForCsv(value)`: Prepend `'` if value begins with `=`, `+`, `-`, or `@`.
   - `escapeCsvField(value)`: Quote fields containing `"`, `,`, `\n`, or `\r`; escape internal quotes as `""`.
   - `serializeRow(fields)`: Join fields with comma and terminate with CRLF (`\r\n`).
   - `parseCsv(rawCsvText)`: State-machine parser parsing quoted fields with internal commas, quotes, and newlines.
5. **`src/utils/validator.js`:**
   - Enforce customer name non-empty after trimming (`"Please enter a valid customer name."`).
   - Enforce amount is valid number and $> 0$ (`"Please enter an amount greater than zero."`).
   - Enforce category selected and not `"default"` (`"Please select a category."`).
   - Enforce custom category non-empty when category is `"Custom"` (`"Please enter a custom category name."`).
6. **`src/repositories/csvExpenseRepository.js`:**
   - `initialize()`: Ensure `data/` directory exists; create `expenses.csv` with header if missing.
   - `findAll()`: Read `data/expenses.csv`, parse rows, map to objects skipping header.
   - `appendRecord(expense)`: Serialize row and append to file using sequential mutex promise chain.
   - `deleteById(id)`: Filter matching row, write remaining rows to `expenses.csv.tmp`, atomic rename to `expenses.csv`. Throw `404` if ID not found.
7. **`src/services/expenseService.js`:**
   - Assign unique ID: `exp-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`.
   - Normalize amount to 2 decimal places (`Math.round(val * 100) / 100`).
   - Auto-trim customer name and resolve custom category.
8. **`src/controllers/expenseController.js`:**
   - Handlers for `getExpenses`, `createExpense`, and `deleteExpense` mapping to status codes `200`, `201`, `400`, `404`, `500`.
9. **`src/staticHandler.js`:**
   - Resolve requested path relative to `public/`.
   - Enforce `filePath.startsWith(PUBLIC_DIR)` to strictly prevent `../` path traversal.
   - Stream static assets with proper MIME types (`text/html`, `text/css`, `application/javascript`, `image/x-icon`).
10. **`src/routes/expenseRoutes.js` & `src/app.js`:**
    - Route `/api/expenses` (`GET`, `POST`) and `/api/expenses/:id` (`DELETE`).
    - Dispatch static file serving for non-API routes.
11. **`server.js`:**
    - Initialize CSV persistence repository before calling `http.createServer(app).listen(PORT)`.
    - Handle `SIGINT` and `SIGTERM` for graceful server shutdown.

---

### 3.2 Frontend Tier Implementation Plan

1. **`public/index.html`:**
   - Semantic single-page HTML layout with:
     - Header and subheadings.
     - `#error-banner` container (hidden by default, `role="alert"`).
     - `#expense-form` with `#customer-name`, `#amount` (`step="0.01"`), `#category` dropdown, `#custom-category-group` (hidden by default), and `#btn-submit`.
     - `#total-heading` and `#total-amount` spent badge.
     - `#empty-state` placeholder (`"No expenses recorded yet."`).
     - `#expense-table` with columns: Customer Name, Amount (USD), Category, Action.
   - Include `<script type="module" src="js/app.js"></script>`.
2. **`public/css/styles.css`:**
   - Responsive CSS layout (maximum container width `960px`, CSS Grid form layout, responsive breakpoints at 640px).
   - High-contrast focus outlines, hover states, card elevation, error banner, and table styles.
3. **`public/js/state.js`:**
   - In-memory `expenses` array.
   - `getTotalSpent()`: Arithmetic sum of active expense amounts.
   - `formatCurrency(amount)`: Formats numbers using `Intl.NumberFormat` to `$X.XX` with commas for thousands.
4. **`public/js/validator.js`:**
   - Client-side validation enforcing the exact 4 validation rules and returning `{ isValid, errorMessage }`.
5. **`public/js/api.js`:**
   - Fetch wrapper methods: `getExpenses()`, `createExpense(payload)`, and `deleteExpense(id)`.
6. **`public/js/ui.js`:**
   - `createExpenseRow(item)`: Construct DOM rows using `document.createElement` and `textContent` for XSS protection.
   - `showError(message)` / `clearError()`: Manage error banner visibility.
   - `handleCategoryChange(val)`: Dynamically toggle visibility of `#custom-category-group`.
   - `confirmDeletion()`: Trigger native `window.confirm("Are you sure you want to delete this expense?")`.
   - `renderList()` / `renderTotal()`: Synchronize DOM with state.
7. **`public/js/app.js`:**
   - Initialize on `DOMContentLoaded`, fetch initial data, bind submit listener and delete event delegation.

---

## 4. Requirements Traceability Matrix

Every requirement and acceptance criteria from `smart_expense_tracker_requirements.md` is mapped to its concrete implementation:

| Req ID | Requirement Description | Implementation Modules | Verification Method |
| :--- | :--- | :--- | :--- |
| **FR-1** | Expense Data Entry & Custom Category | `index.html`, `ui.js`, `app.js`, `expenseController.js` | Form submits predefined/custom categories; inputs reset to initial blank state. |
| **FR-2** | Input Validation & Error Messaging | `validator.js` (client & server), `ui.js` | Test all 4 invalid inputs; verify exact error copy; verify field values are preserved. |
| **FR-3** | Expense List Display | `index.html`, `ui.js`, `styles.css` | Verify row rendered below form with Name, `$X.XX`, Category, Delete; verify empty state text. |
| **FR-4** | Total Amount Calculation | `state.js`, `ui.js` | Verify dynamic recalculation on initial load, add expense, and delete expense; `$0.00` on empty. |
| **FR-5** | Deletion with Confirmation | `ui.js`, `app.js`, `csvExpenseRepository.js` | `window.confirm()` prompted; Cancel does nothing; OK deletes specific item by unique ID. |
| **FR-6** | CSV Persistence & Lifecycle | `csvExpenseRepository.js`, `csvHelper.js` | Reload browser and restart server; verify records persist in `data/expenses.csv`. |
| **NFR-1** | Performance & Responsiveness | Pure native Node.js & Vanilla JS | Direct file I/O latency $< 500\text{ms}$; instant DOM reactivity $< 100\text{ms}$. |
| **NFR-2** | Data Integrity & File Safety | `csvExpenseRepository.js` (Mutex + Atomic Rename) | Sequential queue prevents race conditions; atomic rename prevents partial writes. |
| **NFR-3** | Usability & Accessibility | `styles.css`, `index.html` | Keyboard accessible form; responsive on laptop/desktop $\ge 1024\text{px}$ and mobile. |
| **NFR-4** | Security & Input Sanitization | `ui.js` (`textContent`), `csvHelper.js`, `staticHandler.js` | XSS prevented via `textContent`; formula injection sanitized; path traversal guarded. |

---

## 5. Phased Implementation Roadmap

1. **Phase 1: Project Environment & Backend Core**
   - Create `package.json` (`"type": "module"`, zero external dependencies).
   - Create `src/config.js` with directory paths, port, and CSV header constants.
   - Create `src/utils/httpHelper.js`, `src/utils/csvHelper.js`, and `src/utils/validator.js`.
2. **Phase 2: Data Persistence & Business Logic**
   - Create `src/repositories/csvExpenseRepository.js` with auto-initialization, mutex write queue, and atomic file replacement.
   - Create `src/services/expenseService.js` and `src/controllers/expenseController.js`.
3. **Phase 3: HTTP Server & Routing**
   - Create `src/staticHandler.js` with MIME stream resolution and path traversal security guards.
   - Create `src/routes/expenseRoutes.js`, `src/app.js`, and `server.js`.
4. **Phase 4: Frontend User Interface**
   - Create `public/index.html` with semantic structure and accessibility attributes.
   - Create `public/css/styles.css` with responsive layout and design tokens.
   - Create `public/js/state.js`, `public/js/validator.js`, `public/js/api.js`, `public/js/ui.js`, and `public/js/app.js`.
5. **Phase 5: Automated & Manual End-to-End Verification**
   - Verify server boot and auto-creation of `data/expenses.csv`.
   - Execute CLI `curl` tests for `GET`, `POST` (predefined & custom), and `DELETE`.
   - Run end-to-end browser tests verifying form inputs, validation error banners, total spent calculations, confirmation dialogs, and persistence across server restarts.

---

## 6. Formal Request for Approval

All cross-stakeholder requirements, architectural constraints, and interface designs have been fully harmonized. 

**I request formal approval to proceed with executing the implementation according to this brief.**

