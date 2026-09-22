"""
Phase 1 — Step 4: Graph Edge-Case Handling & Input Validation Tests.

Tests the graph input and processing boundary:
1. Input format validation (validate_graph)
2. Parameter validation (validate_pagerank_params)
3. Direct calculate_pagerank validation & topological edge cases
4. API endpoint /calculate error responses (HTTP 400 on malformed input)
"""

import math
import pytest
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from graph_validator import validate_graph, validate_pagerank_params, validate_node_id
from pagerank import calculate_pagerank
from app import app


# =====================================================================
# 1. Node Validation Unit Tests
# =====================================================================
class TestNodeValidation:
    """Tests for node identifier validation and pages structure."""

    def test_pages_must_be_list(self):
        with pytest.raises(ValueError, match="'pages' must be a list"):
            validate_graph("ABC", [["A", "B"]])

    def test_pages_cannot_be_none(self):
        with pytest.raises(ValueError, match="'pages' must be a list"):
            validate_graph(None, [])

    def test_pages_cannot_be_dict(self):
        with pytest.raises(ValueError, match="'pages' must be a list"):
            validate_graph({"A": 1}, [])

    def test_node_cannot_be_none(self):
        with pytest.raises(ValueError, match=r"must be a non-empty string"):
            validate_graph(["A", None, "B"], [])

    def test_node_cannot_be_integer(self):
        with pytest.raises(ValueError, match=r"must be a non-empty string"):
            validate_graph(["A", 123, "B"], [])

    def test_node_cannot_be_boolean(self):
        with pytest.raises(ValueError, match=r"must be a non-empty string"):
            validate_graph([True, "A"], [])

    def test_node_cannot_be_empty_string(self):
        with pytest.raises(ValueError, match=r"must be a non-empty string"):
            validate_graph(["A", ""], [])

    def test_node_cannot_be_whitespace_only(self):
        with pytest.raises(ValueError, match=r"must be a non-empty string"):
            validate_graph(["A", "   \t\n"], [])

    def test_valid_node_types_allowed(self):
        # Spaces, Unicode, URLs are all valid string node identifiers
        pages, links = validate_graph(
            ["Home Page", "https://example.com/about", "ページA", "α_node"],
            [["Home Page", "https://example.com/about"]]
        )
        assert len(pages) == 4
        assert len(links) == 1

    def test_validate_node_id_helper(self):
        assert validate_node_id("valid_node") is True
        assert validate_node_id("Node With Spaces") is True
        assert validate_node_id("") is False
        assert validate_node_id("   ") is False
        assert validate_node_id(None) is False
        assert validate_node_id(123) is False


# =====================================================================
# 2. Edge Validation Unit Tests
# =====================================================================
class TestEdgeValidation:
    """Tests for edge structure and endpoint validation."""

    def test_links_must_be_list(self):
        with pytest.raises(ValueError, match="'links' must be a list"):
            validate_graph(["A", "B"], "not_a_list")

    def test_links_cannot_be_none(self):
        with pytest.raises(ValueError, match="'links' must be a list"):
            validate_graph(["A", "B"], None)

    def test_edge_cannot_be_bare_string(self):
        # 'AB' has len 2 and slicing works in Python, but it's a string, not a pair
        with pytest.raises(ValueError, match=r"must be a \[source, target\] pair"):
            validate_graph(["A", "B"], ["AB"])

    def test_edge_cannot_have_fewer_than_2_elements(self):
        with pytest.raises(ValueError, match=r"must have exactly 2 elements"):
            validate_graph(["A", "B"], [["A"]])

    def test_edge_cannot_have_more_than_2_elements(self):
        with pytest.raises(ValueError, match=r"must have exactly 2 elements"):
            validate_graph(["A", "B", "C"], [["A", "B", "C"]])

    def test_edge_source_cannot_be_none(self):
        with pytest.raises(ValueError, match=r"\(source\) must be a non-empty string"):
            validate_graph(["A", "B"], [[None, "B"]])

    def test_edge_target_cannot_be_none(self):
        with pytest.raises(ValueError, match=r"\(target\) must be a non-empty string"):
            validate_graph(["A", "B"], [["A", None]])

    def test_edge_source_cannot_be_empty(self):
        with pytest.raises(ValueError, match=r"\(source\) must be a non-empty string"):
            validate_graph(["A", "B"], [["", "B"]])

    def test_edge_target_cannot_be_whitespace(self):
        with pytest.raises(ValueError, match=r"\(target\) must be a non-empty string"):
            validate_graph(["A", "B"], [["A", "  "]])

    def test_edge_source_cannot_be_int(self):
        with pytest.raises(ValueError, match=r"\(source\) must be a non-empty string"):
            validate_graph(["A", "B"], [[1, "B"]])

    def test_edge_target_cannot_be_int(self):
        with pytest.raises(ValueError, match=r"\(target\) must be a non-empty string"):
            validate_graph(["A", "B"], [["A", 2]])


# =====================================================================
# 3. Numeric Parameter Validation Tests
# =====================================================================
class TestParameterValidation:
    """Tests for damping, tol, and max_iterations validation."""

    def test_valid_params(self):
        params = validate_pagerank_params(damping=0.85, tol=1e-6, max_iterations=100)
        assert params['damping'] == 0.85
        assert params['tol'] == 1e-6
        assert params['max_iterations'] == 100

    def test_none_params_omitted(self):
        params = validate_pagerank_params(damping=None, tol=None, max_iterations=None)
        assert params == {}

    def test_invalid_damping_boundary(self):
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            validate_pagerank_params(damping=0.0)
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            validate_pagerank_params(damping=1.0)
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            validate_pagerank_params(damping=-0.5)
        with pytest.raises(ValueError, match="strictly between 0 and 1"):
            validate_pagerank_params(damping=1.5)

    def test_invalid_damping_non_finite(self):
        with pytest.raises(ValueError, match="finite number"):
            validate_pagerank_params(damping=float('nan'))
        with pytest.raises(ValueError, match="finite number"):
            validate_pagerank_params(damping=float('inf'))

    def test_invalid_tol(self):
        with pytest.raises(ValueError, match="positive"):
            validate_pagerank_params(tol=0.0)
        with pytest.raises(ValueError, match="positive"):
            validate_pagerank_params(tol=-1e-4)
        with pytest.raises(ValueError, match="finite number"):
            validate_pagerank_params(tol=float('nan'))

    def test_invalid_max_iterations(self):
        with pytest.raises(ValueError, match="at least 1"):
            validate_pagerank_params(max_iterations=0)
        with pytest.raises(ValueError, match="at least 1"):
            validate_pagerank_params(max_iterations=-5)
        with pytest.raises(ValueError, match="positive integer"):
            validate_pagerank_params(max_iterations=True)
        with pytest.raises(ValueError, match="positive integer"):
            validate_pagerank_params(max_iterations=10.5)

    def test_calculate_pagerank_direct_parameter_checks(self):
        # Ensure calculate_pagerank itself also enforces tol and max_iterations
        with pytest.raises(ValueError, match="tol must be a positive finite number"):
            calculate_pagerank(["A"], [], tol=-1.0)
        with pytest.raises(ValueError, match="max_iterations must be an integer >= 1"):
            calculate_pagerank(["A"], [], max_iterations=0)


# =====================================================================
# 4. Topological Graph Edge Cases
# =====================================================================
class TestTopologicalEdgeCases:
    """Tests for complex, extreme, and pathological graph structures."""

    def test_empty_graph(self):
        scores = calculate_pagerank([], [])
        assert scores == {}

    def test_single_node_no_edges(self):
        scores = calculate_pagerank(["A"], [])
        assert scores == {"A": 1.0}

    def test_single_node_self_loop(self):
        scores = calculate_pagerank(["A"], [["A", "A"]])
        assert scores == {"A": 1.0}

    def test_all_nodes_isolated(self):
        nodes = ["N1", "N2", "N3", "N4", "N5"]
        scores = calculate_pagerank(nodes, [])
        assert len(scores) == 5
        for n in nodes:
            assert pytest.approx(scores[n], abs=1e-5) == 0.2
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0

    def test_complete_graph(self):
        # In a complete directed graph with N nodes, all ranks should be equal 1/N
        nodes = ["A", "B", "C", "D"]
        links = [[u, v] for u in nodes for v in nodes if u != v]
        scores = calculate_pagerank(nodes, links)
        for n in nodes:
            assert pytest.approx(scores[n], abs=1e-5) == 0.25
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0

    def test_star_graph_inward(self):
        # All leaf nodes point to center C
        leaves = ["L1", "L2", "L3", "L4"]
        nodes = ["C"] + leaves
        links = [[leaf, "C"] for leaf in leaves]
        scores = calculate_pagerank(nodes, links)
        # Center C should have strictly higher rank than leaves
        for leaf in leaves:
            assert scores["C"] > scores[leaf]
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0

    def test_star_graph_outward(self):
        # Center C points to all leaves, leaves are dangling
        leaves = ["L1", "L2", "L3", "L4"]
        nodes = ["C"] + leaves
        links = [["C", leaf] for leaf in leaves]
        scores = calculate_pagerank(nodes, links)
        # Symmetry among leaves
        for leaf in leaves:
            assert pytest.approx(scores[leaf], abs=1e-6) == scores[leaves[0]]
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0

    def test_linear_dangling_chain(self):
        # A -> B -> C -> D (D is dangling)
        nodes = ["A", "B", "C", "D"]
        links = [["A", "B"], ["B", "C"], ["C", "D"]]
        scores = calculate_pagerank(nodes, links)
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0
        # Rank should accumulate down the chain
        assert scores["D"] > scores["A"]

    def test_disconnected_subgraphs(self):
        # Component 1: A <-> B
        # Component 2: C <-> D
        # Both are symmetric 2-cycles
        nodes = ["A", "B", "C", "D"]
        links = [["A", "B"], ["B", "A"], ["C", "D"], ["D", "C"]]
        scores = calculate_pagerank(nodes, links)
        assert pytest.approx(scores["A"], abs=1e-6) == 0.25
        assert pytest.approx(scores["B"], abs=1e-6) == 0.25
        assert pytest.approx(scores["C"], abs=1e-6) == 0.25
        assert pytest.approx(scores["D"], abs=1e-6) == 0.25
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0

    def test_duplicate_nodes_in_pages_input(self):
        # Duplicate nodes in pages list should be deduplicated
        pages = ["A", "B", "A", "C", "B"]
        links = [["A", "B"], ["B", "C"], ["C", "A"]]
        scores = calculate_pagerank(pages, links)
        assert list(scores.keys()) == ["A", "B", "C"]
        assert pytest.approx(scores["A"], abs=1e-6) == 1.0 / 3.0

    def test_edges_to_unknown_nodes_safely_ignored(self):
        pages = ["A", "B"]
        links = [["A", "B"], ["A", "Ghost"], ["Ghost", "B"], ["X", "Y"]]
        scores = calculate_pagerank(pages, links)
        assert set(scores.keys()) == {"A", "B"}
        assert pytest.approx(sum(scores.values()), abs=1e-6) == 1.0


# =====================================================================
# 5. Flask API Integration & HTTP 400 Error Handling Tests
# =====================================================================
class TestAPIEdgeCases:
    """Tests that Flask API returns HTTP 400 on malformed input."""

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_api_rejects_null_node_in_pages(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', None, 'B'],
            'links': [['A', 'B']]
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'non-empty string' in data['error']

    def test_api_rejects_empty_string_node_in_pages(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', '', 'B'],
            'links': [['A', 'B']]
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_api_rejects_malformed_edge_length(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B'],
            'links': [['A']]  # only 1 element
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'exactly 2 elements' in data['error']

    def test_api_rejects_edge_with_more_than_2_elements(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B', 'C'],
            'links': [['A', 'B', 'C']]  # 3 elements
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'exactly 2 elements' in data['error']

    def test_api_rejects_edge_as_bare_string(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B'],
            'links': ['AB']
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_api_rejects_invalid_damping(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B'],
            'links': [['A', 'B']],
            'damping': 1.5
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'damping' in data['error']

    def test_api_rejects_invalid_tol(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B'],
            'links': [['A', 'B']],
            'tol': -0.01
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'tol' in data['error']

    def test_api_rejects_invalid_max_iterations(self, client):
        resp = client.post('/calculate', json={
            'pages': ['A', 'B'],
            'links': [['A', 'B']],
            'max_iterations': 0
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data
        assert 'max_iterations' in data['error']

    def test_api_accepts_valid_edge_cases(self, client):
        # Single isolated node
        resp = client.post('/calculate', json={
            'pages': ['Single'],
            'links': []
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == {'Single': 1.0}

        # Self loop
        resp = client.post('/calculate', json={
            'pages': ['Single'],
            'links': [['Single', 'Single']]
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == {'Single': 1.0}
