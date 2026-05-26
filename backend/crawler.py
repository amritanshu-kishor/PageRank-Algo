from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


REQUEST_TIMEOUT = 8
USER_AGENT = "MiniPageRankCrawler/1.0"


def crawl_site(start_url, max_pages=12):
    """
    Crawl a small same-site graph starting at start_url.

    Returns:
        {
            "pages": [url, ...],
            "links": [[source_url, target_url], ...]
        }
    """
    start_url = normalize_url(start_url)
    if not start_url:
        raise ValueError("Enter a valid http or https URL.")

    max_pages = max(1, min(int(max_pages or 12), 30))
    root_host = urlparse(start_url).netloc.lower()
    queue = deque([start_url])
    queued = {start_url}
    visited = set()
    links = set()

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    while queue and len(visited) < max_pages:
        current_url = queue.popleft()
        queued.discard(current_url)
        if current_url in visited:
            continue

        visited.add(current_url)
        html = fetch_html(session, current_url)
        if not html:
            continue

        for href in extract_links(html, current_url):
            target_url = normalize_url(href)
            if not target_url:
                continue
            if urlparse(target_url).netloc.lower() != root_host:
                continue

            links.add((current_url, target_url))

            if target_url not in visited and target_url not in queued and len(visited) + len(queued) < max_pages:
                queue.append(target_url)
                queued.add(target_url)

    pages = sorted(visited)
    page_set = set(pages)
    filtered_links = sorted(
        [list(edge) for edge in links if edge[0] in page_set and edge[1] in page_set and edge[0] != edge[1]]
    )

    return {"pages": pages, "links": filtered_links}


def fetch_html(session, url):
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        content_type = response.headers.get("content-type", "")
        if response.status_code >= 400 or "text/html" not in content_type:
            return None
        return response.text
    except requests.RequestException:
        return None


def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        yield urljoin(base_url, anchor["href"])


def normalize_url(raw_url):
    raw_url = (raw_url or "").strip()
    if not raw_url:
        return None

    if not raw_url.startswith(("http://", "https://")):
        raw_url = f"https://{raw_url}"

    raw_url, _fragment = urldefrag(raw_url)
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            parsed.query,
            "",
        )
    )
