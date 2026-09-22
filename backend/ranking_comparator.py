"""
Ranking Comparison Layer for PageRank application.

Provides objective mathematical comparison metrics between two ranking vectors
over the same node set.

Supported Metrics:
1. Vector validation & common-node alignment
2. L1 distance
3. L2 distance
4. Cosine similarity (with zero-vector protection)
5. Spearman rank correlation (with fractional rank tie-handling)
6. Kendall tau-b rank correlation (with tie-handling)
7. Top-k overlap (with deterministic lexicographical tie-breaking)
8. Rank displacement statistics (max, mean, per-node displacement)
9. Consolidated comparison summary
"""

import math


def validate_ranking_vector(ranking, name="ranking"):
    """
    Validate a ranking vector dictionary.

    Rules:
    - Must be a dictionary.
    - Cannot be empty (if required for comparison).
    - Keys must be non-empty strings (node identifiers).
    - Values must be finite numbers (int or float, not bool, not NaN, not inf).

    :param ranking: dict mapping node ID -> numeric score.
    :param name: String label for error messages.
    :return: dict of validated node -> float score mappings.
    :raises ValueError: If structure or types are invalid.
    """
    if not isinstance(ranking, dict):
        raise ValueError(f"'{name}' must be a dictionary mapping node ID -> score, got {type(ranking).__name__}.")

    validated = {}
    for node, score in ranking.items():
        if not isinstance(node, str) or not node.strip():
            raise ValueError(f"'{name}' contains invalid node identifier: {node!r}. Node IDs must be non-empty strings.")

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError(f"'{name}[{node!r}]' score must be a number, got {type(score).__name__}: {score!r}.")

        s = float(score)
        if math.isnan(s) or math.isinf(s):
            raise ValueError(f"'{name}[{node!r}]' score must be a finite number, got {score!r}.")

        validated[node] = s

    return validated


def align_rankings(ranking_a, ranking_b):
    """
    Validate and align two ranking vectors onto a common deterministic node set.

    :param ranking_a: dict mapping node ID -> score
    :param ranking_b: dict mapping node ID -> score
    :return: Tuple (nodes: list[str], vector_a: list[float], vector_b: list[float])
    :raises ValueError: If input is invalid or node sets do not match.
    """
    val_a = validate_ranking_vector(ranking_a, "ranking_a")
    val_b = validate_ranking_vector(ranking_b, "ranking_b")

    set_a = set(val_a.keys())
    set_b = set(val_b.keys())

    if set_a != set_b:
        missing_in_b = sorted(set_a - set_b)
        missing_in_a = sorted(set_b - set_a)
        diff_msgs = []
        if missing_in_b:
            diff_msgs.append(f"Nodes in ranking_a but missing in ranking_b: {missing_in_b[:5]}")
        if missing_in_a:
            diff_msgs.append(f"Nodes in ranking_b but missing in ranking_a: {missing_in_a[:5]}")
        raise ValueError(f"Rankings must refer to the exact same node set. {'; '.join(diff_msgs)}")

    nodes = sorted(set_a)
    vec_a = [val_a[node] for node in nodes]
    vec_b = [val_b[node] for node in nodes]

    return nodes, vec_a, vec_b


def calculate_l1_distance(vec_a, vec_b):
    """
    Calculate L1 distance: sum(|A_i - B_i|).
    """
    return float(sum(abs(a - b) for a, b in zip(vec_a, vec_b)))


def calculate_l2_distance(vec_a, vec_b):
    """
    Calculate L2 distance: sqrt(sum((A_i - B_i)^2)).
    """
    return float(math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b))))


def calculate_cosine_similarity(vec_a, vec_b):
    """
    Calculate cosine similarity: (A . B) / (||A|| * ||B||).
    Returns 1.0 if both vectors are identically zero, or 0.0 if one is zero vector.
    """
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0 if norm_a == norm_b == 0.0 else 0.0

    return float(max(-1.0, min(1.0, dot / (norm_a * norm_b))))


def get_fractional_ranks(vector):
    """
    Compute 1-based fractional ranks for a numeric vector (handling ties with average ranks).
    Higher values receive higher rank values (e.g. 1.0 < 2.0).
    """
    N = len(vector)
    if N == 0:
        return []

    # Pair value with original index
    indexed = sorted((val, idx) for idx, val in enumerate(vector))

    ranks = [0.0] * N
    i = 0
    while i < N:
        j = i
        while j < N and indexed[j][0] == indexed[i][0]:
            j += 1
        # Average rank for tie group (1-indexed)
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            orig_idx = indexed[k][1]
            ranks[orig_idx] = avg_rank
        i = j

    return ranks


def calculate_spearman_correlation(vec_a, vec_b):
    """
    Calculate Spearman rank correlation coefficient with fractional rank tie handling.
    """
    N = len(vec_a)
    if N < 2:
        return 1.0 if vec_a == vec_b else 0.0

    ranks_a = get_fractional_ranks(vec_a)
    ranks_b = get_fractional_ranks(vec_b)

    mean_a = sum(ranks_a) / N
    mean_b = sum(ranks_b) / N

    num = sum((ra - mean_a) * (rb - mean_b) for ra, rb in zip(ranks_a, ranks_b))
    denom_a = math.sqrt(sum((ra - mean_a) ** 2 for ra in ranks_a))
    denom_b = math.sqrt(sum((rb - mean_b) ** 2 for rb in ranks_b))

    if denom_a == 0.0 or denom_b == 0.0:
        return 1.0 if ranks_a == ranks_b else 0.0

    return float(max(-1.0, min(1.0, num / (denom_a * denom_b))))


def calculate_kendall_tau(vec_a, vec_b):
    """
    Calculate Kendall tau-b rank correlation coefficient (handling ties).
    """
    N = len(vec_a)
    if N < 2:
        return 1.0 if vec_a == vec_b else 0.0

    concordant = 0
    discordant = 0
    extra_a = 0
    extra_b = 0

    for i in range(N):
        for j in range(i + 1, N):
            diff_a = vec_a[i] - vec_a[j]
            diff_b = vec_b[i] - vec_b[j]

            sign_a = (diff_a > 0) - (diff_a < 0)
            sign_b = (diff_b > 0) - (diff_b < 0)

            prod = sign_a * sign_b
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            else:
                if sign_a != 0 and sign_b == 0:
                    extra_b += 1
                elif sign_a == 0 and sign_b != 0:
                    extra_a += 1

    denom = math.sqrt((concordant + discordant + extra_a) * (concordant + discordant + extra_b))
    if denom == 0.0:
        return 1.0 if vec_a == vec_b else 0.0

    tau_b = (concordant - discordant) / denom
    return float(max(-1.0, min(1.0, tau_b)))


def calculate_top_k_overlap(nodes, vec_a, vec_b, k_values=None):
    """
    Calculate Top-K overlap ratio for specified k values.

    Deterministic tie-breaking:
    Sort nodes by score descending, then by node ID ascending.

    :param nodes: List of aligned node IDs.
    :param vec_a: Score vector A.
    :param vec_b: Score vector B.
    :param k_values: List of int k values (or None for default [1, 3, 5, 10] bounded by N).
    :return: dict mapping k -> overlap ratio (float in [0.0, 1.0]).
    """
    N = len(nodes)
    if N == 0:
        return {}

    if k_values is None:
        k_values = [k for k in [1, 3, 5, 10] if k <= N]
        if not k_values and N > 0:
            k_values = [N]
    else:
        k_values = [k for k in k_values if 1 <= k <= N]

    # Deterministic sorting for ranking A (score desc, node ID asc)
    nodes_a_sorted = [node for node, score in sorted(zip(nodes, vec_a), key=lambda x: (-x[1], x[0]))]
    nodes_b_sorted = [node for node, score in sorted(zip(nodes, vec_b), key=lambda x: (-x[1], x[0]))]

    overlap_results = {}
    for k in k_values:
        set_a_k = set(nodes_a_sorted[:k])
        set_b_k = set(nodes_b_sorted[:k])
        intersection = set_a_k.intersection(set_b_k)
        overlap_results[k] = float(len(intersection) / k)

    return overlap_results


def calculate_rank_displacements(nodes, vec_a, vec_b):
    """
    Calculate rank displacement statistics between two rankings.

    Rank is 1-indexed (1 = highest score). Ties broken deterministically by node ID.

    :param nodes: List of aligned node IDs.
    :param vec_a: Score vector A.
    :param vec_b: Score vector B.
    :return: Tuple (max_displacement: int, mean_displacement: float, displacements: dict[str, int])
    """
    N = len(nodes)
    if N == 0:
        return 0, 0.0, {}

    nodes_a_sorted = [node for node, score in sorted(zip(nodes, vec_a), key=lambda x: (-x[1], x[0]))]
    nodes_b_sorted = [node for node, score in sorted(zip(nodes, vec_b), key=lambda x: (-x[1], x[0]))]

    rank_a = {node: idx + 1 for idx, node in enumerate(nodes_a_sorted)}
    rank_b = {node: idx + 1 for idx, node in enumerate(nodes_b_sorted)}

    displacements = {}
    for node in nodes:
        displacements[node] = abs(rank_a[node] - rank_b[node])

    max_disp = max(displacements.values()) if displacements else 0
    mean_disp = float(sum(displacements.values()) / N) if N > 0 else 0.0

    return max_disp, mean_disp, displacements


def compare_rankings(ranking_a, ranking_b, top_k=None):
    """
    Consolidated ranking comparison function.

    :param ranking_a: dict mapping node ID -> score
    :param ranking_b: dict mapping node ID -> score
    :param top_k: Optional list of integer k values for top-k overlap.
    :return: dict of mathematical comparison metrics.
    """
    nodes, vec_a, vec_b = align_rankings(ranking_a, ranking_b)
    N = len(nodes)

    l1 = calculate_l1_distance(vec_a, vec_b)
    l2 = calculate_l2_distance(vec_a, vec_b)
    cosine = calculate_cosine_similarity(vec_a, vec_b)
    spearman = calculate_spearman_correlation(vec_a, vec_b)
    kendall = calculate_kendall_tau(vec_a, vec_b)
    overlap = calculate_top_k_overlap(nodes, vec_a, vec_b, k_values=top_k)
    max_disp, mean_disp, displacements = calculate_rank_displacements(nodes, vec_a, vec_b)

    return {
        "node_count": N,
        "l1_distance": l1,
        "l2_distance": l2,
        "cosine_similarity": cosine,
        "spearman_correlation": spearman,
        "kendall_tau": kendall,
        "top_k_overlap": overlap,
        "max_rank_displacement": max_disp,
        "mean_rank_displacement": mean_disp,
        "rank_displacements": displacements,
    }
