# Software Requirements Specification (SRS)
## Smart Expense Tracker

**Client:** ABC & Co Inc  
**Vendor:** XYZ Software Inc  
**Author:** Product Owner, XYZ Software Inc  
**Source Specification:** `smart_expense_tracker_specification.md`  
**Version:** 1.0  
**Status:** Approved for Architectural Design  

---

## 1. Introduction and Objectives

### 1.1 Purpose
This document specifies the software requirements and acceptance criteria for the **Smart Expense Tracker**, a lightweight, reliable web application designed to enable users to record, review, delete, and persist daily expense entries.

### 1.2 Target Audience
- **Software Architect & Engineering Team:** To design the technical architecture, component interactions, API contracts, and data persistence models.
- **Quality Assurance (QA) Team:** To formulate test plans, test cases, and automated acceptance tests.
- **Client Stakeholders (ABC & Co Inc):** To confirm that functional expectations and operational constraints are fully addressed.

### 1.3 Scope of the Application
The application provides a single-page web interface backed by a Node.js server. It captures expense records (Customer Name, Amount in USD, Category), validates user inputs, renders line items directly below the input form, dynamically computes total expenditure, allows safe deletion with confirmation, and persists all records to a local CSV file (`expenses.csv`).

---

## 2. System Architecture & Operating Context

### 2.1 Architectural Pattern
- **Client-Server Architecture:**
  - **Frontend:** Responsive Single-Page Application (SPA) HTML/CSS/JavaScript running in the client's web browser.
  - **Backend:** Node.js runtime exposing RESTful HTTP endpoints and managing local disk read/write access to the CSV persistence layer.
  - **Communication:** Asynchronous HTTP/JSON communication between browser frontend and Node.js backend.

### 2.2 Browser Compatibility
The frontend must be fully functional and render consistently without errors across current stable versions of:
- Google Chrome
- Mozilla Firefox
- Apple Safari
- Microsoft Edge

### 2.3 Runtime Environment
- Standard Node.js LTS environment.
- Local filesystem access for reading and writing `expenses.csv`.
- Configurable server port (default: `3000` or process environment variable `PORT`).

---

## 3. Data Dictionary and CSV Persistence Schema

### 3.1 Data Model
Each expense record consists of the following attributes:

| Field Name | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | String | Unique, Non-empty | Unique identifier (UUID or timestamp-based ID) generated at record creation. |
| `customer_name` | String | Required, Trimmed | Name of the customer associated with the expense. |
| `amount` | Number (Float) | Required, `> 0`, 2 decimal places | Expense amount in United States Dollars (USD). |
| `category` | String | Required, Non-empty | Expense classification (Predefined or Custom). |

### 3.2 CSV File Specification (`expenses.csv`)
- **File Name:** `expenses.csv`
- **Location:** Server root directory (or designated data folder configured in backend).
- **Encoding:** UTF-8.
- **Header Row:** `id,customer_name,amount,category`
- **Special Characters:** Fields containing commas, quotes, or line breaks must follow standard RFC 4180 CSV escaping rules (enclosed in double quotes with internal quotes escaped as `""`).
- **Initialization:** If `expenses.csv` does not exist upon server start, the backend must create it with the header row.

---

## 4. Functional Requirements and Acceptance Criteria

### FR-1: Expense Data Entry & Custom Category Support
**User Story:**  
*As an expense tracking user, I want to input a customer name, an amount in USD, and a category so that I can log a new expense into the system.*

#### Functional Specifications:
1. The user interface must present an expense entry form at the top of the page containing:
   - Text input field for **Customer Name** (placeholder: "Enter customer name").
   - Numeric/decimal input field for **Amount** (placeholder: "0.00", step `0.01`).
   - Dropdown select element for **Category** with options: `Food`, `Travel`, `Shopping`, `Custom`, and a disabled default prompt `Select a category`.
   - Dynamic text input field for **Custom Category Name** displayed only when `Custom` is selected.
   - Button labeled **Add Expense** to submit the record.
2. The form must support submission via clicking the "Add Expense" button or pressing the `Enter` key within any input field.
3. Upon successful submission, input fields must be reset to their default blank/initial states.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Successful expense creation with predefined category
  Given the user is on the Smart Expense Tracker page
  When the user enters "John Doe" into Customer Name
  And enters "45.50" into Amount
  And selects "Food" from Category dropdown
  And clicks the "Add Expense" button
  Then a new expense record is saved with unique ID, "John Doe", 45.50, and "Food"
  And the form inputs are reset to their default empty states
  And the new expense appears in the expense list below

Scenario: Successful expense creation with custom category
  Given the user is on the Smart Expense Tracker page
  When the user selects "Custom" from Category dropdown
  Then a text input for Custom Category becomes visible
  When the user enters "Jane Smith" into Customer Name
  And enters "120.00" into Amount
  And enters "Software Subscription" into the Custom Category input
  And clicks "Add Expense"
  Then a new expense record is saved with category "Software Subscription"
  And the custom category input field is hidden and reset
```

---

### FR-2: Input Validation and Error Messaging
**User Story:**  
*As a user, I want clear and prompt feedback when I enter invalid expense information so that I know exactly what needs correction.*

#### Functional Specifications:
1. Validation must execute on the client side immediately upon submission before sending data to the server, and must be re-validated on the backend.
2. Validation checks:
   - **Customer Name:** Disallow empty string or string containing only whitespace.
   - **Amount:** Disallow missing, non-numeric, zero (`0`), or negative (`< 0`) values. Values must be greater than zero.
   - **Category:** Disallow unselected default prompt (`Select a category`).
   - **Custom Category:** Disallow blank/whitespace-only input when `Custom` category option is selected.
3. When validation fails:
   - Prevent submission and do not persist data.
   - Display a specific, user-friendly error message in a dedicated message area adjacent to the form.
   - Preserve existing valid field inputs so the user does not have to retype them.
4. Error message clears automatically upon the next successful submission.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario Outline: Form validation errors
  Given the user fills the form with "<Name>", "<Amount>", and "<Category>"
  When the user clicks "Add Expense"
  Then the form is not submitted
  And the error message "<ErrorMessage>" is displayed
  And existing input fields retain their entered values

  Examples:
    | Name       | Amount | Category | ErrorMessage                               |
    |            | 25.00  | Food     | Please enter a valid customer name.        |
    | "   "      | 25.00  | Food     | Please enter a valid customer name.        |
    | John Doe   |        | Food     | Please enter an amount greater than zero.  |
    | John Doe   | 0      | Food     | Please enter an amount greater than zero.  |
    | John Doe   | -15.50 | Food     | Please enter an amount greater than zero.  |
    | John Doe   | 25.00  | default  | Please select a category.                  |
    | John Doe   | 25.00  | Custom   | Please enter a custom category name.       |
```

---

### FR-3: Expense List Display
**User Story:**  
*As a user, I want to see all logged expenses displayed line-by-line directly below the input form so that I can easily review all transactions.*

#### Functional Specifications:
1. The expense list must be positioned directly underneath the expense entry form.
2. Each expense record must be displayed as a distinct row/line containing:
   - Customer Name (plain text).
   - Amount formatted in USD currency: `$X.XX` (e.g., `$45.50`, `$1,200.00`).
   - Category name (plain text).
   - An individual **Delete** action button.
3. Newly added expenses must be appended to the list.
4. When no expense records exist in the system, display a clear empty state message: `"No expenses recorded yet."`.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Displaying expense items
  Given the system has recorded expenses
  When the user views the web page
  Then each expense is rendered on its own row below the input form
  And each row displays Customer Name, Amount formatted with "$", Category, and a Delete button

Scenario: Displaying empty state
  Given no expense records exist in the system
  When the user views the web page
  Then the expense list displays "No expenses recorded yet."
  And no expense rows are shown
```

---

### FR-4: Total Amount Calculation
**User Story:**  
*As a user, I want to see the total amount of all recorded expenses so that I immediately know my aggregate spending.*

#### Functional Specifications:
1. A summary indicator labeled **Total Amount Spent** must be clearly visible adjacent to or directly above/below the expense list.
2. The total must represent the mathematical sum of all active, undeleted expense amounts.
3. The total must be formatted in USD currency (`$X.XX`, two decimal digits).
4. The total must update dynamically and instantaneously whenever:
   - Initial records are loaded from the backend.
   - A new expense is added.
   - An existing expense is deleted.
5. If no expenses exist, the total must display `$0.00`.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Dynamic total recalculation on add and delete
  Given the expense list currently contains two items: $20.00 and $30.50
  Then the "Total Amount Spent" displays "$50.50"
  When the user adds a new expense of "$10.25"
  Then the "Total Amount Spent" updates immediately to "$60.75"
  When the user deletes the "$20.00" expense
  Then the "Total Amount Spent" updates immediately to "$40.75"

Scenario: Total amount with zero records
  Given there are no recorded expenses
  Then the "Total Amount Spent" displays "$0.00"
```

---

### FR-5: Expense Deletion with Confirmation
**User Story:**  
*As a user, I want to delete an expense entry with a confirmation prompt so that I can remove unwanted records without accidental loss of data.*

#### Functional Specifications:
1. Each line item in the expense list must have an individual **Delete** button.
2. Clicking the Delete button must trigger a confirmation dialog:
   - Text: `"Are you sure you want to delete this expense?"`
   - Actions: Confirm (`OK` / `Confirm`) and Cancel (`Cancel`).
3. If the user cancels the confirmation, no changes occur.
4. If the user confirms:
   - The frontend issues a deletion request targeting the specific record's unique `id`.
   - The record is removed from `expenses.csv` on the server.
   - The line item is removed from the web page.
   - The Total Amount Spent recalculates immediately.
5. Deletion must strictly target the specific item matching `id`, preventing duplicate data (same name, amount, or category) from being deleted unintentionally.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Cancel expense deletion
  Given an expense "Jane Doe - $50.00 - Travel" is listed
  When the user clicks the "Delete" button for this item
  And chooses "Cancel" on the confirmation prompt
  Then the expense remains visible in the list
  And the CSV data remains unchanged
  And the total amount spent is not changed

Scenario: Confirm expense deletion
  Given an expense with ID "exp-123", "Jane Doe - $50.00 - Travel" is listed
  When the user clicks the "Delete" button for this item
  And chooses "OK" on the confirmation prompt
  Then the item with ID "exp-123" is removed from the display
  And the record "exp-123" is removed from "expenses.csv"
  And the total amount spent is decreased by $50.00
```

---

### FR-6: CSV Data Persistence & Application Lifecycle
**User Story:**  
*As a user, I want my expense records to persist in a CSV file so that my data is saved and reloaded whenever I close and reopen the application.*

#### Functional Specifications:
1. **Application Launch / Page Load:**
   - The web page makes a `GET` request to the backend.
   - The Node.js server reads `expenses.csv`, parses the records, and returns them as JSON.
   - The frontend renders all records and sets the Total Amount Spent.
2. **Add Expense:**
   - The frontend sends a `POST` request containing `{ customer_name, amount, category }`.
   - The backend validates the payload, generates an `id`, and appends the row to `expenses.csv`.
   - The backend responds with the saved record.
3. **Delete Expense:**
   - The frontend sends a `DELETE` request with the record `id`.
   - The backend reads `expenses.csv`, filters out the matching row, rewrites the file, and confirms deletion.
4. **Data Durability:**
   - Closing the browser tab, refreshing the page, or restarting the Node.js server must not erase persisted records.

#### Acceptance Criteria (Gherkin):
```gherkin
Scenario: Persistence across page refresh and session restart
  Given the user has added 3 expenses to the tracker
  When the user closes the browser tab and navigates back to the application URL
  Then all 3 expenses are reloaded and displayed in the list
  And the total amount spent accurately reflects the sum of all 3 expenses
```

---

## 5. Backend REST API Specifications (Guidance for Architect)

To ensure seamless integration between the frontend and Node.js backend, the following RESTful API endpoints are specified:

### 5.1 `GET /api/expenses`
- **Description:** Retrieve all active expense records from `expenses.csv`.
- **Response Status:** `200 OK`
- **Response Payload:**
  ```json
  [
    {
      "id": "1730105400000",
      "customer_name": "Alice Brown",
      "amount": 75.20,
      "category": "Travel"
    }
  ]
  ```

### 5.2 `POST /api/expenses`
- **Description:** Add a new expense record and append to `expenses.csv`.
- **Request Headers:** `Content-Type: application/json`
- **Request Payload:**
  ```json
  {
    "customer_name": "Alice Brown",
    "amount": 75.20,
    "category": "Travel"
  }
  ```
- **Response Status:** `201 Created`
- **Response Payload:** Created record including generated `id`.
- **Error Responses:** `400 Bad Request` with `{ "error": "<validation message>" }` if input data fails validation.

### 5.3 `DELETE /api/expenses/:id`
- **Description:** Delete an expense record by its unique identifier from `expenses.csv`.
- **URL Parameter:** `id` (String)
- **Response Status:** `200 OK` with `{ "success": true, "deletedId": "<id>" }`
- **Error Responses:** `404 Not Found` with `{ "error": "Expense record not found." }` if ID does not exist.

### 5.4 `GET /`
- **Description:** Serve the static single-page frontend application (`index.html`, accompanying CSS/JS).

---

## 6. Input Validation Matrix

| Field | Invalid Condition | Validation Rule | Error Message Displayed |
| :--- | :--- | :--- | :--- |
| **Customer Name** | Empty, null, or whitespace-only | Trimmed length must be `> 0` | `"Please enter a valid customer name."` |
| **Amount** | Missing, NaN, `<= 0` | Parsed float must be `> 0` | `"Please enter an amount greater than zero."` |
| **Amount** | More than 2 decimal places | Must round or validate to 2 decimals | Formatted to 2 decimal places |
| **Category** | Not selected / default prompt | Value must not be empty or `"default"` | `"Please select a category."` |
| **Custom Category**| "Custom" selected, text blank | Trimmed length must be `> 0` | `"Please enter a custom category name."` |

---

## 7. Non-Functional Requirements (NFR)

### 7.1 Performance and Responsiveness (NFR-1)
- Initial page load and expense retrieval from `expenses.csv` must complete in `< 500ms` under normal local execution conditions.
- UI DOM updates (adding row, deleting row, updating total) must be instantaneous (`< 100ms`).

### 7.2 Data Integrity and File Safety (NFR-2)
- CSV file read and write operations must be handled safely to prevent file corruption during simultaneous or rapid sequential additions/deletions.
- If `expenses.csv` does not exist upon initial execution, the server must automatically generate it with proper column headers.

### 7.3 Usability and UI Layout (NFR-3)
- The user interface must be clean, uncluttered, intuitive, and accessible without horizontal scrollbars on desktop and laptop displays (minimum width `1024px`).
- Form elements must be keyboard accessible (Tab navigation, Enter to submit).

### 7.4 Security & Input Sanitization (NFR-4)
- User inputs (`customer_name`, custom category) must be sanitized before rendering in the DOM to prevent Cross-Site Scripting (XSS).
- User inputs written to the CSV file must be properly escaped to prevent CSV injection or file structure corruption.

---

## 8. Assumptions and Boundaries

### 8.1 In-Scope
- Single-page web application.
- Node.js backend with local file system read/write to `expenses.csv`.
- Customer Name, Amount (USD), Predefined & Custom Category.
- Line-by-line expense list, total calculation, and deletion with confirmation.
- Input validation with clear error messages.

### 8.2 Out-of-Scope (Boundaries for Architect)
- Multi-user authentication, login sessions, or role-based access control.
- External SQL/NoSQL database management systems (storage is strictly CSV).
- Multi-currency conversions (system is strictly USD).
- Advanced budgeting, monthly filtering, charts, or graphical reporting.
- Cloud storage integration (data resides strictly in local `expenses.csv`).

