import { MAX_PAYLOAD_BYTES } from '../config.js';

/**
 * Reads and parses JSON payload from incoming HTTP request stream with DoS size protection.
 * @param {import('node:http').IncomingMessage} req 
 * @param {number} maxBytes 
 * @returns {Promise<any>}
 */
export function parseJsonBody(req, maxBytes = MAX_PAYLOAD_BYTES) {
  return new Promise((resolve, reject) => {
    let raw = '';
    let bytes = 0;

    req.on('data', chunk => {
      bytes += chunk.length;
      if (bytes > maxBytes) {
        req.pause();
        req.removeAllListeners('data');
        const err = new Error('Payload Too Large');
        err.statusCode = 413;
        return reject(err);
      }
      raw += chunk;
    });

    req.on('end', () => {
      if (!raw.trim()) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch {
        const err = new Error('Invalid JSON format');
        err.statusCode = 400;
        reject(err);
      }
    });

    req.on('error', reject);
  });
}

/**
 * Sends a JSON response with status code and headers.
 * @param {import('node:http').ServerResponse} res 
 * @param {number} statusCode 
 * @param {any} data 
 */
export function sendJson(res, statusCode, data) {
  const payload = JSON.stringify(data);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload)
  });
  res.end(payload);
}

/**
 * Sends a standardized error envelope: { "error": message }.
 * @param {import('node:http').ServerResponse} res 
 * @param {number} statusCode 
 * @param {string} message 
 */
export function sendError(res, statusCode, message) {
  sendJson(res, statusCode, { error: message });
}

export default {
  parseJsonBody,
  sendJson,
  sendError
};

