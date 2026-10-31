"""
test_static_serving.py — Static File Serving Integration Tests
Smart Expense Tracker — Pytest Integration Suite

Tests the static file serving layer (NFR-3):
  - GET / serves index.html with correct MIME type and HTTP 200
  - CSS and JS assets served with correct Content-Type headers
  - Non-existent static files return 404

Covers: NFR-3 (usability/layout — correct asset delivery), Architecture §5.4
"""

from conftest import http_get


def test_root_serves_html():
    """
    NFR-3 / Architecture §5.4: GET / must serve the index.html file with
    HTTP 200 and Content-Type: text/html.
    """
    status, headers, body = http_get("/")

    assert status == 200, f"Expected 200 from GET /, got {status}"

    content_type = headers.get("Content-Type", "")
    assert "text/html" in content_type, (
        f"Expected text/html content type, got '{content_type}'"
    )


def test_root_html_contains_app_structure():
    """
    NFR-3: The served index.html must contain key structural elements that
    indicate it is the Smart Expense Tracker SPA:
    - A <title> or heading referencing the application
    - A <form> or expense-entry section
    - A script tag loading the JS module entry point
    """
    status, _, body = http_get("/")
    assert status == 200

    # Body may be bytes if not decoded; we request as text via urllib
    html = body if isinstance(body, str) else ""

    # The SPA must include the JS module entry point
    assert 'src="js/app.js"' in html or "src='/js/app.js'" in html or "app.js" in html, (
        "Expected reference to js/app.js in index.html"
    )


def test_css_served_with_correct_mime_type():
    """
    NFR-3: GET /css/styles.css must return HTTP 200 and Content-Type: text/css.
    """
    status, headers, body = http_get("/css/styles.css")

    assert status == 200, f"Expected 200 for /css/styles.css, got {status}"

    content_type = headers.get("Content-Type", "")
    assert "text/css" in content_type, (
        f"Expected text/css for styles.css, got '{content_type}'"
    )


def test_js_app_served_with_correct_mime_type():
    """
    NFR-3: GET /js/app.js must return HTTP 200 and Content-Type: application/javascript.
    """
    status, headers, body = http_get("/js/app.js")

    assert status == 200, f"Expected 200 for /js/app.js, got {status}"

    content_type = headers.get("Content-Type", "")
    assert "javascript" in content_type, (
        f"Expected application/javascript for app.js, got '{content_type}'"
    )


def test_js_state_served_correctly():
    """
    NFR-3: GET /js/state.js must be accessible and served as JavaScript.
    """
    status, headers, _ = http_get("/js/state.js")

    assert status == 200, f"Expected 200 for /js/state.js, got {status}"
    content_type = headers.get("Content-Type", "")
    assert "javascript" in content_type, (
        f"Expected javascript content type, got '{content_type}'"
    )


def test_js_api_served_correctly():
    """
    NFR-3: GET /js/api.js must be accessible and served as JavaScript.
    """
    status, headers, _ = http_get("/js/api.js")

    assert status == 200, f"Expected 200 for /js/api.js, got {status}"


def test_js_ui_served_correctly():
    """
    NFR-3: GET /js/ui.js must be accessible and served as JavaScript.
    """
    status, headers, _ = http_get("/js/ui.js")

    assert status == 200, f"Expected 200 for /js/ui.js, got {status}"


def test_js_validator_served_correctly():
    """
    NFR-3: GET /js/validator.js must be accessible and served as JavaScript.
    """
    status, headers, _ = http_get("/js/validator.js")

    assert status == 200, f"Expected 200 for /js/validator.js, got {status}"


def test_nonexistent_static_file_returns_404():
    """
    NFR-3 / Architecture: Requesting a static file that does not exist must
    return HTTP 404 (not 200 or a server crash).
    """
    status, _, body = http_get("/nonexistent-file-xyz.html")

    assert status == 404, f"Expected 404 for missing file, got {status}"


def test_html_response_has_no_cache_header():
    """
    NFR-3 / Architecture: HTML responses should include Cache-Control: no-cache
    to ensure users always receive the latest version of the SPA.
    """
    status, headers, _ = http_get("/")
    assert status == 200

    cache_control = headers.get("Cache-Control", "")
    assert "no-cache" in cache_control, (
        f"Expected Cache-Control: no-cache for HTML, got '{cache_control}'"
    )


def test_css_response_has_cache_header():
    """
    NFR-3 / Architecture: CSS responses should include a public cache header
    (max-age=3600) to allow browser caching of static assets.
    """
    status, headers, _ = http_get("/css/styles.css")
    assert status == 200

    cache_control = headers.get("Cache-Control", "")
    assert "public" in cache_control or "max-age" in cache_control, (
        f"Expected public cache header for CSS, got '{cache_control}'"
    )

