"""
Graph validation and sanitization for the PageRank application.

Establishes the validation boundary between raw API input and the PageRank core.

Flow:
    RAW INPUT  →  validate_graph()  →  VALID GRAPH  →  calculate_pagerank()

Contract enforced here:
- nodes must be non-empty strings
- edges must be two-element sequences of non-empty strings
- numeric parameters (damping, tol, max_iterations) are range-checked
- malformed input raises ValueError with a descriptive message
- valid input is returned as normalized (pages: list[str], links: list[list[str]])
"""

import math


def validate_node_id(value):
    """
    Return True if value is a valid node identifier: a non-empty string.

    Node identifiers must be:
    - Python str type
    - Non-empty (not just whitespace)

    Spaces within identifiers are allowed (e.g. 'My Page').
    Unicode is allowed.
    URLs are allowed as identifiers.
    """
    return isinstance(value, str) and len(value.strip()) > 0


def validate_graph(pages, links):
    """
    Validate and normalise raw graph input.

    Validation rules:
    - ``pages`` must be a list (not a string or other iterable).
    - Each element of ``pages`` must be a non-empty string.
    - ``links`` must be a list.
    - Each element of ``links`` must be a sequence of exactly 2 non-empty strings.
    - Duplicate node IDs in ``pages`` are accepted; first occurrence is kept.
    - Duplicate edges in ``links`` are accepted; the PageRank core deduplicates them.
    - Edges referencing nodes not in ``pages`` are accepted; the PageRank core filters them.

    :param pages: Raw pages value from API payload.
    :param links: Raw links value from API payload.
    :return: Tuple (pages: list[str], links: list[list[str]]) — normalised.
    :raises ValueError: With a descriptive message if input is structurally invalid.
    """
    # --- Validate pages ---
    if not isinstance(pages, list):
        raise ValueError(
            f"'pages' must be a list of strings, got {type(pages).__name__}."
        )
    for i, node in enumerate(pages):
        if not isinstance(node, str):
            raise ValueError(
                f"'pages[{i}]' must be a non-empty string, "
                f"got {type(node).__name__}: {node!r}."
            )
        if not node.strip():
            raise ValueError(
                f"'pages[{i}]' must be a non-empty string, got empty or whitespace-only string."
            )

    # --- Validate links ---
    if not isinstance(links, list):
        raise ValueError(
            f"'links' must be a list of [source, target] pairs, got {type(links).__name__}."
        )
    for i, edge in enumerate(links):
        # Edge must be a sequence (list or tuple), not a bare string
        if isinstance(edge, str) or not hasattr(edge, '__len__') or not hasattr(edge, '__getitem__'):
            raise ValueError(
                f"'links[{i}]' must be a [source, target] pair, got {type(edge).__name__}: {edge!r}."
            )
        if len(edge) < 2:
            raise ValueError(
                f"'links[{i}]' must have exactly 2 elements [source, target], "
                f"got {len(edge)} element(s): {edge!r}."
            )
        source, target = edge[0], edge[1]
        if not isinstance(source, str):
            raise ValueError(
                f"'links[{i}][0]' (source) must be a non-empty string, "
                f"got {type(source).__name__}: {source!r}."
            )
        if not source.strip():
            raise ValueError(
                f"'links[{i}][0]' (source) must be a non-empty string, "
                f"got empty or whitespace-only string."
            )
        if not isinstance(target, str):
            raise ValueError(
                f"'links[{i}][1]' (target) must be a non-empty string, "
                f"got {type(target).__name__}: {target!r}."
            )
        if not target.strip():
            raise ValueError(
                f"'links[{i}][1]' (target) must be a non-empty string, "
                f"got empty or whitespace-only string."
            )

    # Return normalised types (ensure links inner elements are lists)
    normalised_links = [[str(edge[0]), str(edge[1])] for edge in links]
    return list(pages), normalised_links


def validate_pagerank_params(damping=None, tol=None, max_iterations=None):
    """
    Validate optional numeric PageRank parameters from API input.

    Rules:
    - damping: float strictly in (0, 1), not NaN, not infinite.
    - tol: positive finite float (> 0, not NaN, not infinite).
    - max_iterations: positive integer (>= 1).

    Only parameters that are not None are validated.
    Parameters that pass validation are returned unchanged.

    :param damping: Damping factor (optional).
    :param tol: Convergence tolerance (optional).
    :param max_iterations: Maximum iteration count (optional).
    :return: dict of validated values keyed by parameter name.
    :raises ValueError: If any provided parameter is invalid.
    """
    result = {}

    if damping is not None:
        if not isinstance(damping, (int, float)):
            raise ValueError(
                f"'damping' must be a number in (0, 1), got {type(damping).__name__}: {damping!r}."
            )
        d = float(damping)
        if math.isnan(d) or math.isinf(d):
            raise ValueError(
                f"'damping' must be a finite number, got {damping!r}."
            )
        if not (0.0 < d < 1.0):
            raise ValueError(
                f"'damping' must be strictly between 0 and 1, got {damping}."
            )
        result['damping'] = d

    if tol is not None:
        if not isinstance(tol, (int, float)):
            raise ValueError(
                f"'tol' must be a positive number, got {type(tol).__name__}: {tol!r}."
            )
        t = float(tol)
        if math.isnan(t) or math.isinf(t):
            raise ValueError(
                f"'tol' must be a finite number, got {tol!r}."
            )
        if t <= 0.0:
            raise ValueError(
                f"'tol' must be positive (> 0), got {tol}."
            )
        result['tol'] = t

    if max_iterations is not None:
        if not isinstance(max_iterations, int) or isinstance(max_iterations, bool):
            raise ValueError(
                f"'max_iterations' must be a positive integer, "
                f"got {type(max_iterations).__name__}: {max_iterations!r}."
            )
        if max_iterations < 1:
            raise ValueError(
                f"'max_iterations' must be at least 1, got {max_iterations}."
            )
        result['max_iterations'] = max_iterations

    return result
