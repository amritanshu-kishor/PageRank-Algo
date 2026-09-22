# Graph Structural Analysis Layer Documentation

This document specifies the deterministic Graph Analysis Layer established in Phase 1 — Step 5.

---

## 1. Overview & Architectural Role

The Graph Analysis Layer (`backend/graph_analyzer.py`) computes structural graph properties prior to or independently of PageRank computation. It operates strictly on the validated/sanitized graph representation produced by the Step 4 validation boundary (`graph_validator.py`).

```text
Raw Input (JSON Payload)
          │
          ▼
backend/graph_validator.py: validate_graph()
          │
          ▼ (Validated Graph Representation)
backend/graph_analyzer.py: analyze_graph()
          │
          ▼
Structural Analysis Summary (dict / JSON)
```

---

## 2. Structural Properties & Definitions

### 2.1 Node Count (`node_count`)
- **Type**: `int`
- **Definition**: Number of unique, validated node identifiers in the graph $N$. Duplicate nodes in the input `pages` array are deduplicated deterministically.

### 2.2 Edge Count (`edge_count`)
- **Type**: `int`
- **Definition**: Number of unique valid directed edges $E$. Duplicate edges and edges referencing unknown nodes (nodes not present in `pages`) are excluded as per the Step 4 graph contract.

### 2.3 Graph Density (`density`)
- **Type**: `float`
- **Definition**:
  - For directed graphs with $N \ge 2$:
    $$\text{density} = \frac{E}{N \times (N - 1)}$$
  - For $N < 2$: defined deterministically as `0.0`.
- **Rationals**: Avoids division-by-zero for $N=0$ or $N=1$.

### 2.4 In-Degree Mapping (`in_degree`)
- **Type**: `dict[str, int]`
- **Definition**: Number of incoming directed edges for each node in the graph. Every node appears in the dictionary, including nodes with `in_degree = 0`. Self-loops (`A -> A`) add $+1$ to `in_degree`.

### 2.5 Out-Degree Mapping (`out_degree`)
- **Type**: `dict[str, int]`
- **Definition**: Number of outgoing directed edges for each node in the graph. Every node appears in the dictionary, including nodes with `out_degree = 0`. Self-loops (`A -> A`) add $+1$ to `out_degree`.

### 2.6 Dangling Node Count (`dangling_node_count`)
- **Type**: `int`
- **Definition**: Total number of nodes with `out_degree == 0`. These nodes lack valid outgoing edges and redistribute their rank uniformly during PageRank power iteration.

### 2.7 Isolated Node Count (`isolated_node_count`)
- **Type**: `int`
- **Definition**: Total number of nodes with `in_degree == 0` AND `out_degree == 0`. Isolated nodes have no incoming or outgoing connections.

### 2.8 Weakly Connected Components (`weakly_connected_components`)
- **Type**: `list[list[str]]`
- **Algorithm**: Breadth-First Search / Depth-First Search treating all directed edges as undirected links.
- **Ordering**: Nodes within each component are sorted lexicographically; components are sorted lexicographically by their first node. Every node belongs to exactly one component.

### 2.9 Strongly Connected Components (`strongly_connected_components`)
- **Type**: `list[list[str]]`
- **Algorithm**: Tarjan's Strongly Connected Components algorithm (or Kosaraju's). Nodes $u$ and $v$ belong to the same SCC if and only if there exists a directed path from $u$ to $v$ AND a directed path from $v$ to $u$.
- **Ordering**: Nodes within each component are sorted lexicographically; components are sorted lexicographically by their first node.

---

## 3. Structural Summary Schema

Example output of `analyze_graph()` or `POST /analyze`:

```json
{
  "node_count": 3,
  "edge_count": 2,
  "density": 0.3333333333333333,
  "in_degree": {
    "A": 0,
    "B": 1,
    "C": 1
  },
  "out_degree": {
    "A": 1,
    "B": 1,
    "C": 0
  },
  "dangling_node_count": 1,
  "isolated_node_count": 0,
  "weakly_connected_components": [
    ["A", "B", "C"]
  ],
  "strongly_connected_components": [
    ["A"],
    ["B"],
    ["C"]
  ]
}
```
