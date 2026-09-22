# Ranking Comparison Layer Contract & Metric Definitions

## Overview

The **Ranking Comparison Layer** (`backend/ranking_comparator.py`) provides an independent, mathematically rigorous infrastructure for comparing two ranking vectors over the same directed web graph.

It accepts deterministic node-score mappings and calculates objective mathematical comparison metrics without altering the input ranking vectors or making evaluative claims (such as "Algorithm X is better").

---

## 1. Ranking Vector Contract & Validation

Before comparing any two ranking vectors, both vectors are independently validated by `validate_ranking_vector`.

### Validation Rules:
1. **Structure**: Input must be a dictionary (`dict[str, float]`).
2. **Non-Empty**: The ranking dictionary must contain at least one node. An empty `{}` ranking has no comparable nodes and is rejected with `ValueError`.
3. **Node Identifiers**: Keys must be non-empty strings (`str`).
4. **Numeric Scores**: Values must be finite real numbers (`int` or `float`). Boolean values (`True`/`False`), strings, `None`, `NaN`, and `infinity` (`inf`/`-inf`) are rejected with `ValueError`.
5. **Node Coverage**: Both ranking vectors must refer to the exact same node set ($V_A = V_B$). Mismatched sets raise a `ValueError` with detailed diff diagnostics.

---

## 2. Common Node Alignment

To prevent dependence on dictionary insertion order, ranking vectors are aligned onto a common node order:

$$\text{Nodes} = \text{sorted}(V_A)$$

Both vectors are converted to aligned numerical arrays $A = (A_1, A_2, \dots, A_N)$ and $B = (B_1, B_2, \dots, B_N)$ where element $i$ corresponds to the $i$-th node in lexicographical order.

---

## 3. Metric Definitions

### L1 Distance (Manhattan Distance)
Calculates the absolute magnitude of score differences:

$$L_1(A, B) = \sum_{i=1}^{N} |A_i - B_i|$$

* **Domain**: $[0, \infty)$
* **Semantics**: $0.0$ indicates identical scores for all nodes.

---

### L2 Distance (Euclidean Distance)
Calculates the root sum-of-squares of score differences:

$$L_2(A, B) = \sqrt{\sum_{i=1}^{N} (A_i - B_i)^2}$$

* **Domain**: $[0, \infty)$
* **Semantics**: Geometric distance between the two ranking score vectors in $\mathbb{R}^N$.

---

### Cosine Similarity
Measures the directional alignment of score vectors:

$$\text{Cosine}(A, B) = \frac{A \cdot B}{\|A\|_2 \|B\|_2} = \frac{\sum_{i=1}^N A_i B_i}{\sqrt{\sum_{i=1}^N A_i^2} \sqrt{\sum_{i=1}^N B_i^2}}$$

* **Zero-Vector Policy**: If both $A$ and $B$ have zero norm ($\|A\| = \|B\| = 0$), Cosine Similarity returns `1.0`. If only one vector has zero norm, it returns `0.0`. NaN values or division-by-zero are strictly avoided.
* **Domain**: $[-1.0, 1.0]$

---

### Spearman Rank Correlation ($\rho$)
Measures the monotonic relationship between the ranks induced by scores $A$ and $B$.

$$\rho(A, B) = \frac{\sum_{i=1}^N (R_A(i) - \bar{R}_A)(R_B(i) - \bar{R}_B)}{\sqrt{\sum_{i=1}^N (R_A(i) - \bar{R}_A)^2 \sum_{i=1}^N (R_B(i) - \bar{R}_B)^2}}$$

* **Tie-Handling**: Fractional (average) ranks are assigned to tied values. For example, if two nodes tie for 2nd and 3rd rank, both receive rank $2.5$.
* **Domain**: $[-1.0, 1.0]$

---

### Kendall Tau-b Rank Correlation ($\tau_b$)
Measures the proportion of concordant versus discordant pairs, explicitly accounting for score ties.

$$\tau_b = \frac{P - Q}{\sqrt{(P + Q + T_A)(P + Q + T_B)}}$$

where:
* $P$: Number of concordant pairs ($\text{sign}(A_i - A_j) == \text{sign}(B_i - B_j) \ne 0$)
* $Q$: Number of discordant pairs ($\text{sign}(A_i - A_j) == -\text{sign}(B_i - B_j) \ne 0$)
* $T_A$: Number of pairs tied only in ranking A
* $T_B$: Number of pairs tied only in ranking B
* **Domain**: $[-1.0, 1.0]$

---

### Top-K Overlap
Measures the ratio of common nodes within the top $k$ highest-ranked nodes:

$$\text{TopKOverlap}(k) = \frac{|\text{TopK}(A) \cap \text{TopK}(B)|}{k}$$

* **Deterministic Tie-Breaking**: When score ties occur, nodes are sorted by score descending, then by node ID ascending (lexicographical order).
* **Domain**: $[0.0, 1.0]$ for $1 \le k \le N$.

#### Top-K Input Validation Contract

When the caller explicitly supplies a `top_k` list, the following rules are strictly enforced (violations raise `ValueError`):

| Rule | Accepted | Rejected | Reason |
| :--- | :--- | :--- | :--- |
| **Type** | `list` | non-list | `top_k` must be a list |
| **Non-empty** | `[1]`, `[1, 3]` | `[]` | An explicitly empty list has no comparison purpose; omit `top_k` to use defaults |
| **Element type** | `int` | `float` (`1.5`), `str` (`"3"`), `bool` (`True`), `None` | Each element must be a plain integer |
| **Range** | `1 ≤ k ≤ N` | `k = 0`, `k < 0`, `k > N` | k must index into the node list |
| **No duplicates** | `[1, 2, 3]` | `[1, 1, 3]` | Each requested k must be distinct |

**Default behaviour (when `top_k` is omitted / `None`)**: The default set `[1, 3, 5, 10]` is used, bounded by N. No validation error is raised because the default set is always constructed to be valid.

### Rank Displacement Statistics
Measures absolute changes in node rank positions (1-indexed, 1 = highest score).

* **Per-node Displacement**: $d_i = |\text{Rank}_A(i) - \text{Rank}_B(i)|$
* **Max Displacement**: $\max_{i} d_i$
* **Mean Displacement**: $\frac{1}{N} \sum_{i=1}^N d_i$

---

## 4. API Contract (`POST /compare`)

### Endpoint: `POST /compare`

**Request Body**:
```json
{
  "ranking_a": {"A": 0.4, "B": 0.3, "C": 0.3},
  "ranking_b": {"A": 0.5, "B": 0.3, "C": 0.2},
  "top_k": [1, 2, 3]
}
```

**Success Response (HTTP 200)**:
```json
{
  "node_count": 3,
  "l1_distance": 0.2,
  "l2_distance": 0.14142135623730953,
  "cosine_similarity": 0.9859587355823122,
  "spearman_correlation": 0.8660254037844387,
  "kendall_tau": 0.8164965809277261,
  "top_k_overlap": {
    "1": 1.0,
    "2": 1.0,
    "3": 1.0
  },
  "max_rank_displacement": 1,
  "mean_rank_displacement": 0.6666666666666666,
  "rank_displacements": {
    "A": 0,
    "B": 1,
    "C": 1
  }
}
```

**Error Response (HTTP 400)**:
```json
{
  "error": "Rankings must refer to the exact same node set. Nodes in ranking_a but missing in ranking_b: ['D']"
}
```

#### API Error Cases That Return HTTP 400

| Input | Error Reason |
| :--- | :--- |
| `ranking_a: {}` | Empty ranking vector — at least one node required |
| `ranking_b: {}` | Empty ranking vector — at least one node required |
| `ranking_a` and `ranking_b` have different node sets | Node set mismatch |
| Score is `NaN`, `inf`, boolean, string, or `None` | Invalid score type or value |
| `top_k: []` | Empty `top_k` list — omit `top_k` to use defaults |
| `top_k: [0]` | `k=0` is out of range; minimum is 1 |
| `top_k: [-1]` | Negative k is out of range |
| `top_k: [N+1]` | k exceeds node count N |
| `top_k: ["1"]` | String element — must be a plain integer |
| `top_k: [1.5]` | Float element — must be a plain integer |
| `top_k: [True]` | Boolean element — must be a plain integer |
| `top_k: [1, 1, 3]` | Duplicate k value — each k must be distinct |
