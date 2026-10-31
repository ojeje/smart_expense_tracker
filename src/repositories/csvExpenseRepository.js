import fs from 'node:fs/promises';
import { CSV_FILE_PATH, TMP_CSV_FILE_PATH, DATA_DIR, CSV_HEADERS, CRLF } from '../config.js';
import { parseCsv, serializeRow } from '../utils/csvHelper.js';

class CsvExpenseRepository {
  constructor() {
    this.writeQueue = Promise.resolve();
  }

  /**
   * Enqueues mutating file write operations into a serialized Promise queue (Mutex Lock)
   * @param {() => Promise<any>} task 
   * @returns {Promise<any>}
   */
  enqueueWrite(task) {
    const next = this.writeQueue.then(() => task(), () => task());
    this.writeQueue = next.catch(() => {});
    return next;
  }

  /**
   * Auto-initializes data directory and expenses.csv on startup if missing.
   */
  async initialize() {
    await fs.mkdir(DATA_DIR, { recursive: true });
    try {
      await fs.access(CSV_FILE_PATH);
    } catch {
      // File does not exist: create with headers and CRLF delimiter
      const headerRow = CSV_HEADERS.join(',') + CRLF;
      await fs.writeFile(CSV_FILE_PATH, headerRow, 'utf-8');
    }
  }

  /**
   * Reads and parses all expense records from expenses.csv
   * @returns {Promise<Array<{id: string, customer_name: string, amount: number, category: string}>>}
   */
  async findAll() {
    try {
      const content = await fs.readFile(CSV_FILE_PATH, 'utf-8');
      const rows = parseCsv(content);
      if (rows.length <= 1) return []; // Header only or empty file

      // Skip header row
      return rows.slice(1).map(row => ({
        id: row[0],
        customer_name: row[1],
        amount: parseFloat(row[2]),
        category: row[3]
      }));
    } catch (err) {
      if (err.code === 'ENOENT') {
        await this.initialize();
        return [];
      }
      throw err;
    }
  }

  /**
   * Appends a new expense record to expenses.csv safely using the write mutex queue
   * @param {{id: string, customer_name: string, amount: number, category: string}} expense 
   * @returns {Promise<{id: string, customer_name: string, amount: number, category: string}>}
   */
  async appendRecord(expense) {
    return this.enqueueWrite(async () => {
      const rowText = serializeRow([
        expense.id,
        expense.customer_name,
        expense.amount.toFixed(2),
        expense.category
      ]);
      await fs.appendFile(CSV_FILE_PATH, rowText, 'utf-8');
      return expense;
    });
  }

  /**
   * Deletes an expense by unique ID using atomic temporary file write and rename
   * @param {string} id 
   * @returns {Promise<{success: boolean, deletedId: string}>}
   */
  async deleteById(id) {
    return this.enqueueWrite(async () => {
      const content = await fs.readFile(CSV_FILE_PATH, 'utf-8');
      const rows = parseCsv(content);

      if (rows.length <= 1) {
        const error = new Error('Expense record not found.');
        error.statusCode = 404;
        throw error;
      }

      const header = rows[0];
      const dataRows = rows.slice(1);
      const targetIndex = dataRows.findIndex(r => r[0] === id);

      if (targetIndex === -1) {
        const error = new Error('Expense record not found.');
        error.statusCode = 404;
        throw error;
      }

      // Filter out deleted row
      const remainingRows = [header, ...dataRows.filter(r => r[0] !== id)];
      const updatedCsvContent = remainingRows.map(r => serializeRow(r)).join('');

      // Atomic file write & rename to prevent corrupt partial reads
      await fs.writeFile(TMP_CSV_FILE_PATH, updatedCsvContent, 'utf-8');
      await fs.rename(TMP_CSV_FILE_PATH, CSV_FILE_PATH);

      return { success: true, deletedId: id };
    });
  }
}

export default new CsvExpenseRepository();

