"""
Experiment execution and measurement layer for PageRank research framework.

Provides deterministic, reproducible measurement functions for PageRank execution,
graph structural properties, parameter sensitivity sweeps, scalability benchmarking,
and rank stability analysis.

Uses:
  - backend/graph_validator.py for parameter and graph validation
  - backend/graph_analyzer.py for structural graph metrics
  - backend/pagerank.py (calculate_pagerank_detailed) for execution metrics
  - backend/ranking_comparator.py for rank stability metrics
"""

import datetime
import json
import math
import sys
import time
from pathlib import Path

# Ensure backend modules can be imported
_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from graph_validator import validate_graph, validate_pagerank_params
from graph_analyzer import analyze_graph
from pagerank import calculate_pagerank_detailed
from ranking_comparator import compare_rankings


def run_experiment(
    pages,
    links,
    damping=0.85,
    max_iterations=100,
    tol=1.0e-6,
    dataset_id="custom",
    include_graph_analysis=True,
):
    """
    Run a single controlled experiment configuration on a validated graph.

    :param pages: List of node identifiers.
    :param links: List of directed edges [[source, target], ...].
    :param damping: Damping factor d (0 < d < 1). Default 0.85.
    :param max_iterations: Maximum iterations (>= 1). Default 100.
    :param tol: L1 convergence tolerance (> 0). Default 1e-6.
    :param dataset_id: Identifier tag for the dataset. Default "custom".
    :param include_graph_analysis: If True, include structural analysis dict.
    :return: dict with comprehensive, machine-readable experiment results.
             Deterministic content is kept at top level; non-deterministic
             execution timestamp is stored under execution_metadata.
    :raises ValueError: If graph or parameters are invalid.
    """
    # 1. Validate graph input
    valid_pages, valid_links = validate_graph(pages, links)

    # 2. Validate PageRank parameters
    validated_params = validate_pagerank_params(
        damping=damping, tol=tol, max_iterations=max_iterations
    )
    d = validated_params["damping"]
    t = validated_params["tol"]
    m = validated_params["max_iterations"]

    # 3. Structural graph analysis
    structural_analysis = None
    if include_graph_analysis:
        structural_analysis = analyze_graph(valid_pages, valid_links, validate=False)

    # 4. Measure execution
    t_start = time.perf_counter()
    detailed_result = calculate_pagerank_detailed(
        valid_pages, valid_links, damping=d, max_iterations=m, tol=t
    )
    t_end = time.perf_counter()
    runtime_seconds = t_end - t_start

    result = {
        "dataset_id": dataset_id,
        "node_count": len(valid_pages),
        "edge_count": len(valid_links),
        "parameters": {
            "damping": d,
            "tol": t,
            "max_iterations": m,
        },
        "performance": {
            "runtime_seconds": runtime_seconds,
            "iterations": detailed_result["iterations"],
            "converged": detailed_result["converged"],
            "final_error": detailed_result["final_error"],
        },
        "ranking": detailed_result["ranking"],
        "execution_metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }

    if structural_analysis is not None:
        result["structural_analysis"] = structural_analysis

    return result


def run_repeated_experiment(
    pages,
    links,
    num_runs=5,
    damping=0.85,
    max_iterations=100,
    tol=1.0e-6,
    dataset_id="custom",
):
    """
    Run an experiment multiple times to measure runtime stability and rank stability.

    Executes the PageRank algorithm num_runs times. Compares each run's ranking output
    against the reference ranking (Run 1) using compare_rankings() from Step 8.

    :param pages: List of node identifiers.
    :param links: List of directed edges.
    :param num_runs: Number of repetitions (must be >= 1). Default 5.
    :param damping: Damping factor d.
    :param max_iterations: Maximum iterations.
    :param tol: Convergence tolerance.
    :param dataset_id: Identifier string.
    :return: dict with performance statistics, rank stability comparison metrics,
             reference ranking, and execution metadata.
    :raises ValueError: If num_runs < 1 or input validation fails.
    """
    if not isinstance(num_runs, int) or isinstance(num_runs, bool) or num_runs < 1:
        raise ValueError(f"num_runs must be an integer >= 1, got {num_runs!r}")

    # Validate graph & params once up front
    valid_pages, valid_links = validate_graph(pages, links)
    validated_params = validate_pagerank_params(
        damping=damping, tol=tol, max_iterations=max_iterations
    )
    d = validated_params["damping"]
    t = validated_params["tol"]
    m = validated_params["max_iterations"]

    runtimes = []
    rankings_all = []
    last_result = None

    for _ in range(num_runs):
        t_start = time.perf_counter()
        res = calculate_pagerank_detailed(
            valid_pages, valid_links, damping=d, max_iterations=m, tol=t
        )
        t_end = time.perf_counter()
        runtimes.append(t_end - t_start)
        rankings_all.append(res["ranking"])
        last_result = res

    # Compute runtime performance statistics
    mean_runtime = sum(runtimes) / len(runtimes)
    min_runtime = min(runtimes)
    max_runtime = max(runtimes)

    if len(runtimes) > 1:
        variance = sum((x - mean_runtime) ** 2 for x in runtimes) / (len(runtimes) - 1)
        stddev_runtime = math.sqrt(variance)
    else:
        stddev_runtime = 0.0

    # Compute rank stability across repeated runs using Step 8 compare_rankings()
    # Reference run is Run 1 (index 0).
    ref_ranking = rankings_all[0]
    comparisons = []
    for idx in range(1, num_runs):
        metrics = compare_rankings(rankings_all[idx], ref_ranking)
        comparisons.append({
            "run_index": idx + 1,
            "metrics": metrics,
        })

    ranking_stability = {
        "reference_run": 1,
        "comparisons": comparisons,
    }

    return {
        "dataset_id": dataset_id,
        "num_runs": num_runs,
        "parameters": {
            "damping": d,
            "tol": t,
            "max_iterations": m,
        },
        "performance_stats": {
            "runtime_mean_seconds": mean_runtime,
            "runtime_min_seconds": min_runtime,
            "runtime_max_seconds": max_runtime,
            "runtime_stddev_seconds": stddev_runtime,
            "runtimes_all_seconds": runtimes,
            "iterations": last_result["iterations"],
            "converged": last_result["converged"],
            "final_error": last_result["final_error"],
        },
        "ranking_stability": ranking_stability,
        "ranking": ref_ranking,
        "execution_metadata": {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }


def run_damping_sweep(
    pages,
    links,
    damping_values,
    max_iterations=100,
    tol=1.0e-6,
    baseline_damping=0.85,
    dataset_id="custom",
):
    """
    Perform a parameter sweep over a list of damping values.

    Computes execution metrics for each damping value, as well as rank stability
    metrics relative to the baseline_damping ranking using Step 8 ranking comparison.

    :param pages: List of node identifiers.
    :param links: List of directed edges.
    :param damping_values: Iterable of damping factor floats in (0, 1).
    :param max_iterations: Maximum iterations per run.
    :param tol: Convergence tolerance per run.
    :param baseline_damping: Damping factor used as baseline for comparison. Default 0.85.
    :param dataset_id: Identifier string.
    :return: dict with sweep results and stability comparisons.
    :raises ValueError: If damping_values is empty or contains invalid values.
    """
    if not isinstance(damping_values, (list, tuple)) or len(damping_values) == 0:
        raise ValueError("damping_values must be a non-empty sequence")

    # Validate graph up front
    valid_pages, valid_links = validate_graph(pages, links)

    # First, run baseline configuration
    baseline_result = run_experiment(
        valid_pages,
        valid_links,
        damping=baseline_damping,
        max_iterations=max_iterations,
        tol=tol,
        dataset_id=dataset_id,
        include_graph_analysis=False,
    )
    baseline_ranking = baseline_result["ranking"]

    sweep_records = []
    for d in damping_values:
        # Validate individual damping parameter
        exp = run_experiment(
            valid_pages,
            valid_links,
            damping=d,
            max_iterations=max_iterations,
            tol=tol,
            dataset_id=dataset_id,
            include_graph_analysis=False,
        )

        # Rank stability comparison against baseline
        if len(baseline_ranking) > 0:
            stability = compare_rankings(exp["ranking"], baseline_ranking)
        else:
            stability = None

        record = {
            "damping": exp["parameters"]["damping"],
            "iterations": exp["performance"]["iterations"],
            "converged": exp["performance"]["converged"],
            "final_error": exp["performance"]["final_error"],
            "runtime_seconds": exp["performance"]["runtime_seconds"],
            "rank_stability_vs_baseline": stability,
            "ranking": exp["ranking"],
        }
        sweep_records.append(record)

    return {
        "dataset_id": dataset_id,
        "sweep_type": "damping",
        "baseline_damping": baseline_damping,
        "count": len(sweep_records),
        "results": sweep_records,
    }


def run_tolerance_sweep(
    pages,
    links,
    tol_values,
    damping=0.85,
    max_iterations=100,
    baseline_tol=1.0e-6,
    dataset_id="custom",
):
    """
    Perform a parameter sweep over a list of tolerance values.

    :param pages: List of node identifiers.
    :param links: List of directed edges.
    :param tol_values: Iterable of tolerance floats (> 0).
    :param damping: Damping factor. Default 0.85.
    :param max_iterations: Maximum iterations. Default 100.
    :param baseline_tol: Tolerance value for baseline comparison. Default 1e-6.
    :param dataset_id: Identifier string.
    :return: dict with sweep results.
    :raises ValueError: If tol_values is empty or contains invalid values.
    """
    if not isinstance(tol_values, (list, tuple)) or len(tol_values) == 0:
        raise ValueError("tol_values must be a non-empty sequence")

    valid_pages, valid_links = validate_graph(pages, links)

    baseline_result = run_experiment(
        valid_pages,
        valid_links,
        damping=damping,
        max_iterations=max_iterations,
        tol=baseline_tol,
        dataset_id=dataset_id,
        include_graph_analysis=False,
    )
    baseline_ranking = baseline_result["ranking"]

    sweep_records = []
    for t in tol_values:
        exp = run_experiment(
            valid_pages,
            valid_links,
            damping=damping,
            max_iterations=max_iterations,
            tol=t,
            dataset_id=dataset_id,
            include_graph_analysis=False,
        )

        if len(baseline_ranking) > 0:
            stability = compare_rankings(exp["ranking"], baseline_ranking)
        else:
            stability = None

        record = {
            "tol": exp["parameters"]["tol"],
            "iterations": exp["performance"]["iterations"],
            "converged": exp["performance"]["converged"],
            "final_error": exp["performance"]["final_error"],
            "runtime_seconds": exp["performance"]["runtime_seconds"],
            "rank_stability_vs_baseline": stability,
            "ranking": exp["ranking"],
        }
        sweep_records.append(record)

    return {
        "dataset_id": dataset_id,
        "sweep_type": "tolerance",
        "baseline_tol": baseline_tol,
        "count": len(sweep_records),
        "results": sweep_records,
    }


def run_max_iterations_sweep(
    pages,
    links,
    max_iter_values,
    damping=0.85,
    tol=1.0e-6,
    dataset_id="custom",
):
    """
    Perform a sweep over max_iterations thresholds to observe convergence progression.

    :param pages: List of node identifiers.
    :param links: List of directed edges.
    :param max_iter_values: Iterable of max_iterations integers (>= 1).
    :param damping: Damping factor. Default 0.85.
    :param tol: Convergence tolerance. Default 1e-6.
    :param dataset_id: Identifier string.
    :return: dict with sweep results across iteration caps.
    :raises ValueError: If max_iter_values is empty or contains invalid values.
    """
    if not isinstance(max_iter_values, (list, tuple)) or len(max_iter_values) == 0:
        raise ValueError("max_iter_values must be a non-empty sequence")

    valid_pages, valid_links = validate_graph(pages, links)

    sweep_records = []
    for m in max_iter_values:
        exp = run_experiment(
            valid_pages,
            valid_links,
            damping=damping,
            max_iterations=m,
            tol=tol,
            dataset_id=dataset_id,
            include_graph_analysis=False,
        )
        record = {
            "max_iterations": exp["parameters"]["max_iterations"],
            "iterations_performed": exp["performance"]["iterations"],
            "converged": exp["performance"]["converged"],
            "final_error": exp["performance"]["final_error"],
            "runtime_seconds": exp["performance"]["runtime_seconds"],
            "ranking": exp["ranking"],
        }
        sweep_records.append(record)

    return {
        "dataset_id": dataset_id,
        "sweep_type": "max_iterations",
        "count": len(sweep_records),
        "results": sweep_records,
    }


def run_scalability_sweep(
    generator_fn,
    sizes,
    damping=0.85,
    max_iterations=100,
    tol=1.0e-6,
):
    """
    Perform a scalability experiment by generating graphs of increasing sizes.

    :param generator_fn: Callable taking size n and returning a dataset dict with 'pages' and 'links'.
    :param sizes: Iterable of integer graph sizes n.
    :param damping: Damping factor. Default 0.85.
    :param max_iterations: Max iterations. Default 100.
    :param tol: Convergence tolerance. Default 1e-6.
    :return: dict with scalability benchmark results.
    :raises ValueError: If generator_fn is not callable or sizes is empty/invalid.
    """
    if not callable(generator_fn):
        raise ValueError("generator_fn must be a callable function")
    if not isinstance(sizes, (list, tuple)) or len(sizes) == 0:
        raise ValueError("sizes must be a non-empty sequence")

    sweep_records = []
    for n in sizes:
        dataset = generator_fn(n)
        pages = dataset["pages"]
        links = dataset["links"]
        dataset_id = dataset.get("dataset_id", f"scale-{n}")

        exp = run_experiment(
            pages,
            links,
            damping=damping,
            max_iterations=max_iterations,
            tol=tol,
            dataset_id=dataset_id,
            include_graph_analysis=True,
        )

        record = {
            "target_size_n": n,
            "node_count": exp["node_count"],
            "edge_count": exp["edge_count"],
            "density": exp["structural_analysis"]["density"],
            "runtime_seconds": exp["performance"]["runtime_seconds"],
            "iterations": exp["performance"]["iterations"],
            "converged": exp["performance"]["converged"],
            "final_error": exp["performance"]["final_error"],
        }
        sweep_records.append(record)

    return {
        "sweep_type": "scalability",
        "count": len(sweep_records),
        "results": sweep_records,
    }


def save_experiment_results(results, output_path):
    """
    Serialize experiment results to a machine-readable JSON file.

    :param results: dict containing experiment results.
    :param output_path: str or Path destination file path.
    :return: str resolved output file path.
    :raises ValueError: If results is not a dict or cannot be serialized.
    """
    if not isinstance(results, dict):
        raise ValueError(f"results must be a dict, got {type(results).__name__}")

    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)

    return str(path)
