// public/js/app.js
import api from './api.js?v=2';
import state from './state.js';
import ui from './ui.js?v=2';
import { validateExpenseForm } from './validator.js';

class AppController {
  constructor() {
    this.init();
  }

  async init() {
    this.bindEvents();
    this.initTheme();
    await this.loadInitialData();
  }

  /**
   * Initializes the section theme from localStorage or default
   */
  initTheme() {
    try {
      const savedTheme = localStorage.getItem('smart_expense_theme') || 'default';
      ui.setSectionTheme(savedTheme);
    } catch {
      ui.setSectionTheme('default');
    }
  }

  /**
   * Attaches DOM event listeners
   */
  bindEvents() {
    // Form Submission
    ui.form.addEventListener('submit', (e) => this.handleFormSubmit(e));

    // Category Dropdown Change (Dynamic Custom Category toggle)
    ui.categorySelect.addEventListener('change', (e) => {
      ui.handleCategoryChange(e.target.value);
    });

    // Section Theme Dropdown Change (Toggles background of all three sections)
    if (ui.themeSelect) {
      ui.themeSelect.addEventListener('change', (e) => {
        const theme = e.target.value;
        ui.setSectionTheme(theme);
        try {
          localStorage.setItem('smart_expense_theme', theme);
        } catch {
          // Graceful fallback if localStorage is restricted
        }
      });
    }

    // Table Event Delegation for Delete Buttons
    ui.tableBody.addEventListener('click', (e) => {
      const deleteBtn = e.target.closest('.btn-delete');
      if (deleteBtn) {
        const id = deleteBtn.dataset.id;
        this.handleDelete(id);
      }
    });
  }

  /**
   * Loads initial expense records from backend on startup
   */
  async loadInitialData() {
    try {
      const expenses = await api.getExpenses();
      state.setExpenses(expenses);
      ui.renderList();
    } catch (err) {
      ui.showError(err.message || 'Unable to connect to the server.');
    }
  }

  /**
   * Handles expense creation workflow
   * @param {Event} event 
   */
  async handleFormSubmit(event) {
    event.preventDefault();

    const formData = ui.getFormData();
    const validation = validateExpenseForm(formData);

    // If client validation fails: show error and retain existing inputs
    if (!validation.isValid) {
      ui.showError(validation.errorMessage);
      return;
    }

    // Build payload matching backend contract
    const payload = {
      customer_name: formData.customer_name.trim(),
      amount: parseFloat(formData.amount),
      category: formData.category
    };

    if (formData.category === 'Custom') {
      payload.custom_category = formData.custom_category.trim();
    }

    try {
      ui.setSubmitting(true);
      const createdRecord = await api.createExpense(payload);

      // Success workflow
      state.addExpense(createdRecord);
      ui.clearError();
      ui.resetForm();
      ui.renderList();
    } catch (err) {
      // Backend validation or connection error
      ui.showError(err.message);
    } finally {
      ui.setSubmitting(false);
    }
  }

  /**
   * Handles expense deletion workflow
   * @param {string} id 
   */
  async handleDelete(id) {
    if (!id) return;

    // Step 1: Confirmation prompt
    const confirmed = ui.confirmDeletion();
    if (!confirmed) {
      return; // Cancelled by user: no action taken
    }

    try {
      await api.deleteExpense(id);

      // Step 2: Remove from state and re-render UI
      state.removeExpense(id);
      ui.renderList();
      ui.clearError();
    } catch (err) {
      ui.showError(err.message || 'Failed to delete expense record.');
    }
  }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  new AppController();
});

