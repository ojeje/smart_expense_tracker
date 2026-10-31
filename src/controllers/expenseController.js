import service from '../services/expenseService.js';
import { parseJsonBody, sendJson, sendError } from '../utils/httpHelper.js';
import { validateExpensePayload } from '../utils/validator.js';

class ExpenseController {
  /**
   * GET /api/expenses
   */
  async getExpenses(req, res) {
    try {
      const expenses = await service.getAllExpenses();
      sendJson(res, 200, expenses);
    } catch (err) {
      console.error('[ExpenseController] getExpenses error:', err);
      sendError(res, 500, 'Internal server error while retrieving expenses.');
    }
  }

  /**
   * POST /api/expenses
   */
  async createExpense(req, res) {
    try {
      const body = await parseJsonBody(req);
      const validation = validateExpensePayload(body);

      if (!validation.isValid) {
        return sendError(res, 400, validation.errorMessage);
      }

      const created = await service.createExpense(body);
      sendJson(res, 201, created);
    } catch (err) {
      if (err.statusCode) {
        return sendError(res, err.statusCode, err.message);
      }
      console.error('[ExpenseController] createExpense error:', err);
      sendError(res, 500, 'Internal server error while saving expense.');
    }
  }

  /**
   * DELETE /api/expenses/:id
   */
  async deleteExpense(req, res, id) {
    try {
      if (!id || id.trim() === '') {
        return sendError(res, 400, 'Missing expense identifier.');
      }
      const result = await service.deleteExpense(id);
      sendJson(res, 200, result);
    } catch (err) {
      if (err.statusCode === 404) {
        return sendError(res, 404, err.message || 'Expense record not found.');
      }
      console.error('[ExpenseController] deleteExpense error:', err);
      sendError(res, 500, 'Internal server error while deleting expense.');
    }
  }
}

export default new ExpenseController();

