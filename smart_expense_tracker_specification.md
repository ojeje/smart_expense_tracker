# Smart Expense Tracker - Improved Functional Specification

## 1. Project Overview and Scope
- Project Name: Smart Expense Tracker
- Client: ABC & Co Inc
- Document Purpose: Comprehensive functional specification detailing requirements for a simple web-based expense tracking application
- Core Functionality: Entry, listing, deletion, total calculation, and file-based persistence of daily expenses

## 2. System Architecture and Browser Compatibility
- Architecture Model: Client-server web application
  - Frontend: Web client running within a web browser
  - Backend: Lightweight Node.js server managing local CSV file operations and serving application endpoints
- Browser Compatibility: Must run consistently across the latest stable versions of major web browsers:
  - Google Chrome
  - Mozilla Firefox
  - Apple Safari
  - Microsoft Edge
- Display Requirements:
  - Clean, user-friendly single-page layout
  - Form and list properly scaled and viewable on standard desktop and laptop screen resolutions

## 3. Expense Data Entry Requirements
- Input Form Placement: Located prominently at the top of the application web page
- Data Fields:
  - Customer Name:
    - Input Type: Single-line text input field
    - Requirement: Mandatory field
    - Constraints: Must not be blank; leading and trailing whitespace must be trimmed automatically
    - Placeholder Text: "Enter customer name"
  - Amount:
    - Input Type: Numeric/decimal input field
    - Currency: United States Dollar (USD)
    - Requirement: Mandatory field
    - Constraints: Must be a positive numeric value greater than zero (no zero or negative values allowed); supports up to two decimal places for cents
    - Placeholder Text: "0.00"
  - Category:
    - Input Type: Selection dropdown control with custom category entry option
    - Requirement: Mandatory selection
    - Predefined Options: "Food", "Travel", "Shopping", and "Custom"
    - Custom Category Behavior: Selecting "Custom" reveals an additional text input for the user to type their custom category name
    - Default Selection: Neutral prompt (e.g., "Select a category")
- Submission Control:
  - Control Type: Dedicated "Add Expense" submission button
  - Submission Trigger: Clicking the button or pressing the "Enter" key within input fields
  - Post-Submission Form Behavior: Clears all form fields to default states upon successful entry

## 4. Expense Display List
- Display Location: Positioned directly below the data entry form
- Layout Structure: Tabular or line-by-line list where each recorded expense appears on its own line
- Line Item Attributes:
  - Customer Name: Full entered text
  - Amount: Displayed in standard USD currency format (e.g., `$15.00`)
  - Category: Selected or custom category label
  - Action Control: Individual "Delete" button associated with that specific line item
- Display Ordering: Newest added expense line appended to the list
- Empty State: Displays a clear informational message (e.g., "No expenses recorded yet.") when no records exist

## 5. Total Amount Calculation
- Metric Display: Visible summary label showing "Total Amount Spent"
- Placement: Clearly displayed adjacent to the expense list
- Calculation Logic: Sum of the amount field across all currently recorded, active expenses
- Currency Formatting: Formatted in USD with dollar symbol and two decimal places (e.g., `$1,250.00`)
- Update Frequency: Recalculates dynamically in real time upon adding a new expense or deleting an existing expense
- Zero State: Displays `$0.00` when no expenses are present

## 6. Expense Deletion
- Deletion Control: An individual "Delete" button attached to each expense line item
- Deletion Confirmation:
  - Triggers an explicit confirmation prompt prior to executing deletion (e.g., "Are you sure you want to delete this expense?")
  - User confirmation proceeds with deletion; cancellation leaves the record unaffected
- Deletion Action (Upon Confirmation):
  - Identifies target record using its unique internal ID/timestamp
  - Removes the selected expense record from the on-screen display immediately
  - Sends a delete request to the Node.js backend to remove the specific row from `expenses.csv`
  - Triggers an immediate recalculation and update of the "Total Amount Spent"
- Scope of Deletion: Deletes only the targeted single expense item without affecting other records, even if duplicate names, amounts, or categories exist

## 7. Input Validation and Error Messaging
- Validation Trigger: Evaluated immediately upon user clicking "Add Expense" prior to record creation
- Validation Rules:
  - Empty Customer Name: Flagged if customer name is empty or contains only whitespace
  - Non-positive or Non-numeric Amount: Flagged if amount is less than or equal to zero (`<= 0`), missing, or not a valid number
  - Missing Category: Flagged if the user has not selected a valid category option
  - Empty Custom Category: Flagged if "Custom" category is selected but custom category text field is left blank or whitespace-only
- Error Messaging Display:
  - Simple, clear, human-readable error message displayed near the form area
  - Specific message text:
    - "Please enter a valid customer name."
    - "Please enter an amount greater than zero."
    - "Please select a category."
    - "Please enter a custom category name."
- Error Recovery:
  - Existing valid field inputs are preserved when an error message is triggered
  - Error message automatically clears once valid data is provided and successfully submitted

## 8. Data Storage and Persistence (CSV & Node.js Backend)
- Storage Medium: Local Comma-Separated Values (`expenses.csv`) file managed by a Node.js backend server
- Persistence Requirement: Expense data persists permanently on disk across page refreshes, browser tab closures, and server restarts
- Data Schema:
  - Column 1: `id` (Unique internal identifier / timestamp generated at creation)
  - Column 2: `customer_name` (Text string)
  - Column 3: `amount` (Numeric value in USD with up to 2 decimal places)
  - Column 4: `category` (Text string containing predefined or custom category)
- Lifecycle Handling:
  - Application Load / Initialization:
    - Web client requests all existing records from the Node.js backend
    - Node.js reads `expenses.csv` (or initializes the file with header row if not present) and returns records
    - Web client populates the display list and recalculates the total amount spent
  - Add Expense:
    - Web client sends validated expense payload to Node.js backend
    - Node.js generates unique record ID/timestamp and appends the row to `expenses.csv`
    - Web client appends the new line item to the display and updates the total amount spent
  - Delete Expense:
    - Web client sends delete request with record ID to Node.js backend
    - Node.js rewrites `expenses.csv` excluding the record matching the specified ID
    - Web client removes the line item from the display and updates the total amount spent

## 9. Client Clarifications and Architectural Decisions
- Backend Technology: Node.js runtime chosen to manage reading and writing `expenses.csv` securely and reliably
- Category Flexibility: Users are supported with both standard presets ("Food", "Travel", "Shopping") and custom category input
- Record Identity: Unique internal ID/timestamp assigned to each entry to guarantee safe and deterministic deletion
- Deletion Safety: Explicit user confirmation prompt required before executing permanent deletion
