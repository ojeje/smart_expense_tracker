import crypto from 'node:crypto';
import repo from '../repositories/csvExpenseRepository.js';

class ExpenseService {
  /**
   * Retrieves all active expense records
   * @returns {Promise<Array<{id: string, customer_name: string, amount: number, category: string}>>}
   */
  async getAllExpenses() {
    return await repo.findAll();
  }

  /**
   * Creates, validates, normalizes, and persists a new expense record
   * @param {{customer_name: string, amount: number|string, category: string, custom_category?: string}} data 
   * @returns {Promise<{id: string, customer_name: string, amount: number, category: string}>}
   */
  async createExpense(data) {
    const id = `exp-${Date.now()}-${crypto.randomUUID().substring(0, 8)}`;
    const normalizedAmount = Math.round(Number(data.amount) * 100) / 100;

    // Automatic whitespace trimming and custom category resolution
    const trimmedName = data.customer_name.trim();
    const finalCategory = data.category === 'Custom'
      ? data.custom_category.trim()
      : data.category.trim();

    const record = {
      id,
      customer_name: trimmedName,
      amount: normalizedAmount,
      category: finalCategory
    };

    await repo.appendRecord(record);
    return record;
  }

  /**
   * Deletes an expense record by unique ID
   * @param {string} id 
   * @returns {Promise<{success: boolean, deletedId: string}>}
   */
  async deleteExpense(id) {
    return await repo.deleteById(id);
  }
}

export default new ExpenseService();

