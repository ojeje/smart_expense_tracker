// public/js/api.js

const API_BASE = '/api/expenses';

class ApiService {
  /**
   * Fetches all expenses from the backend
   * @returns {Promise<Array<{id: string, customer_name: string, amount: number, category: string}>>}
   */
  async getExpenses() {
    const response = await fetch(API_BASE, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      const errorData = await this._parseError(response);
      throw new Error(errorData.error || 'Failed to retrieve expenses from server.');
    }

    return await response.json();
  }

  /**
   * Creates a new expense record on the backend
   * @param {{customer_name: string, amount: number, category: string, custom_category?: string}} payload 
   * @returns {Promise<{id: string, customer_name: string, amount: number, category: string}>}
   */
  async createExpense(payload) {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await this._parseError(response);
      throw new Error(errorData.error || 'Failed to save expense.');
    }

    return await response.json();
  }

  /**
   * Deletes an expense record by unique ID
   * @param {string} id 
   * @returns {Promise<{success: boolean, deletedId: string}>}
   */
  async deleteExpense(id) {
    const response = await fetch(`${API_BASE}/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      const errorData = await this._parseError(response);
      throw new Error(errorData.error || 'Failed to delete expense.');
    }

    return await response.json();
  }

  async _parseError(response) {
    try {
      return await response.json();
    } catch {
      return { error: `Server error: ${response.status} ${response.statusText}` };
    }
  }
}

export default new ApiService();

