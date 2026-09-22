"""
Phase 1 — Step 6: Hardened Web Crawler Unit & Contract Compatibility Tests.

Tests the crawler layer with deterministic mocked HTTP responses (no live network requests):
1. Single page crawl
2. Simple chain crawl (A -> B -> C)
3. Cycle crawl (A -> B -> C -> A)
4. Duplicate links deduplication
5. Relative URL resolution (/about, ../contact, ./team)
6. URL Fragment stripping (#section)
7. Off-domain link exclusion (https://google.com)
8. Malicious similar host exclusion (example.com.evil.com)
9. Non-HTML resource exclusion (Content-Type validation)
10. HTTP 404 error handling (graceful continuation)
11. HTTP 500 error handling (graceful continuation)
12. Request timeout handling (requests.Timeout)
13. On-domain redirect handling
14. Off-domain redirect rejection
15. Exact page limit (max_pages=1, max_pages=2, etc.)
16. Malformed href exclusion (javascript:, mailto:, tel:, data:)
17. Deterministic crawl output
18. Step 4 Graph Validator compatibility verification
"""

from unittest.mock import MagicMock, patch
import pytest
import requests
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from crawler import crawl_site, extract_links, is_same_host, normalize_url
from graph_validator import validate_graph


class TestURLNormalizationAndBoundary:
    """Unit tests for URL normalization and domain boundary rules."""

    def test_normalize_url_basic(self):
        assert normalize_url("https://example.com") == "https://example.com/"
        assert normalize_url("http://example.com/about/") == "http://example.com/about"
        assert normalize_url("   https://EXAMPLE.COM/page   ") == "https://example.com/page"

    def test_normalize_url_fragments(self):
        assert normalize_url("https://example.com/page#section1") == "https://example.com/page"
        assert normalize_url("https://example.com/page#two") == "https://example.com/page"

    def test_normalize_url_default_ports(self):
        assert normalize_url("http://example.com:80/page") == "http://example.com/page"
        assert normalize_url("https://example.com:443/page") == "https://example.com/page"
        assert normalize_url("http://example.com:8000/page") == "http://example.com:8000/page"

    def test_normalize_url_query_strings(self):
        assert normalize_url("https://example.com/search?q=test") == "https://example.com/search?q=test"

    def test_normalize_url_scheme_relative(self):
        assert normalize_url("//example.com/page") == "https://example.com/page"

    def test_normalize_url_invalid_schemes(self):
        assert normalize_url("javascript:void(0)") is None
        assert normalize_url("mailto:user@example.com") is None
        assert normalize_url("tel:1234567890") is None
        assert normalize_url("data:text/html,test") is None
        assert normalize_url("") is None
        assert normalize_url(None) is None

    def test_is_same_host_strict_matching(self):
        root = "example.com"
        assert is_same_host("https://example.com/page1", root) is True
        assert is_same_host("http://example.com/about", root) is True
        assert is_same_host("https://example.com:443/about", root) is True
        # Off-domain
        assert is_same_host("https://google.com/about", root) is False
        # Sub-domain when root is exact domain
        assert is_same_host("https://sub.example.com/page", root) is False
        # Malicious suffix
        assert is_same_host("https://example.com.evil.com/page", root) is False
        assert is_same_host("https://notexample.com/page", root) is False


class TestMockedCrawler:
    """Crawler functionality tests using mocked requests session."""

    def make_mock_session(self, responses_dict):
        """
        Helper to construct a mocked requests.Session.
        responses_dict maps URL -> (status_code, content_type, html_text, final_url) or Exception.
        """
        session = MagicMock()
        session.headers = {}

        def mock_get(url, timeout=None, allow_redirects=True):
            norm = normalize_url(url) or url
            target_key = None
            for key in (url, norm, url + "/", url.rstrip("/")):
                if key in responses_dict:
                    target_key = key
                    break

            if target_key is not None:
                item = responses_dict[target_key]
                if isinstance(item, Exception):
                    raise item
                status_code, content_type, text, final_url = item
                resp = MagicMock()
                resp.status_code = status_code
                resp.headers = {"content-type": content_type}
                resp.text = text
                resp.url = final_url or target_key
                return resp

            # Default 404 for unmocked URLs
            resp = MagicMock()
            resp.status_code = 404
            resp.headers = {"content-type": "text/html"}
            resp.text = "Not Found"
            resp.url = url
            return resp

        session.get = MagicMock(side_effect=mock_get)
        return session

    @patch("requests.Session")
    def test_1_single_page(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (200, "text/html", "<html><body>No links</body></html>", "https://example.com/")
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/"]
        assert result["links"] == []
        assert result["pages_crawled"] == 1
        assert result["pages_failed"] == 0

    @patch("requests.Session")
    def test_2_simple_chain(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (200, "text/html", '<a href="/b">B</a>', "https://example.com/"),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", 'End', "https://example.com/c"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/", "https://example.com/b", "https://example.com/c"]
        assert result["links"] == [
            ["https://example.com/", "https://example.com/b"],
            ["https://example.com/b", "https://example.com/c"],
        ]
        assert result["pages_crawled"] == 3

    @patch("requests.Session")
    def test_3_directed_cycle(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (200, "text/html", '<a href="/b">B</a>', "https://example.com/a"),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", '<a href="/a">A</a>', "https://example.com/c"),
        })
        result = crawl_site("https://example.com/a", max_pages=10)
        assert result["pages"] == ["https://example.com/a", "https://example.com/b", "https://example.com/c"]
        assert result["links"] == [
            ["https://example.com/a", "https://example.com/b"],
            ["https://example.com/b", "https://example.com/c"],
            ["https://example.com/c", "https://example.com/a"],
        ]

    @patch("requests.Session")
    def test_4_duplicate_links_deduplicated(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/b">B1</a> <a href="/b">B2</a> <a href="/b#sec">B3</a>',
                "https://example.com/"
            ),
            "https://example.com/b": (200, "text/html", "Target", "https://example.com/b"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/", "https://example.com/b"]
        assert result["links"] == [["https://example.com/", "https://example.com/b"]]

    @patch("requests.Session")
    def test_5_relative_urls_resolution(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/dir/": (
                200,
                "text/html",
                '<a href="/about">About</a> <a href="../contact">Contact</a> <a href="./team">Team</a>',
                "https://example.com/dir/"
            ),
            "https://example.com/about": (200, "text/html", "About", "https://example.com/about"),
            "https://example.com/contact": (200, "text/html", "Contact", "https://example.com/contact"),
            "https://example.com/dir/team": (200, "text/html", "Team", "https://example.com/dir/team"),
        })
        result = crawl_site("https://example.com/dir/", max_pages=10)
        assert "https://example.com/about" in result["pages"]
        assert "https://example.com/contact" in result["pages"]
        assert "https://example.com/dir/team" in result["pages"]

    @patch("requests.Session")
    def test_6_fragment_urls_handling(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/page": (
                200,
                "text/html",
                '<a href="/page#section1">S1</a> <a href="/page#section2">S2</a>',
                "https://example.com/page"
            ),
        })
        result = crawl_site("https://example.com/page", max_pages=10)
        assert result["pages"] == ["https://example.com/page"]

    @patch("requests.Session")
    def test_7_off_domain_link_excluded(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="https://google.com/about">Google</a>',
                "https://example.com/"
            ),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/"]
        assert result["links"] == []

    @patch("requests.Session")
    def test_8_malicious_hostname_excluded(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="https://example.com.evil.com/phish">Evil</a>',
                "https://example.com/"
            ),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/"]
        assert result["links"] == []

    @patch("requests.Session")
    def test_9_non_html_resource_excluded(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/img.png">Image</a> <a href="/doc.pdf">PDF</a> <a href="/zip.zip">ZIP</a>',
                "https://example.com/"
            ),
            "https://example.com/img.png": (200, "image/png", "binary_png_data", "https://example.com/img.png"),
            "https://example.com/doc.pdf": (200, "application/pdf", "%PDF-1.4", "https://example.com/doc.pdf"),
            "https://example.com/zip.zip": (200, "application/zip", "PK", "https://example.com/zip.zip"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        # Non-html links are attempted, but content-type check returns None -> failed set -> excluded from outgoing links
        assert result["pages"] == ["https://example.com/"]
        assert result["links"] == []

    @patch("requests.Session")
    def test_10_http_404_handled_gracefully(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/broken">404 Page</a> <a href="/good">Good Page</a>',
                "https://example.com/"
            ),
            "https://example.com/broken": (404, "text/html", "Not Found", "https://example.com/broken"),
            "https://example.com/good": (200, "text/html", "Good", "https://example.com/good"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert "https://example.com/good" in result["pages"]

    @patch("requests.Session")
    def test_11_http_500_handled_gracefully(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/error">500 Page</a> <a href="/ok">OK Page</a>',
                "https://example.com/"
            ),
            "https://example.com/error": (500, "text/html", "Server Error", "https://example.com/error"),
            "https://example.com/ok": (200, "text/html", "OK", "https://example.com/ok"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert "https://example.com/ok" in result["pages"]

    @patch("requests.Session")
    def test_12_request_timeout_handled(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/slow">Slow Page</a> <a href="/fast">Fast Page</a>',
                "https://example.com/"
            ),
            "https://example.com/slow": requests.Timeout("Connection timed out"),
            "https://example.com/fast": (200, "text/html", "Fast", "https://example.com/fast"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert "https://example.com/fast" in result["pages"]

    @patch("requests.Session")
    def test_13_on_domain_redirect_handled(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/old": (
                200,
                "text/html",
                "New Content",
                "https://example.com/new"
            ),
        })
        result = crawl_site("https://example.com/old", max_pages=10)
        assert "https://example.com/new" in result["pages"]

    @patch("requests.Session")
    def test_14_off_domain_redirect_rejected(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/external": (
                200,
                "text/html",
                "External Content",
                "https://google.com/home"  # Redirected off domain
            ),
        })
        result = crawl_site("https://example.com/external", max_pages=10)
        # Off-domain redirect target is rejected
        assert "https://google.com/home" not in result["pages"]

    @patch("requests.Session")
    def test_15_page_limit_enforced(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/p1">P1</a> <a href="/p2">P2</a> <a href="/p3">P3</a>',
                "https://example.com/"
            ),
            "https://example.com/p1": (200, "text/html", "P1", "https://example.com/p1"),
            "https://example.com/p2": (200, "text/html", "P2", "https://example.com/p2"),
            "https://example.com/p3": (200, "text/html", "P3", "https://example.com/p3"),
        })
        # max_pages = 1
        res1 = crawl_site("https://example.com", max_pages=1)
        assert len(res1["pages"]) == 1

        # max_pages = 2
        res2 = crawl_site("https://example.com", max_pages=2)
        assert len(res2["pages"]) == 2

    @patch("requests.Session")
    def test_16_malformed_href_ignored(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '''
                <a href="">Empty</a>
                <a href="javascript:void(0)">JS</a>
                <a href="mailto:test@example.com">Mail</a>
                <a href="tel:12345">Tel</a>
                <a href="data:text/plain;base64,123">Data</a>
                <a href="/valid">Valid</a>
                ''',
                "https://example.com/"
            ),
            "https://example.com/valid": (200, "text/html", "Valid", "https://example.com/valid"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        assert result["pages"] == ["https://example.com/", "https://example.com/valid"]
        assert result["links"] == [["https://example.com/", "https://example.com/valid"]]

    @patch("requests.Session")
    def test_17_deterministic_crawl_output(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/b">B</a> <a href="/a">A</a>',
                "https://example.com/"
            ),
            "https://example.com/a": (200, "text/html", "A", "https://example.com/a"),
            "https://example.com/b": (200, "text/html", "B", "https://example.com/b"),
        })
        res_run1 = crawl_site("https://example.com", max_pages=10)
        res_run2 = crawl_site("https://example.com", max_pages=10)
        assert res_run1 == res_run2

    @patch("requests.Session")
    def test_18_graph_validator_compatibility(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/p1">P1</a>',
                "https://example.com/"
            ),
            "https://example.com/p1": (200, "text/html", "P1", "https://example.com/p1"),
        })
        result = crawl_site("https://example.com", max_pages=10)
        # Pass crawler output directly into Step 4 graph validator
        valid_pages, valid_links = validate_graph(result["pages"], result["links"])
        assert valid_pages == result["pages"]
        assert valid_links == result["links"]
