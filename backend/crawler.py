"""
Hardened, Deterministic Web Crawler for PageRank Graph Construction.

Establishes a reliable, reproducible web crawling layer bounded by same-host domain restrictions.

Flow:
    start_url -> normalize_url() -> crawl_site() -> {pages, links, metadata} -> graph_validator -> PageRank / Analysis
"""

from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


REQUEST_TIMEOUT = 8
USER_AGENT = "MiniPageRankCrawler/1.0"


def normalize_url(raw_url):
    """
    Canonicalize and normalize a URL string.

    Rules:
    1. Strip leading/trailing whitespace.
    2. Handle scheme-relative URLs (//example.com/path -> https://example.com/path).
    3. Default missing scheme to 'https://'.
    4. Reject non-HTTP(S) schemes (mailto:, javascript:, tel:, data:, file:, ftp:).
    5. Strip URL fragments (#section).
    6. Lowercase scheme and netloc (hostname).
    7. Strip default ports (:80 for http, :443 for https).
    8. Normalize path: for non-root paths ending with '/', strip trailing slash.
    9. Preserve query string.

    :param raw_url: Raw URL string.
    :return: Canonical URL string or None if invalid.
    """
    if not isinstance(raw_url, str):
        return None
    raw_url = raw_url.strip()
    if not raw_url:
        return None

    # Handle scheme-relative URLs (//example.com/path)
    if raw_url.startswith("//"):
        raw_url = f"https:{raw_url}"
    elif not raw_url.startswith(("http://", "https://")):
        # Reject explicit non-http schemes (javascript:void(0), mailto:user@domain, etc.)
        if ":" in raw_url.split("/")[0] and not raw_url.startswith(("http:", "https:")):
            return None
        raw_url = f"https://{raw_url}"

    # Strip URL fragment
    raw_url, _fragment = urldefrag(raw_url)

    try:
        parsed = urlparse(raw_url)
    except Exception:
        return None

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        return None

    netloc = parsed.netloc.lower()
    if not netloc:
        return None

    # Strip default port from netloc
    if ":" in netloc:
        host, _, port = netloc.partition(":")
        if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
            netloc = host

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))


def get_effective_host(url):
    """
    Extract normalized host (netloc without default port) from a URL.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if ":" in netloc:
        host, _, port = netloc.partition(":")
        if (parsed.scheme == "http" and port == "80") or (parsed.scheme == "https" and port == "443"):
            return host
    return netloc


def is_same_host(target_url, root_host):
    """
    Return True if target_url belongs to the exact same host as root_host.
    Prevents off-domain crawling and sub-domain expansion.
    """
    if not target_url or not root_host:
        return False
    return get_effective_host(target_url) == root_host


def fetch_html(session, url):
    """
    Fetch HTTP response for a URL using requests session.

    Handles:
    - Timeout (REQUEST_TIMEOUT)
    - HTTP status validation (< 400)
    - Content-Type validation (must contain text/html or application/xhtml+xml)
    - Redirect boundary validation

    :param session: requests.Session instance
    :param url: URL string to fetch
    :return: requests.Response object (or string if mocked), or None on failure/non-HTML
    """
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if response.status_code >= 400:
            return None

        content_type = response.headers.get("content-type", "").lower()
        if not ("text/html" in content_type or "application/xhtml+xml" in content_type):
            return None

        # Check for off-domain redirect target
        final_url = normalize_url(response.url)
        if not final_url or not is_same_host(final_url, get_effective_host(url)):
            return None

        return response
    except requests.RequestException:
        return None


def extract_links(html, base_url):
    """
    Extract valid navigation links from HTML anchor tags.

    Ignores non-http schemes (javascript:, mailto:, tel:, data:), empty hrefs.
    Resolves relative URLs against base_url.
    Returns list of raw resolved URLs in DOM order.

    :param html: HTML string
    :param base_url: Source page URL for resolving relative links
    :return: List of resolved URL strings
    """
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href:
            continue
        lower_href = href.lower()
        if lower_href.startswith(("javascript:", "mailto:", "tel:", "data:", "ftp:", "file:")):
            continue

        resolved = urljoin(base_url, href)
        links.append(resolved)
    return links


def crawl_site(start_url, max_pages=12):
    """
    Crawl a same-host graph starting at start_url up to max_pages.

    :param start_url: Starting seed URL string.
    :param max_pages: Maximum number of pages to process (int >= 1).
    :return: dict with keys:
        - "pages": list[str] of sorted normalized page URLs
        - "links": list[list[str]] of sorted directed edges [[source, target], ...]
        - "pages_crawled": int (successful page fetches)
        - "pages_failed": int (failed page fetches)
        - "start_url": str (normalized start URL)
        - "max_pages": int (effective page limit)
    :raises ValueError: If start_url is invalid.
    """
    norm_start = normalize_url(start_url)
    if not norm_start:
        raise ValueError("Enter a valid http or https URL.")

    try:
        max_pages = max(1, int(max_pages if max_pages is not None else 12))
    except (ValueError, TypeError):
        max_pages = 12

    root_host = get_effective_host(norm_start)

    queue = deque([norm_start])
    queued = {norm_start}
    visited = set()
    failed = set()
    links = set()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        queued.discard(current_url)

        if current_url in visited or current_url in failed:
            continue

        res = fetch_html(session, current_url)
        if res is None:
            failed.add(current_url)
            continue

        if isinstance(res, str):
            html = res
            raw_url = current_url
            actual_url = current_url
        else:
            html = getattr(res, "text", "")
            raw_url = getattr(res, "url", current_url)
            actual_url = normalize_url(raw_url) or current_url

        visited.add(actual_url)

        raw_links = extract_links(html, raw_url)
        seen_on_page = set()
        for href in raw_links:
            target_url = normalize_url(href)
            if not target_url:
                continue
            if not is_same_host(target_url, root_host):
                continue

            links.add((actual_url, target_url))

            if target_url not in visited and target_url not in queued and (len(visited) + len(queued)) < max_pages:
                if target_url not in seen_on_page:
                    seen_on_page.add(target_url)
                    queue.append(target_url)
                    queued.add(target_url)

    # Fallback if start_url failed and no pages were successfully fetched
    if not visited:
        visited.add(norm_start)

    pages = sorted(visited)
    page_set = set(pages)
    filtered_links = sorted(
        [list(edge) for edge in links if edge[0] in page_set and edge[1] in page_set]
    )

    return {
        "pages": pages,
        "links": filtered_links,
        "pages_crawled": len(visited - failed),
        "pages_failed": len(failed),
        "start_url": norm_start,
        "max_pages": max_pages,
    }
