// public/js/state.js

class StateManager {
  constructor() {
    this.expenses = [];
  }

  /**
   * Sets the full list of expense records (e.g. upon initial page load)
   * @param {Array<{id: string, customer_name: string, amount: number, category: string}>} records 
   */
  setExpenses(records) {
    this.expenses = Array.isArray(records) ? [...records] : [];
  }

  /**
   * Appends a newly created expense record to the state array
   * @param {{id: string, customer_name: string, amount: number, category: string}} record 
   */
  addExpense(record) {
    if (record && record.id) {
      this.expenses.push(record);
    }
  }

  /**
   * Removes an expense record matching the unique identifier
   * @param {string} id 
   */
  removeExpense(id) {
    this.expenses = this.expenses.filter(item => item.id !== id);
  }

  /**
   * Calculates the arithmetic sum of all active, undeleted expense amounts
   * @returns {number}
   */
  getTotalSpent() {
    const totalCents = this.expenses.reduce((total, item) => {
      const val = typeof item.amount === 'number' ? item.amount : parseFloat(item.amount);
      return total + (isNaN(val) ? 0 : Math.round(val * 100));
    }, 0);
    return totalCents / 100;
  }

  /**
   * Formats a numeric amount to standard USD currency format ($X.XX)
   * @param {number} amount 
   * @returns {string} e.g. "$1,250.00" or "$0.00"
   */
  formatCurrency(amount) {
    const num = typeof amount === 'number' ? amount : parseFloat(amount);
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(isNaN(num) ? 0 : num);
  }
}

export default new StateManager();

