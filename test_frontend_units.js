import { validateExpenseForm } from './public/js/validator.js';
import state from './public/js/state.js';

console.log('--- Starting Frontend Unit Tests (validator.js & state.js) ---');
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  PASS: ${message}`);
    passed++;
  } else {
    console.error(`  FAIL: ${message}`);
    failed++;
  }
}

// 1. Validator Tests
// Valid predefined
const v1 = validateExpenseForm({ customer_name: 'John Doe', amount: '45.50', category: 'Food' });
assert(v1.isValid === true && v1.errorMessage === null, 'Validator: Valid predefined category');

// Valid custom
const v2 = validateExpenseForm({ customer_name: 'John Doe', amount: '45.50', category: 'Custom', custom_category: 'Consulting' });
assert(v2.isValid === true && v2.errorMessage === null, 'Validator: Valid custom category');

// Invalid name (empty)
const v3 = validateExpenseForm({ customer_name: '', amount: '45.50', category: 'Food' });
assert(v3.isValid === false && v3.errorMessage === 'Please enter a valid customer name.', 'Validator: Empty customer name');

// Invalid name (whitespace)
const v4 = validateExpenseForm({ customer_name: '   ', amount: '45.50', category: 'Food' });
assert(v4.isValid === false && v4.errorMessage === 'Please enter a valid customer name.', 'Validator: Whitespace customer name');

// Invalid amount (missing)
const v5 = validateExpenseForm({ customer_name: 'John', amount: '', category: 'Food' });
assert(v5.isValid === false && v5.errorMessage === 'Please enter an amount greater than zero.', 'Validator: Missing amount');

// Invalid amount (zero)
const v6 = validateExpenseForm({ customer_name: 'John', amount: '0', category: 'Food' });
assert(v6.isValid === false && v6.errorMessage === 'Please enter an amount greater than zero.', 'Validator: Zero amount');

// Invalid amount (negative)
const v7 = validateExpenseForm({ customer_name: 'John', amount: '-10.50', category: 'Food' });
assert(v7.isValid === false && v7.errorMessage === 'Please enter an amount greater than zero.', 'Validator: Negative amount');

// Invalid amount (non-numeric)
const v8 = validateExpenseForm({ customer_name: 'John', amount: 'abc', category: 'Food' });
assert(v8.isValid === false && v8.errorMessage === 'Please enter an amount greater than zero.', 'Validator: Non-numeric amount');

// Invalid amount (sub-cent rounding to zero)
const vSubCent = validateExpenseForm({ customer_name: 'John', amount: '0.001', category: 'Food' });
assert(vSubCent.isValid === false && vSubCent.errorMessage === 'Please enter an amount greater than zero.', 'Validator: Sub-cent amount rounding to zero');

// Invalid category (default)
const v9 = validateExpenseForm({ customer_name: 'John', amount: '50', category: 'default' });
assert(v9.isValid === false && v9.errorMessage === 'Please select a category.', 'Validator: Default category prompt');

// Invalid custom category (blank)
const v10 = validateExpenseForm({ customer_name: 'John', amount: '50', category: 'Custom', custom_category: '   ' });
assert(v10.isValid === false && v10.errorMessage === 'Please enter a custom category name.', 'Validator: Blank custom category');

// 2. State Management Tests
state.setExpenses([]);
assert(state.getTotalSpent() === 0, 'State: Empty state returns 0 total');
assert(state.formatCurrency(0) === '$0.00', 'State: Format $0.00 correctly');

// Add expenses
state.addExpense({ id: '1', customer_name: 'Alice', amount: 20.00, category: 'Food' });
state.addExpense({ id: '2', customer_name: 'Bob', amount: 30.50, category: 'Travel' });
assert(state.expenses.length === 2, 'State: Two expenses added');
assert(state.getTotalSpent() === 50.50, 'State: Total spent calculated accurately ($50.50)');
assert(state.formatCurrency(state.getTotalSpent()) === '$50.50', 'State: Formatted currency is $50.50');

// Add third expense
state.addExpense({ id: '3', customer_name: 'Charlie', amount: 10.25, category: 'Shopping' });
assert(state.getTotalSpent() === 60.75, 'State: Total updated to $60.75');
assert(state.formatCurrency(state.getTotalSpent()) === '$60.75', 'State: Formatted currency is $60.75');

// Remove expense
state.removeExpense('1');
assert(state.expenses.length === 2, 'State: One expense removed');
assert(state.getTotalSpent() === 40.75, 'State: Total updated to $40.75 after deletion');
assert(state.formatCurrency(state.getTotalSpent()) === '$40.75', 'State: Formatted currency is $40.75');

// Large thousands amount formatting
assert(state.formatCurrency(1250.50) === '$1,250.50', 'State: Formats thousands with comma ($1,250.50)');

console.log(`\nFrontend Unit Tests Finished: ${passed} passed, ${failed} failed.`);
process.exit(failed > 0 ? 1 : 0);

