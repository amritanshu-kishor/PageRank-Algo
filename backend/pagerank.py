def calculate_pagerank(pages, links, damping=0.85, max_iterations=100, tol=1.0e-6):
    """
    Computes the PageRank of given pages and links using standard power iteration.

    Mathematical model:

        PR(i) = (1 - damping) / N
                + damping * [ dangling_rank / N
                              + sum over valid incoming j: PR(j) / outgoing_links[j] ]

    where dangling_rank is the total PageRank held by dangling nodes (nodes with no
    valid outgoing edges). This redistributes dangling rank uniformly across all nodes
    at every iteration, preserving mass conservation throughout the iteration process.

    Graph semantics:
    - An edge (source, target) is valid only if both source AND target exist in pages.
    - Duplicate edges are deduplicated; only one copy of each (source, target) pair counts.
    - Self-loops (A -> A) are valid directed edges and handled naturally by the formula.
    - Disconnected components are handled correctly under the teleportation model.
    - Dangling nodes (no valid outgoing edges) redistribute their rank to all nodes.

    Convergence criterion: L1 norm — sum of |PR_new(i) - PR_old(i)| over all nodes.
    Iteration stops when error < tol OR max_iterations is reached.
    Node order is deterministic: preserved from the input pages list order.

    :param pages: List of page names (nodes). Duplicates are ignored; first occurrence wins.
    :param links: List of directed edges [[source, target], ...].
    :param damping: Damping factor d in (0, 1). Default 0.85.
    :param max_iterations: Maximum power iteration steps. Default 100.
    :param tol: L1 convergence tolerance. Default 1e-6.
    :return: dict mapping page name -> PageRank score (float), summing to approx. 1.0.
    :raises ValueError: If damping is not strictly in (0, 1).
    """
    # --- Input validation ---
    import math
    if not isinstance(damping, (int, float)) or math.isnan(damping) or math.isinf(damping):
        raise ValueError(f"damping must be a finite number, got {damping!r}")
    if not (0.0 < damping < 1.0):
        raise ValueError(f"damping must be strictly between 0 and 1, got {damping}")

    # --- Build deterministic node list (preserving input order, deduplicating) ---
    seen = set()
    nodes = []
    for page in pages:
        if page not in seen:
            nodes.append(page)
            seen.add(page)

    N = len(nodes)
    if N == 0:
        return {}

    node_set = seen  # same set, used for O(1) membership checks

    # --- Build valid, deduplicated edge set ---
    # An edge is valid only if both endpoints exist in node_set.
    # Deduplication: treat the graph as a simple directed graph.
    valid_edges = set()
    for edge in links:
        source, target = edge[0], edge[1]
        if source in node_set and target in node_set:
            valid_edges.add((source, target))

    # Sort edges for deterministic iteration order
    valid_edges = sorted(valid_edges)

    # --- Compute outgoing link count for each node ---
    outgoing_links = {node: 0 for node in nodes}
    for source, target in valid_edges:
        outgoing_links[source] += 1

    # --- Identify dangling nodes (no valid outgoing edges) ---
    dangling_nodes = [node for node in nodes if outgoing_links[node] == 0]

    # --- Build incoming adjacency: for each node, list its (source, 1/out_degree) contributors ---
    # Precompute to avoid re-scanning all edges every iteration.
    incoming = {node: [] for node in nodes}
    for source, target in valid_edges:
        incoming[target].append((source, outgoing_links[source]))

    # --- Initialize rank vector uniformly ---
    rank = {node: 1.0 / N for node in nodes}

    # --- Power iteration ---
    for _iteration in range(max_iterations):
        # Total rank held by dangling nodes — redistributed uniformly to all nodes
        dangling_rank = sum(rank[node] for node in dangling_nodes)

        new_rank = {}
        for node in nodes:
            # Teleportation base + dangling redistribution
            base = (1.0 - damping) / N + damping * (dangling_rank / N)
            # Valid incoming contributions
            incoming_sum = sum(rank[src] / out_deg for src, out_deg in incoming[node])
            new_rank[node] = base + damping * incoming_sum

        # --- L1 convergence check ---
        error = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank

        if error < tol:
            break

    return rank
