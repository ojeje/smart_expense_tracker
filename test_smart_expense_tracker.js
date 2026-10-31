import fs from 'node:fs/promises';
import { EventEmitter } from 'node:events';
import { Readable } from 'node:stream';
import app from './src/app.js';
import repo from './src/repositories/csvExpenseRepository.js';
import { CSV_FILE_PATH, DATA_DIR } from './src/config.js';

/**
 * Creates an in-memory simulated HTTP request and response pair to test app(req, res)
 * without needing network sockets / TCP bindings.
 */
function simulateRequest(url, method = 'GET', headers = {}, body = null) {
  return new Promise((resolve) => {
    // 1. Mock Request (Readable Stream)
    const req = new Readable({
      read() {
        if (body) {
          this.push(typeof body === 'string' ? body : JSON.stringify(body));
        }
        this.push(null); // EOF
      }
    });

    req.url = url;
    req.method = method;
    req.headers = { host: 'localhost:3000', ...headers };

    // 2. Mock Response
    let statusCode = 200;
    const responseHeaders = {};
    const chunks = [];

    const res = new EventEmitter();
    res.writeHead = function (status, hdrs = {}) {
      statusCode = status;
      Object.assign(responseHeaders, hdrs);
      return res;
    };

    res.write = function (chunk) {
      if (chunk) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      return true;
    };

    res.end = function (chunk) {
      if (chunk) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      const rawBody = Buffer.concat(chunks).toString('utf-8');
      let json = null;
      try {
        json = JSON.parse(rawBody);
      } catch {
        // Not JSON
      }
      resolve({
        status: statusCode,
        headers: responseHeaders,
        text: rawBody,
        json
      });
    };

    // Dispatch to app
    app(req, res);
  });
}

async function runTests() {
  console.log('--- Starting Sandboxed In-Memory Test Suite for Smart Expense Tracker ---');
  let passed = 0;
  let failed = 0;

  function assert(condition, message) {
    if (condition) {
      console.log(`  PASS: ${message}`);
      passed++;
    } else {
      console.error(`  FAIL: ${message}`);
      failed++;
    }
  }

  try {
    // Clean up data directory for a fresh test run
    await fs.rm(DATA_DIR, { recursive: true, force: true });

    // 1. Initialize repository
    await repo.initialize();

    // Verify CSV file creation
    const fileExists = await fs.access(CSV_FILE_PATH).then(() => true).catch(() => false);
    assert(fileExists, 'data/expenses.csv was auto-created on initialization');

    const initialCsvContent = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    assert(initialCsvContent.includes('id,customer_name,amount,category'), 'CSV header row is present');

    // 2. GET /api/expenses initially empty
    const getInitial = await simulateRequest('/api/expenses', 'GET');
    assert(getInitial.status === 200, 'GET /api/expenses returns 200 OK');
    assert(Array.isArray(getInitial.json) && getInitial.json.length === 0, 'GET /api/expenses returns empty array initially');

    // 3. POST /api/expenses with predefined category
    const postPredefined = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'Alice Brown',
      amount: 75.20,
      category: 'Travel'
    });
    assert(postPredefined.status === 201, 'POST /api/expenses returns 201 Created');
    assert(postPredefined.json && postPredefined.json.id, 'Created record contains generated unique id');
    assert(postPredefined.json.customer_name === 'Alice Brown', 'Created record preserves customer_name');
    assert(postPredefined.json.amount === 75.2, 'Created record preserves normalized amount');
    assert(postPredefined.json.category === 'Travel', 'Created record preserves category');
    const firstId = postPredefined.json.id;

    // 4. POST /api/expenses with custom category
    const postCustom = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'Bob Smith',
      amount: 120.00,
      category: 'Custom',
      custom_category: 'Software Subscription'
    });
    assert(postCustom.status === 201, 'POST /api/expenses with Custom category returns 201 Created');
    assert(postCustom.json.category === 'Software Subscription', 'Resolved category is Software Subscription');
    const secondId = postCustom.json.id;

    // 5. GET /api/expenses returns 2 items
    const getTwo = await simulateRequest('/api/expenses', 'GET');
    assert(getTwo.status === 200, 'GET /api/expenses returns 200 OK');
    assert(getTwo.json && getTwo.json.length === 2, 'GET /api/expenses contains 2 expense records');

    // 6. Verify CSV persistence on disk
    const diskCsv = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    assert(diskCsv.includes('Alice Brown'), 'CSV file on disk contains Alice Brown');
    assert(diskCsv.includes('Bob Smith'), 'CSV file on disk contains Bob Smith');
    assert(diskCsv.includes('Software Subscription'), 'CSV file on disk contains Software Subscription');

    // 7. Test Validation Matrix Errors
    // Empty Name
    const errName = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: '   ',
      amount: 50,
      category: 'Food'
    });
    assert(errName.status === 400, 'Blank customer name returns 400 Bad Request');
    assert(errName.json && errName.json.error === 'Please enter a valid customer name.', 'Error message: Please enter a valid customer name.');

    // Zero Amount
    const errZero = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'John',
      amount: 0,
      category: 'Food'
    });
    assert(errZero.status === 400, 'Zero amount returns 400 Bad Request');
    assert(errZero.json && errZero.json.error === 'Please enter an amount greater than zero.', 'Error message: Please enter an amount greater than zero.');

    // Negative Amount
    const errNeg = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'John',
      amount: -15.5,
      category: 'Food'
    });
    assert(errNeg.status === 400, 'Negative amount returns 400 Bad Request');
    assert(errNeg.json && errNeg.json.error === 'Please enter an amount greater than zero.', 'Error message: Please enter an amount greater than zero.');

    // Missing Category
    const errCat = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'John',
      amount: 25,
      category: 'default'
    });
    assert(errCat.status === 400, 'Default category returns 400 Bad Request');
    assert(errCat.json && errCat.json.error === 'Please select a category.', 'Error message: Please select a category.');

    // Blank Custom Category
    const errCustom = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: 'John',
      amount: 25,
      category: 'Custom',
      custom_category: '   '
    });
    assert(errCustom.status === 400, 'Blank custom category returns 400 Bad Request');
    assert(errCustom.json && errCustom.json.error === 'Please enter a custom category name.', 'Error message: Please enter a custom category name.');

    // 8. Formula Injection Defense
    const postFormula = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: '=SUM(A1:A5)',
      amount: 10,
      category: 'Food'
    });
    assert(postFormula.status === 201, 'Formula injection string accepted as text');
    const formulaCsv = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    assert(formulaCsv.includes("'=SUM(A1:A5)"), 'Formula injection operator was escaped with prepended single quote in CSV');

    // 9. Whitespace Trimming
    const postTrim = await simulateRequest('/api/expenses', 'POST', { 'Content-Type': 'application/json' }, {
      customer_name: '   Charlie Chaplin   ',
      amount: 20,
      category: 'Shopping'
    });
    assert(postTrim.status === 201, 'Trimmable customer name accepted');
    assert(postTrim.json && postTrim.json.customer_name === 'Charlie Chaplin', 'Customer name was trimmed in JSON response');
    const trimCsv = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    assert(trimCsv.includes('Charlie Chaplin') && !trimCsv.includes('   Charlie Chaplin'), 'Customer name was trimmed in CSV on disk');

    // 10. DELETE /api/expenses/:id
    const delRes = await simulateRequest(`/api/expenses/${firstId}`, 'DELETE');
    assert(delRes.status === 200, 'DELETE /api/expenses/:id returns 200 OK');
    assert(delRes.json && delRes.json.success === true, 'DELETE response contains success: true');
    assert(delRes.json && delRes.json.deletedId === firstId, 'DELETE response contains deletedId');

    // Verify deletion reflected in GET
    const afterDel = await simulateRequest('/api/expenses', 'GET');
    assert(!afterDel.json.some(item => item.id === firstId), 'Deleted expense is no longer present in GET /api/expenses');

    // Verify deletion reflected in CSV file
    const postDelCsv = await fs.readFile(CSV_FILE_PATH, 'utf-8');
    assert(!postDelCsv.includes('Alice Brown'), 'Alice Brown was removed from CSV file on disk');

    // DELETE non-existent ID -> 404
    const del404 = await simulateRequest('/api/expenses/non-existent-id', 'DELETE');
    assert(del404.status === 404, 'DELETE non-existent ID returns 404 Not Found');
    assert(del404.json && del404.json.error === 'Expense record not found.', 'Error message: Expense record not found.');

    // 11. Static File Serving
    const getIndex = await simulateRequest('/', 'GET');
    assert(getIndex.status === 200, 'GET / serves 200 OK');
    assert(getIndex.text.includes('Smart Expense Tracker'), 'index.html contains app title');

    const getCss = await simulateRequest('/css/styles.css', 'GET');
    assert(getCss.status === 200, 'GET /css/styles.css serves 200 OK');
    assert(getCss.text.includes('--primary'), 'styles.css contains design tokens');

    // Path traversal attempt
    const getTraverse = await simulateRequest('/../package.json', 'GET');
    assert(getTraverse.status === 403 || getTraverse.status === 404, 'Path traversal attempt is rejected (403 or 404)');

  } catch (err) {
    console.error('Fatal error during test run:', err);
    failed++;
  } finally {
    console.log(`\nTest Suite Finished: ${passed} passed, ${failed} failed.`);
    process.exit(failed > 0 ? 1 : 0);
  }
}

runTests();
