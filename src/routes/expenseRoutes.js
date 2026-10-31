import controller from '../controllers/expenseController.js';
import { sendError } from '../utils/httpHelper.js';

/**
 * Handles API route matching and delegates to ExpenseController
 * @param {import('node:http').IncomingMessage} req 
 * @param {import('node:http').ServerResponse} res 
 * @param {string} pathname 
 */
export function handleExpenseRoutes(req, res, pathname) {
  // Normalize trailing slash (e.g. /api/expenses/ -> /api/expenses)
  const normalizedPath = (pathname.length > 1 && pathname.endsWith('/')) ? pathname.slice(0, -1) : pathname;

  if (normalizedPath === '/api/expenses') {
    if (req.method === 'GET') {
      return controller.getExpenses(req, res);
    }
    if (req.method === 'POST') {
      return controller.createExpense(req, res);
    }
    return sendError(res, 405, 'Method Not Allowed');
  }

  const deleteMatch = normalizedPath.match(/^\/api\/expenses\/([^/]+)$/);
  if (deleteMatch) {
    if (req.method === 'DELETE') {
      const id = decodeURIComponent(deleteMatch[1]);
      return controller.deleteExpense(req, res, id);
    }
    return sendError(res, 405, 'Method Not Allowed');
  }

  sendError(res, 404, 'API endpoint not found.');
}

export default {
  handleExpenseRoutes
};

