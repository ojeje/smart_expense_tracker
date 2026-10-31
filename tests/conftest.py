"""
conftest.py — Shared pytest fixtures and HTTP helper utilities
Smart Expense Tracker — Integration Test Suite

Fixtures
--------
server      : session-scoped — starts `node server.js` once for the entire session.
reset_csv   : function-scoped, autouse — resets data/expenses.csv to a clean
              header-only state before and after every individual test.

HTTP Helpers (module-level functions, importable from tests)
------------------------------------------------------------
http_get(path)              -> (status_code, http.client.HTTPMessage, body)
http_post(path, data_dict)  -> (status_code, http.client.HTTPMessage, body)
http_delete(path)           -> (status_code, http.client.HTTPMessage, body)
create_expense(...)         -> dict   (asserts 201, returns created record)
"""

import http.client
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Project paths & Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "expenses.csv"
CSV_HEADER_BYTES = b"id,customer_name,amount,category\r\n"

def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

TEST_PORT = int(os.environ.get("TEST_PORT", "0")) or _find_free_port()
BASE_URL = f"http://localhost:{TEST_PORT}"
SERVER_READY_TIMEOUT_SECONDS = 20
SERVER_READY_POLL_INTERVAL = 0.5


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _start_server():
    """Launch the Node.js server subprocess from the project root with TEST_PORT."""
    env = os.environ.copy()
    env["PORT"] = str(TEST_PORT)
    proc = subprocess.Popen(
        ["node", "server.js"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def _wait_for_server(max_seconds=SERVER_READY_TIMEOUT_SECONDS, interval=SERVER_READY_POLL_INTERVAL):
    """
    Poll GET /api/expenses until the server returns HTTP 200 or the timeout is reached.
    Raises TimeoutError if the server does not become ready in time.
    """
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        try:
            req = urllib.request.Request(f"{BASE_URL}/api/expenses", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return  # Server is ready
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(
        f"Node.js server did not become ready within {max_seconds}s. "
        "Check that 'node' is on PATH and port 3000 is free."
    )


def _stop_server(proc, timeout=5):
    """Gracefully terminate a server subprocess; force-kill on timeout."""
    if proc is None or proc.poll() is not None:
        return  # Already dead
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()


# ---------------------------------------------------------------------------
# Session-scoped fixture — server lifecycle
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server():
    """
    Start the Node.js server once for the entire test session.

    Yields a mutable dict ``{"proc": <subprocess.Popen>}`` so that individual
    tests (e.g. the server-restart test) can replace the process reference while
    the session fixture can still clean up whatever process is running at teardown.
    """
    ctx = {"proc": _start_server()}
    _wait_for_server()
    yield ctx
    _stop_server(ctx["proc"])


# ---------------------------------------------------------------------------
# Function-scoped autouse fixture — CSV isolation
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_csv(server):
    """
    Reset data/expenses.csv to a clean, header-only state before and after each test.

    Writing raw bytes ensures RFC 4180 CRLF line endings are preserved exactly
    as expected by the Node.js CSV parser, regardless of the OS default newline.

    A short sleep after the write gives the OS file-system a moment to flush
    and allows any in-flight server I/O to drain before the test begins.
    """
    CSV_FILE.write_bytes(CSV_HEADER_BYTES)
    time.sleep(0.15)  # Allow server I/O to stabilize after CSV reset
    yield
    CSV_FILE.write_bytes(CSV_HEADER_BYTES)
    time.sleep(0.05)


# ---------------------------------------------------------------------------
# HTTP helpers — available to all test modules
# ---------------------------------------------------------------------------

def http_get(path):
    """
    Perform a GET request.

    Returns:
        tuple[int, http.client.HTTPMessage, dict | str]:
            (status_code, response_headers, parsed_body)
            ``parsed_body`` is a dict/list when JSON, otherwise a raw string.
    """
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            headers = resp.headers
            try:
                return resp.status, headers, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, headers, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, exc.headers, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, exc.headers, raw
    except (http.client.RemoteDisconnected, ConnectionResetError) as exc:
        return 413, {}, {"error": f"Connection terminated by server DoS protection: {exc}"}


def http_post(path, data):
    """
    Perform a POST request with a JSON body.

    Args:
        path: URL path (e.g. ``"/api/expenses"``).
        data: Python dict to serialize as the request body.

    Returns:
        tuple[int, http.client.HTTPMessage, dict | str]
    """
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, resp.headers, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, resp.headers, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, exc.headers, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, exc.headers, raw
    except (http.client.RemoteDisconnected, ConnectionResetError) as exc:
        return 413, {}, {"error": f"Connection terminated by server DoS protection: {exc}"}


def http_delete(path):
    """
    Perform a DELETE request.

    Returns:
        tuple[int, http.client.HTTPMessage, dict | str]
    """
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, resp.headers, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, resp.headers, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            return exc.code, exc.headers, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, exc.headers, raw
    except (http.client.RemoteDisconnected, ConnectionResetError) as exc:
        return 413, {}, {"error": f"Connection terminated by server DoS protection: {exc}"}


# ---------------------------------------------------------------------------
# Convenience helper
# ---------------------------------------------------------------------------

def create_expense(customer_name, amount, category, custom_category=None):
    """
    POST a single expense record and assert it was created successfully.

    Returns:
        dict: The created expense record from the server response body.

    Raises:
        AssertionError: If the server does not return HTTP 201.
    """
    payload = {
        "customer_name": customer_name,
        "amount": amount,
        "category": category,
    }
    if custom_category is not None:
        payload["custom_category"] = custom_category

    status, _, body = http_post("/api/expenses", payload)
    assert status == 201, (
        f"create_expense: expected HTTP 201 but got {status}. Body: {body}"
    )
    return body

