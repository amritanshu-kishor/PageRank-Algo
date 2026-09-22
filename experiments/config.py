"""
Experiment configuration model and validation for PageRank research framework.

Provides configuration validation for experiment runs, parameter sweeps, and dataset catalog lookup.
"""

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from graph_validator import validate_graph, validate_pagerank_params
from datasets import ALL_DATASETS, load_dataset


DATASET_CATALOG = {d["dataset_id"]: d for d in ALL_DATASETS}


def get_catalog_dataset(dataset_id):
    """
    Look up a static dataset definition by ID from the catalog.

    :param dataset_id: String ID (e.g., 'chain-4', 'cycle-3').
    :return: dict dataset definition.
    :raises ValueError: If dataset_id is not in the catalog.
    """
    if not isinstance(dataset_id, str):
        raise ValueError(f"dataset_id must be a string, got {type(dataset_id).__name__}")
    if dataset_id not in DATASET_CATALOG:
        valid_ids = sorted(list(DATASET_CATALOG.keys()))
        raise ValueError(
            f"Unknown dataset_id {dataset_id!r}. Available datasets: {valid_ids}"
        )
    return DATASET_CATALOG[dataset_id]


def validate_experiment_config(config):
    """
    Validate a complete experiment configuration dictionary.

    Expected config keys:
      - 'dataset': dict with 'pages' and 'links' (or 'dataset_id' to look up catalog)
      - 'damping' (optional, default 0.85)
      - 'max_iterations' (optional, default 100)
      - 'tol' (optional, default 1e-6)

    :param config: dict experiment specification.
    :return: dict sanitized configuration ready for execution.
    :raises ValueError: If any configuration option is invalid.
    """
    if not isinstance(config, dict):
        raise ValueError(f"Experiment config must be a dict, got {type(config).__name__}")

    # Dataset resolution
    if "dataset_id" in config and ("pages" not in config or "links" not in config):
        ds = get_catalog_dataset(config["dataset_id"])
        pages = ds["pages"]
        links = ds["links"]
        dataset_id = ds["dataset_id"]
    elif "pages" in config and "links" in config:
        pages = config["pages"]
        links = config["links"]
        dataset_id = config.get("dataset_id", "custom")
    elif "dataset" in config and isinstance(config["dataset"], dict):
        ds = config["dataset"]
        pages = ds["pages"]
        links = ds["links"]
        dataset_id = ds.get("dataset_id", "custom")
    else:
        raise ValueError(
            "Experiment config must specify dataset ('pages' and 'links' or 'dataset_id')"
        )

    # Validate graph
    valid_pages, valid_links = validate_graph(pages, links)

    # Validate parameters
    damping = config.get("damping", 0.85)
    tol = config.get("tol", 1.0e-6)
    max_iterations = config.get("max_iterations", 100)

    valid_params = validate_pagerank_params(
        damping=damping, tol=tol, max_iterations=max_iterations
    )

    return {
        "dataset_id": dataset_id,
        "pages": valid_pages,
        "links": valid_links,
        "damping": valid_params["damping"],
        "tol": valid_params["tol"],
        "max_iterations": valid_params["max_iterations"],
    }


def validate_sweep_config(sweep_config):
    """
    Validate a parameter sweep configuration.

    Expected keys:
      - 'sweep_type': 'damping', 'tolerance', 'max_iterations', or 'scalability'
      - 'values': sequence of parameter values to sweep
      - 'dataset' or 'dataset_id' or ('pages', 'links')
      - base algorithm parameters

    :param sweep_config: dict sweep specification.
    :return: dict sanitized sweep configuration.
    :raises ValueError: If sweep_config is invalid.
    """
    if not isinstance(sweep_config, dict):
        raise ValueError(f"Sweep config must be a dict, got {type(sweep_config).__name__}")

    sweep_type = sweep_config.get("sweep_type")
    valid_types = {"damping", "tolerance", "max_iterations", "scalability"}
    if sweep_type not in valid_types:
        raise ValueError(
            f"Invalid sweep_type {sweep_type!r}. Must be one of {sorted(list(valid_types))}"
        )

    values = sweep_config.get("values")
    if not isinstance(values, (list, tuple)) or len(values) == 0:
        raise ValueError(f"Sweep 'values' must be a non-empty list or tuple, got {values!r}")

    # Validate individual value types depending on sweep type
    if sweep_type == "damping":
        for v in values:
            validate_pagerank_params(damping=v)
    elif sweep_type == "tolerance":
        for v in values:
            validate_pagerank_params(tol=v)
    elif sweep_type == "max_iterations":
        for v in values:
            validate_pagerank_params(max_iterations=v)
    elif sweep_type == "scalability":
        for v in values:
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                raise ValueError(
                    f"Scalability size values must be positive integers, got {v!r}"
                )

    return sweep_config
