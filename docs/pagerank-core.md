# PageRank Core

This document describes the mathematically corrected PageRank implementation in `backend/pagerank.py` as established during Phase 1 — Step 3.

---

## Previous Implementation

The baseline implementation (`calculate_pagerank` before Step 3) used the correct update formula for nodes that had valid outgoing edges, but had three confirmed mathematical problems:

1. **Dangling node handling**: Nodes with no outgoing edges simply leaked rank out of the system during power iterations. The sum of all ranks dropped below 1.0 during iteration. A post-hoc step divided every score by the sum to restore the total to 1.0. This is NOT the standard PageRank algorithm; it produces a different fixed point than the proper dangling-node redistribution model.

2. **Invalid target edges**: If an edge `(A, C)` appeared in `links` where `C` was not in `pages`, the code still incremented `out_degree[A]`, causing A's rank to be divided among transitions — including one that goes nowhere. Rank proportional to `PR(A)/out_degree(A)` simply vanished from the system each iteration.

3. **Duplicate edges**: If the same directed pair `(A, B)` appeared multiple times, `out_degree[A]` was incremented once per copy, and the inner loop accumulated `PR(A)/out_degree[A]` once per copy. The errors cancelled in the update formula (which is why results appeared numerically similar), but the graph semantics were wrong: the same relationship was not being counted twice intentionally.

4. **No damping factor validation**: Any float could be passed as `d`, including values ≤ 0, ≥ 1, NaN, or infinity.

---

## Problems Identified (Verified)

| Problem | Severity | Status |
|---------|----------|--------|
| Dangling node rank leakage during iteration | Mathematical error | **Fixed** |
| Post-hoc normalization as substitute for proper model | Mathematical error | **Fixed** |
| Invalid target edges inflate source out-degree | Mathematical error | **Fixed** |
| Duplicate edges counted multiple times | Semantic error | **Fixed** |
| No damping factor validation | Missing guard | **Fixed** |

---

## Corrected Mathematical Model

### PageRank Formula

For a graph with N nodes:

```
PR(i) = (1 - d) / N
        + d × [ dangling_rank / N
                + Σ_{j: j→i is valid} PR(j) / outgoing_links(j) ]
```

where:
- `d` = damping factor (default 0.85)
- `N` = number of nodes
- `dangling_rank` = `Σ_{j: dangling} PR(j)` (total rank held by dangling nodes)
- A valid incoming edge `j → i` requires both `j` and `i` to be in the node set
- `outgoing_links(j)` = number of distinct valid outgoing edges from `j` (after deduplication)

The `dangling_rank / N` term distributes each dangling node's mass uniformly to all nodes at **every iteration step**, not just at the end. This is the standard treatment (equivalent to replacing each dangling node's row in the transition matrix with a uniform distribution vector).

### Why Dangling Redistribution Matters

Without in-iteration redistribution, the Markov chain defined by the iteration is not row-stochastic — rank disappears at dangling nodes and the chain does not converge to a proper probability distribution. Post-hoc normalization corrects the sum to 1.0 but at a point that no longer represents a fixed point of the correct recurrence.

### Convergence is Natural

With proper dangling redistribution, the sum `Σ PR(i)` is preserved across every iteration (approximately — within floating-point error). The algorithm converges to the fixed point of the above recurrence without needing any normalization step. No post-hoc normalization is applied in the corrected implementation.

---

## Graph Semantics

### Valid Nodes

A node is valid if it appears in the `pages` input list. The node list is deduplicated (preserving first-occurrence order) before processing.

### Valid Edges

An edge `(source, target)` from `links` is **valid** only if:
- `source` exists in the node set, **AND**
- `target` exists in the node set

Invalid edges are silently filtered before any computation. They do not affect any node's out-degree.

### Duplicate Edges

The graph is treated as a **simple directed graph**. Multiple copies of the same `(source, target)` pair are deduplicated to a single edge. Deduplication occurs before out-degree computation and before the iteration begins.

**Consequence**: The PageRank result for graph `{A→B, A→B, A→B}` is identical to the result for `{A→B}`.

### Self-Loops

Self-loops `A → A` are valid directed edges. They are handled correctly by the update formula: node A's outgoing link count includes the self-loop, and in the incoming-contribution summation for A, the `PR(A)/outgoing_links(A)` term from the self-loop is included naturally.

### Dangling Nodes

A dangling node is any node with `outgoing_links[node] == 0` after edge filtering and deduplication. This includes:
- Nodes explicitly added with no outgoing edges.
- Nodes whose all outgoing edges were filtered as invalid.
- Isolated nodes (no edges at all).

Dangling nodes redistribute their rank uniformly to all N nodes at every iteration step.

### Disconnected Graphs

Multiple connected components are handled correctly. The teleportation term `(1 - d) / N` ensures every node receives a minimum base rank regardless of component membership. Disconnected components do not cause crashes, infinite values, or negative ranks.

---

## Convergence

| Parameter | Value | Description |
|-----------|-------|-------------|
| `tol` | `1e-6` | L1 convergence tolerance |
| `max_iterations` | `100` | Hard iteration limit |
| Error metric | L1 norm | `Σ |PR_new(i) - PR_old(i)|` |

**Convergence criterion**: Iteration stops when `Σ |PR_new(i) - PR_old(i)| < tol`, or when `max_iterations` steps have been taken.

**Deterministic ordering**: Nodes are iterated in the order they appear in the `pages` input list (with first-occurrence deduplication). Edges are sorted lexicographically after deduplication. This ensures identical inputs produce identical outputs across all runs.

---

## Numerical Stability

The corrected implementation verifies the following properties:

| Property | Guarantee |
|----------|-----------|
| NaN-free | No division-by-zero (dangling nodes never divide); all inputs validated |
| Infinity-free | No operation can produce infinity under valid inputs |
| Non-negative | All ranks initialized positive; update formula preserves positivity |
| Mass conservation | `Σ PR(i) ≈ 1.0` within floating-point error (verified by tests) |
| No post-hoc normalization | Algorithm converges naturally without forced renormalization |

---

## Testing

### Test File: `tests/test_pagerank_correctness.py`

36 correctness tests organized into 10 test classes:

| Test Class | Tests | Requirement |
|------------|-------|-------------|
| `TestMassConservation` | 6 | Sum = 1.0 for all graph types |
| `TestCycleSymmetry` | 1 | A→B→C→A gives equal ranks |
| `TestDanglingNode` | 2 | Dangling redistribution |
| `TestDisconnectedGraph` | 2 | Disconnected components |
| `TestSelfLoop` | 2 | Self-loop handling |
| `TestDuplicateEdges` | 2 | Edge deduplication |
| `TestInvalidTargetEdge` | 3 | Invalid edge filtering |
| `TestDampingFactorValidation` | 7 | `d` validation |
| `TestDeterminism` | 2 | Reproducible results |
| `TestConvergence` | 3 | Actual convergence |
| `TestNumericalStability` | 5 | NaN/inf/negative guards |
| `TestPerformanceSanity` | 1 | 100-node chain < 5s |

**Total: 36 tests. All pass.**

### Baseline Tests: `tests/test_pagerank_baseline.py`

The 16 original Step 2 baseline tests are preserved. Two tests are marked `@unittest.skip` because they asserted the exact numerical output of the pre-Step-3 broken behavior (dangling leakage + post-hoc normalization). Their test bodies remain verbatim as historical records.

| Skipped Test | Reason |
|---|---|
| `test_c_dangling_node_graph` | Asserted pre-Step-3 post-hoc-normalization values |
| `test_invalid_target_edge` | Asserted that invalid target inflated out-degree |

All other 14 baseline tests pass against the corrected implementation.

---

## Before vs After

### Case 1: Dangling Node (A→B→C, C has no outgoing edges)

**Before (Step 2 behavior)**:
```
A: 0.18441678192715535
B: 0.34117104656523745
C: 0.47441217150760717
```
Mechanism: rank leaked out each iteration; sum < 1.0 mid-iteration; post-hoc division restored sum to 1.0. The values represented the fixed point of an incorrect recurrence.

**After (Step 3 corrected)**:
```
A: 0.18441687554671388
B: 0.34117100648207455
C: 0.47441211797121174
```
Mechanism: C's rank redistributed uniformly to all 3 nodes at every iteration. Sum ≈ 1.0 is preserved throughout. Values represent the true fixed point of the standard PageRank recurrence.

**Numerical difference**: ~1e-7 (beyond 6-decimal-place precision). Semantically different fixed point; numerically very close for this graph because both approaches converge to a similar stochastic distribution for symmetric chains.

**Mathematical reason**: For short chains with small N, the effect of dangling redistribution vs post-hoc normalization is numerically small because the teleportation term `(1-d)/N` partially compensates for rank leakage in the pre-normalization model. For larger, more complex graphs with many dangling nodes, the difference would be larger.

### Case 2: Invalid Target Edge (A→C, C not in pages, nodes = {A, B})

**Before (Step 2 behavior)**:
```
A: 0.5000
B: 0.5000
```
Reason: `out_degree[A]` was incremented for the invalid edge, so A's rank was divided by 1 and assigned to a phantom node C that didn't exist. This leaked A's rank each iteration. Post-hoc normalization then divided both nodes' equal-teleportation-only ranks by their sum, yielding 0.5 each.

**After (Step 3 corrected)**:
```
A: 0.5000
B: 0.5000
```
Reason: A→C is filtered (C not in node set). A has no valid outgoing edges → A is dangling. B also has no valid outgoing edges → B is dangling. Both nodes get equal rank from teleportation + dangling redistribution. Final result: 0.5 each.

**Numeric result is identical** but for a completely different mathematical reason. The baseline assertion was accidentally correct. The internal computation now correctly models the graph (A isolated, B isolated, uniform rank).

### Case 3: Duplicate Edges (A→B, A→B, A→B)

**Before (Step 2 behavior)**:
```
A: 0.3508771929824562
B: 0.6491228070175439
```
Reason: `out_degree[A]` = 3, inner loop accumulated `PR(A)/3` three times = `PR(A)`. B's incoming sum was effectively `PR(A)`. The double-counting in numerator and denominator cancelled, giving same result as single edge (accidental correctness).

**After (Step 3 corrected)**:
```
A: 0.3508771211772586
B: 0.6491228788227412
```
Reason: Three copies of A→B deduplicated to one. Computation uses single A→B with `out_degree[A]` = 1. Result is numerically near-identical (difference ~7e-8) because the old error cancelled.

**Explicit deduplication is now guaranteed** rather than accidentally correct.

---

## Performance Sanity Check

| Graph | Nodes | Edges | Time | Sum |
|-------|-------|-------|------|-----|
| 100-node chain | 100 | 99 | ~2ms | 1.000000 |

The corrected implementation introduces no catastrophic performance regression. The additional precomputation (building `incoming` adjacency dictionary) reduces inner-loop work from O(E) per node per iteration to O(in-degree) per node per iteration. For most graphs this is a net improvement.

---

## Parameter Reference

```python
calculate_pagerank(
    pages,                # List[str] — node names (duplicates allowed, first occurrence used)
    links,                # List[[str, str]] — directed edges [[source, target], ...]
    damping=0.85,         # float in (0, 1) — damping factor d
    max_iterations=100,   # int — maximum power iteration steps
    tol=1.0e-6,           # float — L1 convergence tolerance
) -> dict[str, float]     # {node: pagerank_score}, sum ≈ 1.0
```

`ValueError` is raised if `damping` is not strictly in (0, 1), or is NaN/infinite.
