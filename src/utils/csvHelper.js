import { CRLF } from '../config.js';

/**
 * Neutralizes CSV formula injection in spreadsheet applications (=, +, -, @)
 * @param {any} value 
 * @returns {string}
 */
export function sanitizeFieldForCsv(value) {
  const str = typeof value === 'string' ? value : String(value ?? '');
  if (/^[=+@-]/.test(str)) {
    return `'${str}`;
  }
  return str;
}

/**
 * Escapes an individual field according to RFC 4180 rules
 * @param {any} value 
 * @returns {string}
 */
export function escapeCsvField(value) {
  const sanitized = sanitizeFieldForCsv(value);
  if (sanitized.includes('"') || sanitized.includes(',') || sanitized.includes('\n') || sanitized.includes('\r')) {
    return `"${sanitized.replace(/"/g, '""')}"`;
  }
  return sanitized;
}

/**
 * Serializes an array of field values into a CRLF-terminated CSV row
 * @param {Array<any>} fields 
 * @returns {string}
 */
export function serializeRow(fields) {
  return fields.map(escapeCsvField).join(',') + CRLF;
}

/**
 * State-machine RFC 4180 CSV parser supporting quoted strings, commas, escaped quotes, and newlines
 * @param {string} rawCsvText 
 * @returns {Array<Array<string>>}
 */
export function parseCsv(rawCsvText) {
  const rows = [];
  let currentRow = [];
  let currentField = '';
  let insideQuotes = false;

  for (let i = 0; i < rawCsvText.length; i++) {
    const char = rawCsvText[i];
    const nextChar = rawCsvText[i + 1];

    if (char === '"') {
      if (insideQuotes && nextChar === '"') {
        currentField += '"';
        i++; // skip escaped quote
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === ',' && !insideQuotes) {
      currentRow.push(currentField);
      currentField = '';
    } else if ((char === '\r' || char === '\n') && !insideQuotes) {
      if (char === '\r' && nextChar === '\n') {
        i++; // Handle CRLF
      }
      currentRow.push(currentField);
      currentField = '';
      if (currentRow.length > 0 && currentRow.some(f => f.trim() !== '')) {
        rows.push(currentRow);
      }
      currentRow = [];
    } else {
      currentField += char;
    }
  }

  if (currentField !== '' || currentRow.length > 0) {
    currentRow.push(currentField);
    if (currentRow.some(f => f.trim() !== '')) {
      rows.push(currentRow);
    }
  }

  return rows;
}

export default {
  sanitizeFieldForCsv,
  escapeCsvField,
  serializeRow,
  parseCsv
};

