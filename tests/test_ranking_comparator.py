"""
Unit and integration tests for Ranking Comparison Layer (backend/ranking_comparator.py).

Verifies:
1. Vector validation & common-node alignment
2. Distance metrics (L1, L2)
3. Cosine similarity & zero-vector safety
4. Spearman rank correlation & tie handling
5. Kendall tau-b correlation & tie handling
6. Top-K overlap & deterministic tie-breaking
7. Rank displacement statistics
8. API integration via POST /compare
"""

import math
import pytest
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ranking_comparator import (
    validate_ranking_vector,
    align_rankings,
    calculate_l1_distance,
    calculate_l2_distance,
    calculate_cosine_similarity,
    calculate_spearman_correlation,
    calculate_kendall_tau,
    calculate_top_k_overlap,
    calculate_rank_displacements,
    compare_rankings,
)
from app import app


# -------------------------------------------------------------------
# 1. Ranking Vector Validation Tests
# -------------------------------------------------------------------

def test_validate_ranking_vector_valid():
    ranking = {"A": 0.5, "B": 0.3, "C": 0.2}
    val = validate_ranking_vector(ranking)
    assert val == {"A": 0.5, "B": 0.3, "C": 0.2}
    assert isinstance(val["A"], float)


def test_validate_ranking_vector_invalid_type():
    with pytest.raises(ValueError, match="must be a dictionary"):
        validate_ranking_vector([("A", 0.5)])


def test_validate_ranking_vector_invalid_node_id():
    with pytest.raises(ValueError, match="invalid node identifier"):
        validate_ranking_vector({"": 0.5})

    with pytest.raises(ValueError, match="invalid node identifier"):
        validate_ranking_vector({123: 0.5})


def test_validate_ranking_vector_non_numeric_score():
    with pytest.raises(ValueError, match="score must be a number"):
        validate_ranking_vector({"A": "0.5"})

    with pytest.raises(ValueError, match="score must be a number"):
        validate_ranking_vector({"A": None})

    with pytest.raises(ValueError, match="score must be a number"):
        validate_ranking_vector({"A": True})


def test_validate_ranking_vector_nan_inf_score():
    with pytest.raises(ValueError, match="must be a finite number"):
        validate_ranking_vector({"A": float("nan")})

    with pytest.raises(ValueError, match="must be a finite number"):
        validate_ranking_vector({"A": float("inf")})


# -------------------------------------------------------------------
# 2. Common-Node Alignment Tests
# -------------------------------------------------------------------

def test_align_rankings_success():
    r_a = {"B": 0.3, "A": 0.5, "C": 0.2}
    r_b = {"A": 0.4, "C": 0.1, "B": 0.5}

    nodes, vec_a, vec_b = align_rankings(r_a, r_b)
    assert nodes == ["A", "B", "C"]
    assert vec_a == [0.5, 0.3, 0.2]
    assert vec_b == [0.4, 0.5, 0.1]


def test_align_rankings_mismatched_node_sets():
    r_a = {"A": 0.5, "B": 0.3, "C": 0.2}
    r_b = {"A": 0.5, "B": 0.3, "D": 0.2}

    with pytest.raises(ValueError, match="Rankings must refer to the exact same node set"):
        align_rankings(r_a, r_b)


# -------------------------------------------------------------------
# 3. L1 and L2 Distance Tests
# -------------------------------------------------------------------

def test_l1_l2_distance_identity():
    vec_a = [0.4, 0.3, 0.3]
    vec_b = [0.4, 0.3, 0.3]
    assert calculate_l1_distance(vec_a, vec_b) == 0.0
    assert calculate_l2_distance(vec_a, vec_b) == 0.0


def test_l1_l2_distance_known_values():
    vec_a = [1.0, 2.0, 3.0]
    vec_b = [4.0, 0.0, 3.0]
    # L1: |1-4| + |2-0| + |3-3| = 3 + 2 + 0 = 5.0
    assert calculate_l1_distance(vec_a, vec_b) == 5.0
    # L2: sqrt((1-4)^2 + (2-0)^2 + (3-3)^2) = sqrt(9 + 4 + 0) = sqrt(13)
    assert pytest.approx(calculate_l2_distance(vec_a, vec_b)) == math.sqrt(13)


# -------------------------------------------------------------------
# 4. Cosine Similarity Tests
# -------------------------------------------------------------------

def test_cosine_similarity():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    assert pytest.approx(calculate_cosine_similarity(vec_a, vec_b)) == 1.0

    vec_c = [0.0, 1.0, 0.0]
    assert pytest.approx(calculate_cosine_similarity(vec_a, vec_c)) == 0.0


def test_cosine_similarity_zero_vectors():
    zero_vec = [0.0, 0.0, 0.0]
    non_zero = [0.5, 0.3, 0.2]

    # Both zero -> 1.0
    assert calculate_cosine_similarity(zero_vec, zero_vec) == 1.0
    # One zero -> 0.0
    assert calculate_cosine_similarity(zero_vec, non_zero) == 0.0
    assert calculate_cosine_similarity(non_zero, zero_vec) == 0.0


# -------------------------------------------------------------------
# 5. Spearman Rank Correlation Tests
# -------------------------------------------------------------------

def test_spearman_correlation_identical():
    vec_a = [0.1, 0.4, 0.3, 0.2]
    vec_b = [0.1, 0.4, 0.3, 0.2]
    assert pytest.approx(calculate_spearman_correlation(vec_a, vec_b)) == 1.0


def test_spearman_correlation_inverse():
    vec_a = [1.0, 2.0, 3.0, 4.0]
    vec_b = [4.0, 3.0, 2.0, 1.0]
    assert pytest.approx(calculate_spearman_correlation(vec_a, vec_b)) == -1.0


def test_spearman_correlation_ties():
    # Tie at values 2.0 in vec_a -> ranks [1, 2.5, 2.5, 4]
    vec_a = [1.0, 2.0, 2.0, 4.0]
    vec_b = [1.0, 2.0, 3.0, 4.0]
    res = calculate_spearman_correlation(vec_a, vec_b)
    assert 0.8 < res <= 1.0


# -------------------------------------------------------------------
# 6. Kendall Tau Tests
# -------------------------------------------------------------------

def test_kendall_tau_identical():
    vec_a = [0.1, 0.4, 0.3, 0.2]
    vec_b = [0.1, 0.4, 0.3, 0.2]
    assert pytest.approx(calculate_kendall_tau(vec_a, vec_b)) == 1.0


def test_kendall_tau_inverse():
    vec_a = [1.0, 2.0, 3.0, 4.0]
    vec_b = [4.0, 3.0, 2.0, 1.0]
    assert pytest.approx(calculate_kendall_tau(vec_a, vec_b)) == -1.0


def test_kendall_tau_with_ties():
    vec_a = [1.0, 2.0, 2.0, 4.0]
    vec_b = [1.0, 2.0, 3.0, 4.0]
    res = calculate_kendall_tau(vec_a, vec_b)
    assert 0.8 < res <= 1.0


# -------------------------------------------------------------------
# 7. Top-K Overlap Tests
# -------------------------------------------------------------------

def test_top_k_overlap_perfect():
    nodes = ["A", "B", "C", "D"]
    vec_a = [0.4, 0.3, 0.2, 0.1]
    vec_b = [0.4, 0.3, 0.2, 0.1]

    res = calculate_top_k_overlap(nodes, vec_a, vec_b, k_values=[1, 2, 4])
    assert res[1] == 1.0
    assert res[2] == 1.0
    assert res[4] == 1.0


def test_top_k_overlap_partial():
    nodes = ["A", "B", "C", "D"]
    vec_a = [0.4, 0.3, 0.2, 0.1] # Top 2: A, B
    vec_b = [0.1, 0.3, 0.4, 0.2] # Top 2: C, B

    res = calculate_top_k_overlap(nodes, vec_a, vec_b, k_values=[2])
    # Intersection is {'B'}, so 1/2 = 0.5
    assert res[2] == 0.5


def test_top_k_overlap_deterministic_tie_breaking():
    # Both nodes A and B have score 0.5 in vec_a.
    # Deterministic sorting (score desc, node ID asc) puts 'A' before 'B'.
    nodes = ["A", "B", "C"]
    vec_a = [0.5, 0.5, 0.1]
    vec_b = [0.5, 0.1, 0.4] # Top 1 in vec_b is A

    res = calculate_top_k_overlap(nodes, vec_a, vec_b, k_values=[1])
    assert res[1] == 1.0 # Top 1 for both is A


# -------------------------------------------------------------------
# 8. Rank Displacement Tests
# -------------------------------------------------------------------

def test_rank_displacements():
    nodes = ["A", "B", "C"]
    vec_a = [0.5, 0.3, 0.2] # Ranks: A=1, B=2, C=3
    vec_b = [0.2, 0.5, 0.3] # Ranks: B=1, C=2, A=3

    max_d, mean_d, dict_d = calculate_rank_displacements(nodes, vec_a, vec_b)
    # A: |1 - 3| = 2
    # B: |2 - 1| = 1
    # C: |3 - 2| = 1
    assert dict_d == {"A": 2, "B": 1, "C": 1}
    assert max_d == 2
    assert pytest.approx(mean_d) == 4.0 / 3.0


# -------------------------------------------------------------------
# 9. Consolidated Compare Rankings Function
# -------------------------------------------------------------------

def test_compare_rankings_consolidated():
    r_a = {"A": 0.4, "B": 0.3, "C": 0.2, "D": 0.1}
    r_b = {"A": 0.35, "B": 0.35, "C": 0.2, "D": 0.1}

    res = compare_rankings(r_a, r_b, top_k=[2, 4])
    assert res["node_count"] == 4
    assert "l1_distance" in res
    assert "l2_distance" in res
    assert "cosine_similarity" in res
    assert "spearman_correlation" in res
    assert "kendall_tau" in res
    assert res["top_k_overlap"] == {2: 1.0, 4: 1.0}
    assert res["max_rank_displacement"] >= 0
    assert res["mean_rank_displacement"] >= 0.0


# -------------------------------------------------------------------
# 10. API Integration Tests (POST /compare)
# -------------------------------------------------------------------

def test_api_compare_success():
    client = app.test_client()
    payload = {
        "ranking_a": {"A": 0.4, "B": 0.3, "C": 0.3},
        "ranking_b": {"A": 0.5, "B": 0.3, "C": 0.2},
        "top_k": [1, 2]
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["node_count"] == 3
    assert "l1_distance" in data
    assert "cosine_similarity" in data
    assert data["top_k_overlap"] == {"1": 1.0, "2": 1.0}


def test_api_compare_validation_error():
    client = app.test_client()
    # Mismatched node sets
    payload = {
        "ranking_a": {"A": 0.4, "B": 0.6},
        "ranking_b": {"A": 0.5, "C": 0.5}
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "exact same node set" in data["error"]


# ===================================================================
# STEP 8 VALIDATION REGRESSION TESTS
# ===================================================================

# -------------------------------------------------------------------
# Issue 1: Empty Ranking Vector Rejection
# -------------------------------------------------------------------

def test_validate_ranking_vector_empty_both():
    """Empty ranking_a must be rejected."""
    with pytest.raises(ValueError, match="must not be empty"):
        validate_ranking_vector({})


def test_validate_ranking_vector_empty_ranking_a():
    """Empty ranking_a must be rejected even when ranking_b is non-empty."""
    with pytest.raises(ValueError, match="must not be empty"):
        align_rankings({}, {"A": 1.0})


def test_validate_ranking_vector_empty_ranking_b():
    """Empty ranking_b must be rejected even when ranking_a is non-empty."""
    with pytest.raises(ValueError, match="must not be empty"):
        align_rankings({"A": 1.0}, {})


def test_compare_rankings_empty_ranking_a_raises():
    """compare_rankings must raise ValueError if ranking_a is empty."""
    with pytest.raises(ValueError, match="must not be empty"):
        compare_rankings({}, {"A": 1.0})


def test_compare_rankings_empty_ranking_b_raises():
    """compare_rankings must raise ValueError if ranking_b is empty."""
    with pytest.raises(ValueError, match="must not be empty"):
        compare_rankings({"A": 1.0}, {})


def test_compare_rankings_both_empty_raises():
    """compare_rankings must raise ValueError if both rankings are empty."""
    with pytest.raises(ValueError, match="must not be empty"):
        compare_rankings({}, {})


# -------------------------------------------------------------------
# Issue 2 & 3: Invalid top-k values must be explicitly rejected
# -------------------------------------------------------------------

def test_top_k_zero_rejected():
    """k=0 must raise ValueError."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must be >= 1"):
        compare_rankings(r, r, top_k=[0])


def test_top_k_negative_rejected():
    """k=-1 must raise ValueError."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must be >= 1"):
        compare_rankings(r, r, top_k=[-1])


def test_top_k_exceeds_n_rejected():
    """k > N must raise ValueError."""
    r = {"A": 0.5, "B": 0.3}  # N=2
    with pytest.raises(ValueError, match="exceeds the number of nodes"):
        compare_rankings(r, r, top_k=[3])


def test_top_k_string_rejected():
    """A string element in top_k must raise ValueError."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must be a plain integer"):
        compare_rankings(r, r, top_k=["3"])


def test_top_k_float_rejected():
    """A float element (e.g. 1.5) in top_k must raise ValueError."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must be a plain integer"):
        compare_rankings(r, r, top_k=[1.5])


def test_top_k_bool_rejected():
    """Boolean True in top_k must raise ValueError (bool is a subclass of int)."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must be a plain integer"):
        compare_rankings(r, r, top_k=[True])


# -------------------------------------------------------------------
# Issue 3: Empty top_k list must be rejected
# -------------------------------------------------------------------

def test_top_k_empty_list_rejected():
    """top_k=[] must raise ValueError (no k values requested is meaningless)."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="must not be an empty list"):
        compare_rankings(r, r, top_k=[])


# -------------------------------------------------------------------
# Issue 4: Duplicate top-k values must be rejected
# -------------------------------------------------------------------

def test_top_k_duplicate_rejected():
    """top_k=[1, 1, 3] must raise ValueError due to duplicate k=1."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="duplicate value"):
        compare_rankings(r, r, top_k=[1, 1, 3])


def test_top_k_duplicate_at_end_rejected():
    """top_k=[1, 2, 2] must raise ValueError due to duplicate k=2."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    with pytest.raises(ValueError, match="duplicate value"):
        compare_rankings(r, r, top_k=[1, 2, 2])


# -------------------------------------------------------------------
# Valid boundary values: k=1 and k=N must succeed
# -------------------------------------------------------------------

def test_top_k_boundary_k_equals_1():
    """k=1 (minimum valid value) must succeed."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}
    result = compare_rankings(r, r, top_k=[1])
    assert 1 in result["top_k_overlap"]
    assert result["top_k_overlap"][1] == 1.0


def test_top_k_boundary_k_equals_n():
    """k=N (maximum valid value) must succeed."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}  # N=3
    result = compare_rankings(r, r, top_k=[3])
    assert 3 in result["top_k_overlap"]
    assert result["top_k_overlap"][3] == 1.0


def test_top_k_k1_and_kN_together():
    """k=1 and k=N together must succeed."""
    r = {"A": 0.5, "B": 0.3, "C": 0.2}  # N=3
    result = compare_rankings(r, r, top_k=[1, 3])
    assert result["top_k_overlap"][1] == 1.0
    assert result["top_k_overlap"][3] == 1.0


# -------------------------------------------------------------------
# API regression: invalid top_k values return HTTP 400
# -------------------------------------------------------------------

def test_api_compare_top_k_zero_returns_400():
    """API must return 400 for k=0."""
    client = app.test_client()
    payload = {
        "ranking_a": {"A": 0.5, "B": 0.3, "C": 0.2},
        "ranking_b": {"A": 0.4, "B": 0.4, "C": 0.2},
        "top_k": [0],
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_compare_top_k_exceeds_n_returns_400():
    """API must return 400 when k > N."""
    client = app.test_client()
    payload = {
        "ranking_a": {"A": 0.5, "B": 0.5},
        "ranking_b": {"A": 0.4, "B": 0.6},
        "top_k": [5],  # N=2, k=5 is invalid
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_compare_empty_top_k_returns_400():
    """API must return 400 for top_k=[]."""
    client = app.test_client()
    payload = {
        "ranking_a": {"A": 0.5, "B": 0.5},
        "ranking_b": {"A": 0.4, "B": 0.6},
        "top_k": [],
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_compare_duplicate_top_k_returns_400():
    """API must return 400 for duplicate k values."""
    client = app.test_client()
    payload = {
        "ranking_a": {"A": 0.5, "B": 0.3, "C": 0.2},
        "ranking_b": {"A": 0.4, "B": 0.4, "C": 0.2},
        "top_k": [1, 1, 2],
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_api_compare_empty_ranking_returns_400():
    """API must return 400 when ranking_a is empty."""
    client = app.test_client()
    payload = {
        "ranking_a": {},
        "ranking_b": {"A": 1.0},
    }
    response = client.post("/compare", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()

