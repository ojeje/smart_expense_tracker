// public/js/ui.js
import state from './state.js';

class UIManager {
  constructor() {
    // Cache DOM references
    this.form = document.getElementById('expense-form');
    this.customerNameInput = document.getElementById('customer-name');
    this.amountInput = document.getElementById('amount');
    this.categorySelect = document.getElementById('category');
    this.customCategoryGroup = document.getElementById('custom-category-group');
    this.customCategoryInput = document.getElementById('custom-category');
    this.errorBanner = document.getElementById('error-banner');
    this.errorMessage = document.getElementById('error-message');
    this.totalAmountDisplay = document.getElementById('total-amount');
    this.expenseTable = document.getElementById('expense-table');
    this.tableBody = document.getElementById('expense-table-body');
    this.emptyState = document.getElementById('empty-state');
    this.submitBtn = document.getElementById('btn-submit');
    this.themeSelect = document.getElementById('theme-select');
  }

  /**
   * Sets the background color theme across all three card sections
   * @param {string} theme ('default' | 'light-gray' | 'light-blue' | 'light-green')
   */
  setSectionTheme(theme) {
    const normalizedTheme = theme || 'default';
    const palettes = {
      'default': { bg: '#ffffff', border: '#e5e7eb', titleColor: '#1f2937' },
      'light-gray': { bg: '#f1f5f9', border: '#cbd5e1', titleColor: '#1f2937' },
      'light-blue': { bg: '#e0f2fe', border: '#93c5fd', titleColor: '#0c4a6e' },
      'light-green': { bg: '#dcfce7', border: '#86efac', titleColor: '#064e3b' }
    };
    const palette = palettes[normalizedTheme] || palettes['default'];

    if (normalizedTheme === 'default') {
      document.documentElement.removeAttribute('data-theme');
      document.body.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', normalizedTheme);
      document.body.setAttribute('data-theme', normalizedTheme);
    }

    const cards = document.querySelectorAll('.card');
    cards.forEach((card) => {
      card.style.backgroundColor = palette.bg;
      card.style.borderColor = palette.border;
      const title = card.querySelector('.section-title');
      if (title) {
        title.style.borderBottomColor = palette.border;
        title.style.color = palette.titleColor;
      }
    });

    if (this.themeSelect && this.themeSelect.value !== normalizedTheme) {
      this.themeSelect.value = normalizedTheme;
    }
  }

  /**
   * Displays the error banner with the specified message
   * @param {string} message 
   */
  showError(message) {
    this.errorMessage.textContent = message;
    this.errorBanner.classList.remove('hidden');
    this.errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /**
   * Hides the error banner and clears message text
   */
  clearError() {
    this.errorMessage.textContent = '';
    this.errorBanner.classList.add('hidden');
  }

  /**
   * Dynamically toggles visibility of the Custom Category input field
   * @param {string} selectedCategory 
   */
  handleCategoryChange(selectedCategory) {
    if (selectedCategory === 'Custom') {
      this.customCategoryGroup.classList.remove('hidden');
      this.customCategoryInput.focus();
    } else {
      this.customCategoryGroup.classList.add('hidden');
      this.customCategoryInput.value = '';
    }
  }

  /**
   * Resets all form fields to their initial empty states
   */
  resetForm() {
    this.form.reset();
    this.categorySelect.value = 'default';
    this.customCategoryGroup.classList.add('hidden');
    this.customCategoryInput.value = '';
    this.customerNameInput.focus();
  }

  /**
   * Reads raw user values from the form
   * @returns {{customer_name: string, amount: string, category: string, custom_category: string}}
   */
  getFormData() {
    return {
      customer_name: this.customerNameInput.value,
      amount: this.amountInput.value,
      category: this.categorySelect.value,
      custom_category: this.customCategoryInput.value
    };
  }

  /**
   * Updates the on-screen Total Amount Spent badge
   */
  renderTotal() {
    const total = state.getTotalSpent();
    this.totalAmountDisplay.textContent = state.formatCurrency(total);
  }

  /**
   * Renders the complete expense list and updates empty state
   */
  renderList() {
    this.tableBody.innerHTML = ''; // Safe: Clearing existing table rows

    if (state.expenses.length === 0) {
      this.emptyState.classList.remove('hidden');
      this.expenseTable.classList.add('hidden');
    } else {
      this.emptyState.classList.add('hidden');
      this.expenseTable.classList.remove('hidden');

      state.expenses.forEach(item => {
        const row = this.createExpenseRow(item);
        this.tableBody.appendChild(row);
      });
    }

    this.renderTotal();
  }

  /**
   * Creates an individual table row element using safe DOM nodes (XSS Prevention)
   * @param {{id: string, customer_name: string, amount: number, category: string}} item 
   * @returns {HTMLTableRowElement}
   */
  createExpenseRow(item) {
    const tr = document.createElement('tr');
    tr.dataset.id = item.id;

    // 1. Customer Name Cell (Safe text injection)
    const tdName = document.createElement('td');
    tdName.textContent = item.customer_name;
    tr.appendChild(tdName);

    // 2. Amount Cell (Formatted currency, right-aligned)
    const tdAmount = document.createElement('td');
    tdAmount.className = 'text-right';
    tdAmount.textContent = state.formatCurrency(item.amount);
    tr.appendChild(tdAmount);

    // 3. Category Cell (Safe text injection)
    const tdCategory = document.createElement('td');
    tdCategory.textContent = item.category;
    tr.appendChild(tdCategory);

    // 4. Action / Delete Button Cell
    const tdAction = document.createElement('td');
    tdAction.className = 'text-center';

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-delete';
    deleteBtn.textContent = 'Delete';
    deleteBtn.setAttribute('type', 'button');
    deleteBtn.setAttribute('aria-label', `Delete expense for ${item.customer_name}`);
    deleteBtn.dataset.id = item.id;

    tdAction.appendChild(deleteBtn);
    tr.appendChild(tdAction);

    return tr;
  }

  /**
   * Displays the standard browser confirmation prompt
   * @returns {boolean} True if confirmed, false if cancelled
   */
  confirmDeletion() {
    return window.confirm('Are you sure you want to delete this expense?');
  }

  /**
   * Sets the submitting state of the Add Expense button
   * @param {boolean} isSubmitting 
   */
  setSubmitting(isSubmitting) {
    this.submitBtn.disabled = isSubmitting;
    this.submitBtn.textContent = isSubmitting ? 'Adding...' : 'Add Expense';
  }
}

export default new UIManager();

