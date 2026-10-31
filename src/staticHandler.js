import fs from 'node:fs';
import path from 'node:path';
import { PUBLIC_DIR } from './config.js';
import { sendError } from './utils/httpHelper.js';

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml'
};

/**
 * Streams static assets from the public directory with path traversal protection
 * @param {import('node:http').IncomingMessage} req 
 * @param {import('node:http').ServerResponse} res 
 */
export async function serveStatic(req, res) {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ error: 'Method Not Allowed' }));
  }

  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = decodeURIComponent(parsedUrl.pathname);
  if (pathname === '/') pathname = '/index.html';

  const safePath = path.normalize(pathname).replace(/^(\.\.[/\\])+/, '');
  const filePath = path.join(PUBLIC_DIR, safePath);

  // Security check: ensure path is strictly within PUBLIC_DIR (prevent prefix collisions)
  const isWithinPublic = filePath.startsWith(PUBLIC_DIR + path.sep) || filePath === PUBLIC_DIR;
  if (!isWithinPublic) {
    return sendError(res, 403, 'Forbidden');
  }

  try {
    const stats = await fs.promises.stat(filePath);
    if (!stats.isFile()) {
      return sendError(res, 404, 'File Not Found');
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': contentType,
      'Content-Length': stats.size,
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=0, must-revalidate'
    });

    if (req.method === 'HEAD') {
      return res.end();
    }

    fs.createReadStream(filePath).pipe(res);
  } catch (err) {
    if (err.code === 'ENOENT') {
      return sendError(res, 404, 'File Not Found');
    }
    console.error('[StaticHandler] Error serving file:', err);
    sendError(res, 500, 'Internal Server Error');
  }
}

export default {
  serveStatic
};

