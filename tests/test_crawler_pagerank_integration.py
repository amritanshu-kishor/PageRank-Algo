"""
Phase 1 — Step 7: Crawler -> Graph Validator -> Graph Analysis -> PageRank Integration Tests.

Verifies end-to-end data pipeline correctness and invariants:
1. Invariant 1 (Node consistency): crawler.pages == validated_pages == analysis_nodes == pagerank_nodes
2. Invariant 2 (Edge consistency): validated_links == analysis_edges == pagerank_edges
3. Invariant 3 (Edge uniqueness): deduplicated edges passed to analysis & PageRank
4. Invariant 4 (Rank coverage): every node gets a PageRank score
5. Invariant 5 (Rank mass conservation): sum(ranks) ~= 1.0
6. Invariant 6 (Determinism): repeated runs produce identical pipeline output
7. Failures & Boundary Safety: invalid crawler output fails at validator boundary before analysis/PageRank

All tests use deterministic mocked HTTP responses (0 live network calls).
"""

from unittest.mock import MagicMock, patch
import pytest
import requests
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from crawler import crawl_site
from graph_validator import validate_graph
from graph_analyzer import analyze_graph
from pagerank import calculate_pagerank
from app import app


class TestPipelineHelper:
    """Helper methods for constructing mocked HTTP responses."""

    @staticmethod
    def make_mock_session(responses_dict):
        session = MagicMock()
        session.headers = {}

        def mock_get(url, timeout=None, allow_redirects=True):
            if url in responses_dict:
                item = responses_dict[url]
                if isinstance(item, Exception):
                    raise item
                status_code, content_type, text, final_url = item
                resp = MagicMock()
                resp.status_code = status_code
                resp.headers = {"content-type": content_type}
                resp.text = text
                resp.url = final_url or url
                return resp
            resp = MagicMock()
            resp.status_code = 404
            resp.headers = {"content-type": "text/html"}
            resp.text = "Not Found"
            resp.url = url
            return resp

        session.get = MagicMock(side_effect=mock_get)
        return session


class TestCrawlerPageRankIntegration(TestPipelineHelper):
    """End-to-end integration tests for the full Crawler -> Validator -> Analyzer -> PageRank pipeline."""

    @patch("requests.Session")
    def test_1_simple_chain_integration(self, mock_session_cls):
        # A -> B -> C
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (200, "text/html", '<a href="/b">B</a>', "https://example.com/a"),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", 'End', "https://example.com/c"),
        })

        # 1. Crawler
        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        raw_pages, raw_links = crawl_res["pages"], crawl_res["links"]

        # 2. Validator
        pages, links = validate_graph(raw_pages, raw_links)

        # 3. Analyzer
        analysis = analyze_graph(pages, links, validate=False)

        # 4. PageRank
        scores = calculate_pagerank(pages, links)

        # Invariant Verifications
        assert pages == ["https://example.com/a", "https://example.com/b", "https://example.com/c"]
        assert links == [
            ["https://example.com/a", "https://example.com/b"],
            ["https://example.com/b", "https://example.com/c"],
        ]
        assert analysis["node_count"] == 3
        assert analysis["edge_count"] == 2
        assert set(scores.keys()) == set(pages)
        assert pytest.approx(sum(scores.values()), abs=1e-5) == 1.0

    @patch("requests.Session")
    def test_2_directed_cycle_integration(self, mock_session_cls):
        # A -> B -> C -> A
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (200, "text/html", '<a href="/b">B</a>', "https://example.com/a"),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", '<a href="/a">A</a>', "https://example.com/c"),
        })

        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        assert analysis["dangling_node_count"] == 0
        assert len(analysis["weakly_connected_components"]) == 1
        assert len(analysis["strongly_connected_components"]) == 1
        assert set(scores.keys()) == set(pages)
        assert pytest.approx(sum(scores.values()), abs=1e-5) == 1.0
        # Symmetry: in 3-cycle, all ranks equal 1/3
        for node in pages:
            assert pytest.approx(scores[node], abs=1e-5) == 1.0 / 3.0

    @patch("requests.Session")
    def test_3_dangling_node_integration(self, mock_session_cls):
        # A -> B -> C (C has no outgoing links)
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (200, "text/html", '<a href="/b">B</a>', "https://example.com/a"),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", 'No links here', "https://example.com/c"),
        })

        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        assert analysis["out_degree"]["https://example.com/c"] == 0
        assert analysis["dangling_node_count"] == 1
        assert set(scores.keys()) == set(pages)
        assert pytest.approx(sum(scores.values()), abs=1e-5) == 1.0
        # Accumulation down the chain: PR(c) > PR(a)
        assert scores["https://example.com/c"] > scores["https://example.com/a"]

    @patch("requests.Session")
    def test_4_disconnected_graph_integration(self, mock_session_cls):
        # Component 1: A -> B
        # Component 2: C -> D
        # Isolated: E
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (
                200,
                "text/html",
                '<a href="/b">B</a> <a href="/c">C</a> <a href="/e">E</a>',
                "https://example.com/a"
            ),
            "https://example.com/b": (200, "text/html", "", "https://example.com/b"),
            "https://example.com/c": (200, "text/html", '<a href="/d">D</a>', "https://example.com/c"),
            "https://example.com/d": (200, "text/html", "", "https://example.com/d"),
            "https://example.com/e": (200, "text/html", "", "https://example.com/e"),
        })

        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        assert analysis["node_count"] == 5
        assert set(scores.keys()) == set(pages)
        assert pytest.approx(sum(scores.values()), abs=1e-5) == 1.0

    @patch("requests.Session")
    def test_5_duplicate_links_integration(self, mock_session_cls):
        # Page A has duplicate links to B
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (
                200,
                "text/html",
                '<a href="/b">B1</a> <a href="/b">B2</a> <a href="/b#fragment">B3</a>',
                "https://example.com/a"
            ),
            "https://example.com/b": (200, "text/html", "", "https://example.com/b"),
        })

        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        # Deduplication invariant
        assert links == [["https://example.com/a", "https://example.com/b"]]
        assert analysis["edge_count"] == 1
        assert pytest.approx(sum(scores.values()), abs=1e-5) == 1.0

    @patch("requests.Session")
    def test_6_self_loop_integration(self, mock_session_cls):
        # Page A links to itself
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (
                200,
                "text/html",
                '<a href="/a">Self Loop</a>',
                "https://example.com/a"
            ),
        })

        crawl_res = crawl_site("https://example.com/a", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        assert pages == ["https://example.com/a"]
        assert links == [["https://example.com/a", "https://example.com/a"]]
        assert analysis["in_degree"]["https://example.com/a"] == 1
        assert analysis["out_degree"]["https://example.com/a"] == 1
        assert scores == {"https://example.com/a": 1.0}

    @patch("requests.Session")
    def test_7_isolated_node_integration(self, mock_session_cls):
        # Single page crawl with no outgoing edges -> 1 node, isolated for out_degree
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/isolated": (200, "text/html", "No links", "https://example.com/isolated"),
        })

        crawl_res = crawl_site("https://example.com/isolated", max_pages=10)
        pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
        analysis = analyze_graph(pages, links, validate=False)
        scores = calculate_pagerank(pages, links)

        assert analysis["isolated_node_count"] == 1
        assert scores == {"https://example.com/isolated": 1.0}

    def test_8_invalid_graph_boundary_fails_before_pagerank(self):
        # Construct malformed graph output at boundary
        malformed_pages = ["A", None, "B"]
        malformed_links = [["A", "B"]]

        # Validator MUST raise ValueError
        with pytest.raises(ValueError, match="non-empty string"):
            validate_graph(malformed_pages, malformed_links)

        # Malformed edge length
        with pytest.raises(ValueError, match="exactly 2 elements"):
            validate_graph(["A", "B"], [["A", "B", "C"]])

    @patch("requests.Session")
    def test_9_deterministic_repeated_pipeline(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/a": (
                200,
                "text/html",
                '<a href="/b">B</a> <a href="/c">C</a>',
                "https://example.com/a"
            ),
            "https://example.com/b": (200, "text/html", '<a href="/c">C</a>', "https://example.com/b"),
            "https://example.com/c": (200, "text/html", '<a href="/a">A</a>', "https://example.com/c"),
        })

        def run_full_pipeline():
            crawl_res = crawl_site("https://example.com/a", max_pages=10)
            pages, links = validate_graph(crawl_res["pages"], crawl_res["links"])
            analysis = analyze_graph(pages, links, validate=False)
            scores = calculate_pagerank(pages, links)
            return pages, links, analysis, scores

        p1, l1, a1, s1 = run_full_pipeline()
        p2, l2, a2, s2 = run_full_pipeline()

        assert p1 == p2
        assert l1 == l2
        assert a1 == a2
        assert s1 == s2

    @patch("requests.Session")
    def test_10_api_post_crawl_full_pipeline(self, mock_session_cls):
        mock_session_cls.return_value = self.make_mock_session({
            "https://example.com/": (
                200,
                "text/html",
                '<a href="/about">About</a>',
                "https://example.com/"
            ),
            "https://example.com/about": (200, "text/html", "About Page", "https://example.com/about"),
        })

        app.config["TESTING"] = True
        with app.test_client() as client:
            resp = client.post(
                "/crawl",
                json={"url": "https://example.com", "max_pages": 5}
            )
            assert resp.status_code == 200
            data = resp.get_json()

            # Verify response schema compatibility
            assert "pages" in data
            assert "links" in data
            assert "scores" in data
            assert "analysis" in data
            assert "metadata" in data

            # Verify pipeline outputs inside API response
            assert len(data["pages"]) == 2
            assert len(data["links"]) == 1
            assert set(data["scores"].keys()) == set(data["pages"])
            assert pytest.approx(sum(data["scores"].values()), abs=1e-5) == 1.0
            assert data["analysis"]["node_count"] == 2
            assert data["analysis"]["edge_count"] == 1

    def test_11_api_post_crawl_validation_failure(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            # Invalid URL scheme / format
            resp = client.post("/crawl", json={"url": "ftp://invalid-scheme.com"})
            assert resp.status_code == 400
            data = resp.get_json()
            assert "error" in data
