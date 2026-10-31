import { handleExpenseRoutes } from './routes/expenseRoutes.js';
import { serveStatic } from './staticHandler.js';

/**
 * Top-level HTTP request dispatcher
 * @param {import('node:http').IncomingMessage} req 
 * @param {import('node:http').ServerResponse} res 
 */
export default function app(req, res) {
  try {
    const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const pathname = parsedUrl.pathname;

    if (pathname.startsWith('/api/expenses')) {
      return handleExpenseRoutes(req, res, pathname);
    }

    return serveStatic(req, res);
  } catch (err) {
    console.error('[App] Uncaught request error:', err);
    res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'Internal server error.' }));
  }
}

