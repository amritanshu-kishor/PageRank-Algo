import json
import os
import sys
import unittest
from unittest.mock import patch

# Ensure backend directory is in Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app import app


class TestAPIBaseline(unittest.TestCase):
    """
    Baseline test suite for Flask REST API endpoints (/calculate and /crawl) in backend/app.py.
    """

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_calculate_valid_graph(self):
        """Test POST /calculate with valid graph payload."""
        payload = {"pages": ["A", "B"], "links": [["A", "B"]]}
        response = self.client.post(
            "/calculate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("A", data)
        self.assertIn("B", data)
        self.assertAlmostEqual(data["A"], 0.3508771929824562, places=6)
        self.assertAlmostEqual(data["B"], 0.6491228070175439, places=6)
        self.assertGreater(data["B"], data["A"])

    def test_calculate_missing_pages(self):
        """Test POST /calculate with missing pages key."""
        payload = {"links": [["A", "B"]]}
        response = self.client.post(
            "/calculate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_calculate_missing_links(self):
        """Test POST /calculate with missing links key."""
        payload = {"pages": ["A", "B"]}
        response = self.client.post(
            "/calculate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_calculate_empty_payload(self):
        """Test POST /calculate with empty body."""
        response = self.client.post(
            "/calculate",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_calculate_empty_graph(self):
        """Test POST /calculate with empty pages and links arrays."""
        payload = {"pages": [], "links": []}
        response = self.client.post(
            "/calculate",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {})

    def test_crawl_missing_url(self):
        """Test POST /crawl with missing url key."""
        response = self.client.post(
            "/crawl",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_crawl_unresolvable_url_baseline(self):
        """Test POST /crawl with unresolvable URL (baseline behavior records HTTP 200 with single page)."""
        payload = {"url": "not-a-valid-url"}
        response = self.client.post(
            "/crawl",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("pages", data)
        self.assertIn("links", data)
        self.assertIn("scores", data)
        self.assertEqual(data["pages"], ["https://not-a-valid-url/"])
        self.assertEqual(data["links"], [])

    @patch("crawler.fetch_html")
    def test_crawl_mocked_success(self, mock_fetch):
        """Test POST /crawl with mocked HTML fetch response."""

        def mock_fetch_impl(session, url):
            if url == "https://example.com/":
                return '<a href="https://example.com/about">About</a>'
            elif url == "https://example.com/about":
                return '<a href="https://example.com/">Home</a>'
            return None

        mock_fetch.side_effect = mock_fetch_impl

        payload = {"url": "https://example.com", "max_pages": 5}
        response = self.client.post(
            "/crawl",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("pages", data)
        self.assertIn("links", data)
        self.assertIn("scores", data)
        self.assertIn("https://example.com/", data["pages"])
        self.assertIn("https://example.com/about", data["pages"])
        self.assertEqual(len(data["links"]), 2)


if __name__ == "__main__":
    unittest.main()
