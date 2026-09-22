"""
Phase 1 — Step 5: Graph Analysis Layer Unit & API Tests.

Tests the deterministic structural graph analysis layer:
1. Node & edge counts
2. Density calculation ($E / (N*(N-1))$ for $N>=2$, 0.0 for $N<2$)
3. In-degree and Out-degree mappings
4. Dangling node count vs Isolated node count
5. Weakly connected components (WCC)
6. Strongly connected components (SCC via Tarjan's algorithm)
7. Deterministic ordering of summary outputs and component lists
8. Step 4 graph validator integration
9. Flask API endpoint POST /analyze
"""

import pytest
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from graph_analyzer import analyze_graph
from app import app


class TestGraphAnalysisCore:
    """Unit tests for analyze_graph core function."""

    def test_case_1_empty_graph(self):
        summary = analyze_graph([], [])
        assert summary["node_count"] == 0
        assert summary["edge_count"] == 0
        assert summary["density"] == 0.0
        assert summary["in_degree"] == {}
        assert summary["out_degree"] == {}
        assert summary["dangling_node_count"] == 0
        assert summary["isolated_node_count"] == 0
        assert summary["weakly_connected_components"] == []
        assert summary["strongly_connected_components"] == []

    def test_case_2_single_node_no_edges(self):
        summary = analyze_graph(["A"], [])
        assert summary["node_count"] == 1
        assert summary["edge_count"] == 0
        assert summary["density"] == 0.0
        assert summary["in_degree"] == {"A": 0}
        assert summary["out_degree"] == {"A": 0}
        assert summary["dangling_node_count"] == 1
        assert summary["isolated_node_count"] == 1
        assert summary["weakly_connected_components"] == [["A"]]
        assert summary["strongly_connected_components"] == [["A"]]

    def test_case_3_simple_chain(self):
        summary = analyze_graph(["A", "B", "C"], [["A", "B"], ["B", "C"]])
        assert summary["node_count"] == 3
        assert summary["edge_count"] == 2
        # Density for N=3, E=2 is 2 / (3 * 2) = 2/6 = 1/3
        assert pytest.approx(summary["density"], abs=1e-6) == 1.0 / 3.0
        assert summary["in_degree"] == {"A": 0, "B": 1, "C": 1}
        assert summary["out_degree"] == {"A": 1, "B": 1, "C": 0}
        assert summary["dangling_node_count"] == 1  # C
        assert summary["isolated_node_count"] == 0
        assert summary["weakly_connected_components"] == [["A", "B", "C"]]
        assert summary["strongly_connected_components"] == [["A"], ["B"], ["C"]]

    def test_case_4_directed_cycle(self):
        summary = analyze_graph(
            ["A", "B", "C"], [["A", "B"], ["B", "C"], ["C", "A"]]
        )
        assert summary["node_count"] == 3
        assert summary["edge_count"] == 3
        # Density = 3 / 6 = 0.5
        assert pytest.approx(summary["density"], abs=1e-6) == 0.5
        assert summary["in_degree"] == {"A": 1, "B": 1, "C": 1}
        assert summary["out_degree"] == {"A": 1, "B": 1, "C": 1}
        assert summary["dangling_node_count"] == 0
        assert summary["isolated_node_count"] == 0
        assert summary["weakly_connected_components"] == [["A", "B", "C"]]
        assert summary["strongly_connected_components"] == [["A", "B", "C"]]

    def test_case_5_self_loop(self):
        summary = analyze_graph(["A"], [["A", "A"]])
        assert summary["node_count"] == 1
        assert summary["edge_count"] == 1
        # For N < 2, density is defined as 0.0
        assert summary["density"] == 0.0
        assert summary["in_degree"] == {"A": 1}
        assert summary["out_degree"] == {"A": 1}
        assert summary["dangling_node_count"] == 0
        assert summary["isolated_node_count"] == 0
        assert summary["weakly_connected_components"] == [["A"]]
        assert summary["strongly_connected_components"] == [["A"]]

    def test_case_6_disconnected_graph(self):
        # A -> B, C -> D, E (isolated)
        summary = analyze_graph(
            ["A", "B", "C", "D", "E"], [["A", "B"], ["C", "D"]]
        )
        assert summary["node_count"] == 5
        assert summary["edge_count"] == 2
        # Density = 2 / (5 * 4) = 2/20 = 0.1
        assert pytest.approx(summary["density"], abs=1e-6) == 0.1
        assert summary["in_degree"] == {"A": 0, "B": 1, "C": 0, "D": 1, "E": 0}
        assert summary["out_degree"] == {"A": 1, "B": 0, "C": 1, "D": 0, "E": 0}
        assert summary["dangling_node_count"] == 3  # B, D, E
        assert summary["isolated_node_count"] == 1  # E
        assert summary["weakly_connected_components"] == [
            ["A", "B"],
            ["C", "D"],
            ["E"],
        ]
        assert summary["strongly_connected_components"] == [
            ["A"],
            ["B"],
            ["C"],
            ["D"],
            ["E"],
        ]

    def test_case_7_isolated_vs_dangling(self):
        # A and B are isolated; C -> D (D is dangling, C is not isolated)
        summary = analyze_graph(["A", "B", "C", "D"], [["C", "D"]])
        assert summary["node_count"] == 4
        assert summary["edge_count"] == 1
        assert summary["isolated_node_count"] == 2  # A, B
        assert summary["dangling_node_count"] == 3  # A, B, D

    def test_case_8_duplicate_edges(self):
        summary = analyze_graph(["A", "B"], [["A", "B"], ["A", "B"]])
        assert summary["node_count"] == 2
        assert summary["edge_count"] == 1
        assert summary["density"] == 0.5

    def test_case_9_edges_to_unknown_nodes(self):
        summary = analyze_graph(["A", "B"], [["A", "B"], ["A", "Ghost"]])
        assert summary["node_count"] == 2
        assert summary["edge_count"] == 1
        assert summary["in_degree"] == {"A": 0, "B": 1}

    def test_case_10_validator_integration_raises_on_invalid_input(self):
        with pytest.raises(ValueError, match="non-empty string"):
            analyze_graph(["A", None], [])
        with pytest.raises(ValueError, match="exactly 2 elements"):
            analyze_graph(["A", "B"], [["A", "B", "C"]])

    def test_scc_multi_node_cycle_with_branches(self):
        # SCC 1: A <-> B
        # Edge: B -> C
        # Node C is dangling
        summary = analyze_graph(["A", "B", "C"], [["A", "B"], ["B", "A"], ["B", "C"]])
        assert summary["strongly_connected_components"] == [["A", "B"], ["C"]]
        assert summary["weakly_connected_components"] == [["A", "B", "C"]]

    def test_determinism_output_ordering(self):
        # Run multiple times with varying input order
        s1 = analyze_graph(["C", "A", "B"], [["B", "A"], ["A", "C"]])
        s2 = analyze_graph(["A", "B", "C"], [["A", "C"], ["B", "A"]])
        assert s1["weakly_connected_components"] == s2["weakly_connected_components"]
        assert s1["strongly_connected_components"] == s2["strongly_connected_components"]


class TestGraphAnalysisAPI:
    """Integration tests for POST /analyze Flask endpoint."""

    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_api_analyze_success(self, client):
        resp = client.post(
            "/analyze",
            json={"pages": ["A", "B", "C"], "links": [["A", "B"], ["B", "C"]]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["node_count"] == 3
        assert data["edge_count"] == 2
        assert data["dangling_node_count"] == 1
        assert data["isolated_node_count"] == 0
        assert len(data["weakly_connected_components"]) == 1

    def test_api_analyze_validation_failure(self, client):
        resp = client.post(
            "/analyze",
            json={"pages": ["A", 123], "links": []},
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data
        assert "non-empty string" in data["error"]
