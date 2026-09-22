"""
Graph Structural Analysis Layer for PageRank application.

Provides deterministic structural graph analysis on top of the validated
graph representation established in Step 4 (graph_validator.py).

Flow:
    RAW INPUT -> validate_graph() -> VALID GRAPH -> analyze_graph() -> STRUCTURAL SUMMARY

Structural Graph Properties computed:
- node_count (int)
- edge_count (int)
- density (float): E / (N * (N - 1)) for N >= 2, else 0.0
- in_degree (dict[str, int])
- out_degree (dict[str, int])
- dangling_node_count (int): nodes with out_degree == 0
- isolated_node_count (int): nodes with in_degree == 0 AND out_degree == 0
- weakly_connected_components (list[list[str]]): undirected connectivity
- strongly_connected_components (list[list[str]]): directed mutual reachability
"""

from graph_validator import validate_graph


def analyze_graph(pages, links, validate=True):
    """
    Perform deterministic structural analysis on a directed graph.

    :param pages: List of node identifiers.
    :param links: List of directed edges [[source, target], ...].
    :param validate: If True, validate input via validate_graph first. Default True.
    :return: dict containing complete structural analysis summary.
    :raises ValueError: If input is invalid and validate=True.
    """
    if validate:
        pages, links = validate_graph(pages, links)

    # --- Build deterministic node set & list ---
    seen = set()
    nodes = []
    for p in pages:
        if p not in seen:
            nodes.append(p)
            seen.add(p)

    node_set = seen
    N = len(nodes)

    # --- Build valid, deduplicated edge set ---
    valid_edges = set()
    for edge in links:
        source, target = edge[0], edge[1]
        if source in node_set and target in node_set:
            valid_edges.add((source, target))

    # Sort edges for deterministic processing
    sorted_edges = sorted(valid_edges)
    E = len(sorted_edges)

    # --- Density ---
    # Directed density = E / (N * (N - 1)) for N >= 2, else 0.0
    if N >= 2:
        density = E / (N * (N - 1.0))
    else:
        density = 0.0

    # --- Degrees ---
    in_degree = {node: 0 for node in nodes}
    out_degree = {node: 0 for node in nodes}

    for source, target in sorted_edges:
        out_degree[source] += 1
        in_degree[target] += 1

    # --- Counts ---
    dangling_node_count = sum(1 for node in nodes if out_degree[node] == 0)
    isolated_node_count = sum(
        1 for node in nodes if in_degree[node] == 0 and out_degree[node] == 0
    )

    # --- Adjacency Structures ---
    # Outgoing adjacency list
    adj_out = {node: [] for node in nodes}
    # Incoming adjacency list
    adj_in = {node: [] for node in nodes}
    # Undirected adjacency list
    adj_undirected = {node: set() for node in nodes}

    for source, target in sorted_edges:
        adj_out[source].append(target)
        adj_in[target].append(source)
        adj_undirected[source].add(target)
        adj_undirected[target].add(source)

    # --- Weakly Connected Components (WCC) ---
    visited_wcc = set()
    wcc_list = []

    # Sort nodes lexicographically for deterministic traversal
    sorted_nodes = sorted(nodes)

    for start_node in sorted_nodes:
        if start_node not in visited_wcc:
            component = []
            queue = [start_node]
            visited_wcc.add(start_node)
            idx = 0
            while idx < len(queue):
                curr = queue[idx]
                idx += 1
                component.append(curr)
                # Sort neighbors for deterministic traversal
                for neighbor in sorted(adj_undirected[curr]):
                    if neighbor not in visited_wcc:
                        visited_wcc.add(neighbor)
                        queue.append(neighbor)
            wcc_list.append(sorted(component))

    wcc_list.sort(key=lambda comp: comp[0] if comp else "")

    # --- Strongly Connected Components (SCC) using Tarjan's Algorithm ---
    index_counter = [0]
    stack = []
    in_stack = set()
    indices = {}
    lowlink = {}
    scc_list = []

    def strongconnect(node):
        indices[node] = index_counter[0]
        lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        in_stack.add(node)

        # Consider neighbors in deterministic (sorted) order
        for neighbor in sorted(adj_out[node]):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlink[node] = min(lowlink[node], lowlink[neighbor])
            elif neighbor in in_stack:
                lowlink[node] = min(lowlink[node], indices[neighbor])

        if lowlink[node] == indices[node]:
            component = []
            while True:
                w = stack.pop()
                in_stack.remove(w)
                component.append(w)
                if w == node:
                    break
            scc_list.append(sorted(component))

    for node in sorted_nodes:
        if node not in indices:
            strongconnect(node)

    scc_list.sort(key=lambda comp: comp[0] if comp else "")

    return {
        "node_count": N,
        "edge_count": E,
        "density": density,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "dangling_node_count": dangling_node_count,
        "isolated_node_count": isolated_node_count,
        "weakly_connected_components": wcc_list,
        "strongly_connected_components": scc_list,
    }
