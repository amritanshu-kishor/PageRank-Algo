# Graph Data Contract & Edge-Case Handling

This document specifies the graph input contracts, validation layer, normalization rules, and behavioral guarantees for the PageRank system as verified in Phase 1 — Step 4.

---

## 1. Architectural Boundary

```text
Raw API Input (JSON Payload)
           │
           ▼
backend/graph_validator.py: validate_graph() & validate_pagerank_params()
           │
           ├─ Failure ──► Raises ValueError (HTTP 400 with descriptive reason)
           │
           ▼ (Normalized Graph Data: pages: list[str], links: list[list[str]])
backend/pagerank.py: calculate_pagerank()
           │
           ▼
Deterministic, Mass-Conserving PageRank Scores (dict[str, float])
```

---

## 2. Graph Input Schema & Rules

### 2.1 Node Identifier Specification (`pages`)
- **Type**: Must be a `list` of Python `str` (or JSON strings).
- **Non-Empty**: Each string must have non-zero length after stripping whitespace. Empty strings (`""`) and whitespace-only strings (`"   "`) are rejected with `ValueError`.
- **Allowed Formats**:
  - Alphanumeric labels (e.g., `"A"`, `"Node_1"`)
  - Human-readable titles with internal spaces (e.g., `"Home Page"`, `"About Us"`)
  - Full URLs (e.g., `"https://example.com/page"`)
  - Unicode strings (e.g., `"ページA"`, `"α_node"`)
- **Invalid Types**: `None`, `int`, `float`, `bool`, `dict`, `list` within `pages` raise `ValueError` (HTTP 400).
- **Duplicate Nodes**: If duplicate node identifiers appear in `pages` (e.g., `["A", "B", "A"]`), the first occurrence is preserved, and subsequent duplicates are deduplicated deterministically.

### 2.2 Directed Edge Specification (`links`)
- **Type**: Must be a `list` of 2-element sequences `[source, target]`.
- **Endpoints**: Both `source` and `target` must be non-empty strings.
- **Malformed Structures**:
  - Non-list links object (e.g. string or dict) raises `ValueError`.
  - Elements that are bare strings (e.g., `"AB"`) rather than list/tuple pairs raise `ValueError`.
  - Sequences with fewer than 2 elements (e.g. `["A"]`) or non-string endpoints raise `ValueError`.
- **Unknown Node References**: Directed edges referencing nodes that do not exist in `pages` (e.g., `["A", "GhostNode"]`) are safely and cleanly filtered out without error.

### 2.3 Numeric Parameter Specification
- **`damping`**: Float strictly in the open interval $(0, 1)$. Must be finite (no `NaN`, no `inf`). Default: `0.85`.
- **`tol`**: Positive finite float $> 0$. Default: `1e-6`.
- **`max_iterations`**: Integer $\ge 1$ (boolean types rejected). Default: `100`.

---

## 3. Topological Edge Cases & Behavioral Guarantees

| Graph Topology | Input Example | Expected Behavior | Mass Conservation |
| :--- | :--- | :--- | :--- |
| **Empty Graph** | `pages = []`, `links = []` | Returns `{}` | $\sum = 0.0$ (trivial) |
| **Single Isolated Node** | `pages = ["A"]`, `links = []` | Returns `{"A": 1.0}` | $\sum = 1.0$ |
| **Single Node Self-Loop** | `pages = ["A"]`, `links = [["A", "A"]]` | Returns `{"A": 1.0}` | $\sum = 1.0$ |
| **All Disconnected Nodes** | `pages = ["A", "B", "C"]`, `links = []` | Returns uniform rank: `{"A": 1/3, "B": 1/3, "C": 1/3}` | $\sum = 1.0$ |
| **Complete Directed Graph** | All pairs $u \to v$ connected | Returns uniform rank $1/N$ for all $N$ nodes | $\sum = 1.0$ |
| **Star Graph (Inward)** | Leaves point to center $C$ | Center rank $> $ leaf ranks; rank conserved | $\sum = 1.0$ |
| **Star Graph (Outward)** | Center points to all leaves | All leaves receive symmetric rank; rank conserved | $\sum = 1.0$ |
| **Linear Dangling Chain** | $A \to B \to C \to D$ ($D$ dangling) | Mass conserved via uniform redistribution; $PR(D) > PR(A)$ | $\sum = 1.0$ |
| **Disconnected Subgraphs** | Distinct symmetric components | Each symmetric component receives equal share | $\sum = 1.0$ |
| **Duplicate Edges** | Multiple copies of $[A, B]$ | Deduplicated to simple directed graph; identical result to single edge | $\sum = 1.0$ |
| **Dangling Nodes** | Nodes with 0 outgoing edges | Dangling rank redistributed uniformly across all $N$ nodes each iteration | $\sum = 1.0$ |

---

## 4. API Error Response Contract

When malformed input is submitted to `POST /calculate`:
- **Status Code**: `400 Bad Request`
- **Response Format**: `{"error": "<Descriptive error message>"}`
- **Examples**:
  - `{"pages": ["A", null], "links": []}` $\to$ `{"error": "'pages[1]' must be a non-empty string, got NoneType: None."}`
  - `{"pages": ["A", "B"], "links": [["A"]]}` $\to$ `{"error": "'links[0]' must have exactly 2 elements [source, target], got 1 element(s): ['A']."}`
  - `{"pages": ["A"], "links": [], "damping": 1.5}` $\to$ `{"error": "'damping' must be strictly between 0 and 1, got 1.5."}`
