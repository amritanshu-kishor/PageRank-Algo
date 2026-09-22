"""
Unit and integration tests for Step 9 — Experiment & Measurement Layer.

Verifies:
- Datasets catalog and deterministic scalable generators (chain, cycle, star)
- Dataset validation against Step 4 graph contract
- Single experiment execution, structural analysis inclusion, runtime measurement
- Detailed PageRank instrumentation (iterations, convergence status, final L1 error)
- Separation of deterministic experiment content from execution metadata (timestamp)
- Repeated experiment execution with rank stability verification across runs using Step 8 comparator
- Damping, tolerance, max_iterations, and scalability parameter sweeps
- Machine-readable result export to JSON files
- Configuration validation and error handling for invalid parameters/graphs
"""

import json
import math
import os
import tempfile
import sys
from pathlib import Path

import pytest

# Ensure backend and experiments modules are importable
_root = Path(__file__).resolve().parent.parent
if str(_root / "backend") not in sys.path:
    sys.path.insert(0, str(_root / "backend"))
if str(_root / "experiments") not in sys.path:
    sys.path.insert(0, str(_root / "experiments"))

from datasets import (
    ALL_DATASETS,
    DATASET_A,
    DATASET_B,
    DATASET_C,
    DATASET_D,
    DATASET_E,
    DATASET_F,
    DATASET_G,
    generate_chain,
    generate_cycle,
    generate_star,
    load_dataset,
)
from runner import (
    run_experiment,
    run_repeated_experiment,
    run_damping_sweep,
    run_tolerance_sweep,
    run_max_iterations_sweep,
    run_scalability_sweep,
    save_experiment_results,
)
from config import (
    get_catalog_dataset,
    validate_experiment_config,
    validate_sweep_config,
)
from pagerank import calculate_pagerank_detailed


# =============================================================================
# 1. Dataset Catalog and Generator Tests
# =============================================================================

def test_static_datasets_catalog_count():
    """Verify ALL_DATASETS contains 7 defined controlled datasets (A-G)."""
    assert len(ALL_DATASETS) == 7
    ids = [d["dataset_id"] for d in ALL_DATASETS]
    assert len(set(ids)) == 7  # All unique IDs


@pytest.mark.parametrize("dataset", ALL_DATASETS)
def test_load_static_datasets_validity(dataset):
    """Verify every static dataset passes Step 4 graph validation."""
    pages, links = load_dataset(dataset)
    assert isinstance(pages, list)
    assert isinstance(links, list)
    assert len(pages) > 0


def test_generate_chain():
    """Verify deterministic chain generation."""
    ds = generate_chain(4)
    assert ds["dataset_id"] == "chain-4"
    assert ds["pages"] == ["N001", "N002", "N003", "N004"]
    assert ds["links"] == [["N001", "N002"], ["N002", "N003"], ["N003", "N004"]]
    pages, links = load_dataset(ds)
    assert len(pages) == 4
    assert len(links) == 3


def test_generate_chain_invalid():
    """Verify generate_chain rejects invalid n."""
    with pytest.raises(ValueError):
        generate_chain(0)
    with pytest.raises(ValueError):
        generate_chain(-5)
    with pytest.raises(ValueError):
        generate_chain(1.5)
    with pytest.raises(ValueError):
        generate_chain(True)


def test_generate_cycle():
    """Verify deterministic cycle generation."""
    ds = generate_cycle(3)
    assert ds["dataset_id"] == "cycle-3"
    assert ds["pages"] == ["N001", "N002", "N003"]
    assert ds["links"] == [["N001", "N002"], ["N002", "N003"], ["N003", "N001"]]
    pages, links = load_dataset(ds)
    assert len(pages) == 3
    assert len(links) == 3


def test_generate_cycle_invalid():
    """Verify generate_cycle rejects invalid n < 2."""
    with pytest.raises(ValueError):
        generate_cycle(1)
    with pytest.raises(ValueError):
        generate_cycle(0)


def test_generate_star():
    """Verify deterministic outward star generation."""
    ds = generate_star(4)
    assert ds["dataset_id"] == "star-4"
    assert ds["pages"] == ["C001", "L001", "L002", "L003"]
    assert ds["links"] == [["C001", "L001"], ["C001", "L002"], ["C001", "L003"]]
    pages, links = load_dataset(ds)
    assert len(pages) == 4
    assert len(links) == 3


def test_generate_star_invalid():
    """Verify generate_star rejects invalid n < 2."""
    with pytest.raises(ValueError):
        generate_star(1)


# =============================================================================
# 2. Detailed PageRank Instrumentation Tests
# =============================================================================

def test_calculate_pagerank_detailed_basic():
    """Verify detailed PageRank returns ranking, iterations, converged, and final_error."""
    pages = ["A", "B", "C"]
    links = [["A", "B"], ["B", "C"], ["C", "A"]]
    res = calculate_pagerank_detailed(pages, links, damping=0.85, max_iterations=100, tol=1e-6)
    assert isinstance(res["ranking"], dict)
    assert set(res["ranking"].keys()) == {"A", "B", "C"}
    assert isinstance(res["iterations"], int)
    assert res["iterations"] > 0
    assert res["converged"] is True
    assert isinstance(res["final_error"], float)
    assert res["final_error"] < 1e-6


def test_calculate_pagerank_detailed_non_convergence():
    """Verify non-convergence when max_iterations is set to 1."""
    pages = ["A", "B", "C"]
    links = [["A", "B"], ["B", "C"]]
    res = calculate_pagerank_detailed(pages, links, damping=0.85, max_iterations=1, tol=1e-12)
    assert res["iterations"] == 1
    assert res["converged"] is False
    assert res["final_error"] > 0.0


def test_calculate_pagerank_detailed_empty_graph():
    """Verify detailed PageRank on empty graph."""
    res = calculate_pagerank_detailed([], [])
    assert res["ranking"] == {}
    assert res["iterations"] == 0
    assert res["converged"] is True
    assert res["final_error"] == 0.0


# =============================================================================
# 3. Experiment Runner & Reproducibility Tests
# =============================================================================

def test_run_experiment_success():
    """Verify single experiment execution with structural analysis and execution metadata."""
    pages = DATASET_A["pages"]
    links = DATASET_A["links"]
    res = run_experiment(pages, links, dataset_id="chain-4")

    assert res["dataset_id"] == "chain-4"
    assert "execution_metadata" in res
    assert "timestamp" in res["execution_metadata"]
    assert res["node_count"] == 4
    assert res["edge_count"] == 3
    assert res["parameters"]["damping"] == 0.85
    assert res["performance"]["converged"] is True
    assert res["performance"]["runtime_seconds"] >= 0.0
    assert "structural_analysis" in res
    assert res["structural_analysis"]["node_count"] == 4


def test_run_experiment_invalid_graph():
    """Verify run_experiment rejects invalid graph input."""
    with pytest.raises(ValueError):
        run_experiment(["A", ""], [["A", "B"]])


def test_run_experiment_invalid_parameters():
    """Verify run_experiment rejects invalid damping, tol, or max_iterations."""
    pages = ["A", "B"]
    links = [["A", "B"]]
    with pytest.raises(ValueError):
        run_experiment(pages, links, damping=1.5)
    with pytest.raises(ValueError):
        run_experiment(pages, links, tol=-0.1)
    with pytest.raises(ValueError):
        run_experiment(pages, links, max_iterations=0)


def test_run_repeated_experiment():
    """Verify repeated experiment produces runtime statistics and ranking stability metrics."""
    pages = DATASET_B["pages"]
    links = DATASET_B["links"]
    res = run_repeated_experiment(pages, links, num_runs=3, dataset_id="cycle-3")

    assert res["num_runs"] == 3
    stats = res["performance_stats"]
    assert len(stats["runtimes_all_seconds"]) == 3
    assert stats["runtime_min_seconds"] <= stats["runtime_mean_seconds"] <= stats["runtime_max_seconds"]
    assert stats["runtime_stddev_seconds"] >= 0.0

    assert "ranking_stability" in res
    assert res["ranking_stability"]["reference_run"] == 1
    assert len(res["ranking_stability"]["comparisons"]) == 2


def test_repeated_experiment_rank_stability():
    """Test 1 — Verify repeated deterministic runs yield rank stability (L1=0, L2=0, Cosine=1, Spearman=1, Kendall=1)."""
    pages = DATASET_C["pages"]
    links = DATASET_C["links"]
    res = run_repeated_experiment(pages, links, num_runs=3, dataset_id="dangling-3")

    stability = res["ranking_stability"]
    assert stability["reference_run"] == 1
    comparisons = stability["comparisons"]
    assert len(comparisons) == 2

    for comp in comparisons:
        metrics = comp["metrics"]
        assert metrics["l1_distance"] == pytest.approx(0.0, abs=1e-12)
        assert metrics["l2_distance"] == pytest.approx(0.0, abs=1e-12)
        assert metrics["cosine_similarity"] == pytest.approx(1.0, abs=1e-12)
        assert metrics["spearman_correlation"] == pytest.approx(1.0, abs=1e-12)
        assert metrics["kendall_tau"] == pytest.approx(1.0, abs=1e-12)
        assert metrics["max_rank_displacement"] == 0
        assert metrics["mean_rank_displacement"] == pytest.approx(0.0, abs=1e-12)


def test_repeated_experiment_multiple_comparisons():
    """Test 2 — Verify that for num_runs = 3, multiple comparisons are recorded against reference run."""
    pages = DATASET_A["pages"]
    links = DATASET_A["links"]
    res3 = run_repeated_experiment(pages, links, num_runs=3, dataset_id="chain-4")
    comparisons = res3["ranking_stability"]["comparisons"]
    assert len(comparisons) == 2
    assert comparisons[0]["run_index"] == 2
    assert comparisons[1]["run_index"] == 3

    # num_runs = 1 case
    res1 = run_repeated_experiment(pages, links, num_runs=1, dataset_id="chain-4")
    assert res1["ranking_stability"]["reference_run"] == 1
    assert len(res1["ranking_stability"]["comparisons"]) == 0


def test_timestamp_separation():
    """Test 3 — Verify timestamp is separated under execution_metadata and deterministic content is independent."""
    pages = DATASET_B["pages"]
    links = DATASET_B["links"]

    res1 = run_experiment(pages, links, dataset_id="cycle-3")
    res2 = run_experiment(pages, links, dataset_id="cycle-3")

    # Timestamp is under execution_metadata
    assert "execution_metadata" in res1
    assert "timestamp" in res1["execution_metadata"]
    assert "execution_metadata" in res2
    assert "timestamp" in res2["execution_metadata"]

    # Deterministic content is identical
    assert res1["dataset_id"] == res2["dataset_id"]
    assert res1["node_count"] == res2["node_count"]
    assert res1["edge_count"] == res2["edge_count"]
    assert res1["parameters"] == res2["parameters"]
    assert res1["ranking"] == res2["ranking"]
    assert res1["performance"]["iterations"] == res2["performance"]["iterations"]
    assert res1["performance"]["converged"] == res2["performance"]["converged"]
    assert res1["performance"]["final_error"] == res2["performance"]["final_error"]


def test_runtime_variability():
    """Test 4 — Verify runtime values are finite and >= 0."""
    pages = DATASET_A["pages"]
    links = DATASET_A["links"]

    res_single = run_experiment(pages, links, dataset_id="chain-4")
    rt_single = res_single["performance"]["runtime_seconds"]
    assert isinstance(rt_single, float)
    assert not math.isnan(rt_single)
    assert not math.isinf(rt_single)
    assert rt_single >= 0.0

    res_rep = run_repeated_experiment(pages, links, num_runs=3, dataset_id="chain-4")
    pstats = res_rep["performance_stats"]
    for rt in pstats["runtimes_all_seconds"]:
        assert isinstance(rt, float)
        assert not math.isnan(rt)
        assert not math.isinf(rt)
        assert rt >= 0.0

    assert not math.isnan(pstats["runtime_mean_seconds"])
    assert pstats["runtime_mean_seconds"] >= 0.0


def test_run_repeated_experiment_invalid_runs():
    """Verify run_repeated_experiment rejects num_runs < 1."""
    pages = ["A", "B"]
    links = [["A", "B"]]
    with pytest.raises(ValueError):
        run_repeated_experiment(pages, links, num_runs=0)


def test_run_damping_sweep():
    """Verify damping parameter sweep with rank stability comparison."""
    pages = DATASET_C["pages"]
    links = DATASET_C["links"]
    dampings = [0.1, 0.5, 0.85, 0.99]
    res = run_damping_sweep(pages, links, damping_values=dampings, dataset_id="dangling-3")

    assert res["sweep_type"] == "damping"
    assert res["count"] == 4
    for record in res["results"]:
        assert "damping" in record
        assert "rank_stability_vs_baseline" in record
        stability = record["rank_stability_vs_baseline"]
        assert "l1_distance" in stability
        assert "spearman_correlation" in stability


def test_run_damping_sweep_invalid():
    """Verify damping sweep rejects empty list or invalid values."""
    pages = ["A", "B"]
    links = [["A", "B"]]
    with pytest.raises(ValueError):
        run_damping_sweep(pages, links, damping_values=[])
    with pytest.raises(ValueError):
        run_damping_sweep(pages, links, damping_values=[0.85, 1.2])


def test_run_tolerance_sweep():
    """Verify tolerance parameter sweep."""
    pages = DATASET_A["pages"]
    links = DATASET_A["links"]
    tols = [1e-2, 1e-4, 1e-6, 1e-8]
    res = run_tolerance_sweep(pages, links, tol_values=tols, dataset_id="chain-4")

    assert res["sweep_type"] == "tolerance"
    assert res["count"] == 4
    assert res["results"][0]["tol"] == 1e-2


def test_run_max_iterations_sweep():
    """Verify max_iterations sweep shows iteration progression."""
    pages = DATASET_B["pages"]
    links = DATASET_B["links"]
    iters = [1, 2, 5, 20]
    res = run_max_iterations_sweep(pages, links, max_iter_values=iters, dataset_id="cycle-3")

    assert res["sweep_type"] == "max_iterations"
    assert res["count"] == 4
    assert res["results"][0]["iterations_performed"] == 1


def test_run_scalability_sweep():
    """Verify scalability sweep using generate_chain."""
    sizes = [3, 5, 10]
    res = run_scalability_sweep(generate_chain, sizes=sizes)

    assert res["sweep_type"] == "scalability"
    assert res["count"] == 3
    assert res["results"][0]["target_size_n"] == 3
    assert res["results"][2]["target_size_n"] == 10


def test_run_scalability_sweep_invalid():
    """Verify scalability sweep rejects non-callable or empty sizes."""
    with pytest.raises(ValueError):
        run_scalability_sweep("not_a_func", [3, 5])
    with pytest.raises(ValueError):
        run_scalability_sweep(generate_chain, [])


def test_save_experiment_results():
    """Verify JSON export of experiment results."""
    data = {"test_key": "test_value", "number": 42}
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = os.path.join(tmpdir, "nested", "results.json")
        res_path = save_experiment_results(data, out_file)

        assert os.path.exists(res_path)
        with open(res_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data


# =============================================================================
# 4. Configuration Model Tests
# =============================================================================

def test_get_catalog_dataset():
    """Verify catalog dataset lookup."""
    ds = get_catalog_dataset("chain-4")
    assert ds["dataset_id"] == "chain-4"

    with pytest.raises(ValueError):
        get_catalog_dataset("nonexistent-dataset")


def test_validate_experiment_config():
    """Verify experiment config validation."""
    config = {
        "dataset_id": "cycle-3",
        "damping": 0.85,
        "max_iterations": 50,
        "tol": 1e-5,
    }
    validated = validate_experiment_config(config)
    assert validated["dataset_id"] == "cycle-3"
    assert len(validated["pages"]) == 3
    assert validated["damping"] == 0.85


def test_validate_sweep_config():
    """Verify sweep config validation."""
    config = {
        "sweep_type": "damping",
        "values": [0.1, 0.5, 0.85],
    }
    validated = validate_sweep_config(config)
    assert validated["sweep_type"] == "damping"

    with pytest.raises(ValueError):
        validate_sweep_config({"sweep_type": "invalid_type", "values": [1, 2]})
