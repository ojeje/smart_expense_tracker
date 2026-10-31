import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const ROOT_DIR = path.resolve(__dirname, '..');
export const PORT = parseInt(process.env.PORT, 10) || 3000;
export const DATA_DIR = path.join(ROOT_DIR, 'data');
export const CSV_FILE_PATH = path.join(DATA_DIR, 'expenses.csv');
export const TMP_CSV_FILE_PATH = path.join(DATA_DIR, 'expenses.csv.tmp');
export const PUBLIC_DIR = path.join(ROOT_DIR, 'public');
export const MAX_PAYLOAD_BYTES = 1024 * 1024; // 1MB DoS safety ceiling
export const CSV_HEADERS = ['id', 'customer_name', 'amount', 'category'];
export const CRLF = '\r\n';

export default {
  ROOT_DIR,
  PORT,
  DATA_DIR,
  CSV_FILE_PATH,
  TMP_CSV_FILE_PATH,
  PUBLIC_DIR,
  MAX_PAYLOAD_BYTES,
  CSV_HEADERS,
  CRLF
};

