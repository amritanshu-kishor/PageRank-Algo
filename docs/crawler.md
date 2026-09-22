# Hardened Web Crawler Documentation

This document specifies the architecture, normalization rules, domain boundary contracts, failure policies, and testing strategy for the hardened web crawler in Phase 1 — Step 6.

---

## 1. Overview & Purpose

The web crawler ([`backend/crawler.py`](file:///d:/pagerank/backend/crawler.py)) performs same-host Breadth-First Search (BFS) graph discovery starting from a seed URL. It converts web page hyper-link structures into a clean, normalized, directed graph representation `{"pages": [...], "links": [...]}` that directly satisfies the Step 4 graph contract ([`backend/graph_validator.py`](file:///d:/pagerank/backend/graph_validator.py)).

```text
Seed URL
   │
   ▼
normalize_url()  ──► Establish Root Host Boundary
   │
   ▼
BFS Queue Execution (Bounded by max_pages & timeout)
   │
   ├─► fetch_html() [Validate Status < 400, Content-Type text/html, On-Host Redirect]
   ├─► extract_links() [Resolve Relative URLs, Filter Non-HTTP Schemes]
   └─► Normalize & Filter Target URLs (Same-Host Only)
   │
   ▼
Deduplicated, Sorted Directed Graph JSON + Metadata
```

---

## 2. Specification & Contracts

### 2.1 Input Parameters
- **`start_url`** (`str`): Seed URL string (e.g., `"https://example.com"`). Prepend `https://` if no scheme provided. Raises `ValueError` if invalid.
- **`max_pages`** (`int`): Maximum number of unique pages to process (clamped $\ge 1$, default 12).

### 2.2 Output Contract
Returns a Python `dict` containing:
```python
{
    "pages": ["https://example.com/", "https://example.com/about"],
    "links": [["https://example.com/", "https://example.com/about"]],
    "pages_crawled": 2,
    "pages_failed": 0,
    "start_url": "https://example.com/",
    "max_pages": 12
}
```

---

## 3. Core Behaviors & Edge-Case Policies

### 3.1 URL Normalization (`normalize_url`)
- **Scheme**: Lowercase `http` or `https`. Scheme-relative URLs (`//example.com/page`) prepend `https:`. Non-HTTP schemes (`javascript:`, `mailto:`, `tel:`, `data:`, `file:`, `ftp:`) return `None`.
- **Fragments**: Stripped via `urldefrag` (`/page#sec1` $\to$ `/page`).
- **Host**: Lowercase netloc string. Default ports (`:80` for HTTP, `:443` for HTTPS) stripped.
- **Path**: Path trailing slashes stripped for non-root paths (`/about/` $\to$ `/about`). Root path `/` preserved.
- **Query Strings**: Preserved in canonical format (`/search?q=1`).

### 3.2 Host / Domain Boundary (`is_same_host`)
- Strict exact host matching (`get_effective_host(url) == root_host`).
- Excludes off-domain targets (e.g. `google.com`), sub-domains (unless seed was that sub-domain), and similar-looking malicious domains (e.g. `example.com.evil.com`).

### 3.3 Relative Link Resolution (`extract_links`)
- Resolves `/about`, `../contact`, `./team` relative to response URL using `urllib.parse.urljoin`.

### 3.4 Response Validation & Content-Type
- Validates `HTTP status_code < 400`.
- Requires `Content-Type` header containing `text/html` or `application/xhtml+xml`. Non-HTML resources (`image/png`, `application/pdf`, `application/zip`, etc.) are ignored.

### 3.5 Redirect Handling
- Follows HTTP redirects (`allow_redirects=True`).
- Evaluates `response.url` (final URL). If redirect targets an off-domain URL (e.g. `google.com`), the response is rejected and not crawled.

### 3.6 Timeout & Failure Resilience
- Enforces `REQUEST_TIMEOUT = 8` seconds per request.
- Handles `requests.RequestException` (timeouts, 4xx, 5xx, DNS failures, connection errors) without crashing the crawl loop. Failed URLs are recorded in metadata.

### 3.7 Duplicate Edge & Page Handling
- `visited` and `queued` sets prevent re-fetching normalized URLs.
- Edge tuple set `links` prevents duplicate directed edges.

### 3.8 Deterministic Ordering
- Crawl traversal follows FIFO deque order. Link extraction follows DOM anchor order.
- Returned `pages` and `links` arrays are sorted lexicographically before returning.

### 3.9 Step 4 Validator Compatibility
- Output strictly satisfies the `graph_validator.py` specification (non-empty string node IDs, 2-element lists `[source, target]`, all edge endpoints present in `pages`).

---

## 4. Security & Safety Boundaries

- **No SSRF / Intranet Scanning**: Restricted to explicit HTTP/HTTPS schemes on target seed host.
- **No JS Execution / Headless Browsers**: Static HTML parsing only via BeautifulSoup4.
- **No Credentials / Auth Bypass**: Public navigation targets only.
- **Bounded Requests**: Strict page count (`max_pages`) and bounded request timeouts prevent runaway resource usage.

---

## 5. Test Strategy

All unit and integration tests ([`tests/test_crawler.py`](file:///d:/pagerank/tests/test_crawler.py)) use deterministic mocked HTTP responses via `unittest.mock.patch("requests.Session")`. No tests depend on live external websites or network connectivity.
