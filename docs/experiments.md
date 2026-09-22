# Experiment & Measurement Layer Specification

This document defines the architecture, design contracts, dataset catalog, measurement procedures, and output schemas for Step 9: Experiment & Measurement Layer (`experiments/`).

---

## Architecture Overview

The Experiment Layer provides a reproducible, isolated measurement framework to evaluate PageRank behavior on directed graphs.

```text
+-----------------------+     +------------------------+
|  experiments/datasets | --> | Step 4 Graph Validator |
+-----------------------+     +------------------------+
            |                              |
            v                              v
+-----------------------+     +------------------------+
|  experiments/config   | --> | backend/pagerank.py    |
+-----------------------+     | (calculate_pagerank_   |
            |                 |  detailed)             |
            v                 +------------------------+
+-----------------------+                  |
|  experiments/runner   | <----------------+
+-----------------------+
     |             |
     v             v
+----------+ +-------------------------------+
| Json     | | Step 8 ranking_comparator.py  |
| Export   | | (Rank Stability Analysis)    |
+----------+ +-------------------------------+
```

### Key Modules

1. **`experiments/datasets.py`**: Statically defined controlled datasets and deterministic scalable graph generators. All datasets are strictly validated against Step 4 graph contract rules before use.
2. **`experiments/config.py`**: Configuration validation and catalog resolution for experiment configurations and parameter sweeps.
3. **`experiments/runner.py`**: Core execution engine for single runs, repeated stability runs, parameter sweeps, and machine-readable JSON exports.
4. **`backend/pagerank.py` (`calculate_pagerank_detailed`)**: Instrumentation layer returning rank vectors alongside actual iteration counts, convergence booleans, and final L1 errors.

---

## Static Controlled Datasets Catalog

All static datasets are statically defined tuples of `(pages, links)` independent of any external network state.

| Dataset ID | Description | Nodes | Edges | Graph Topology Features |
| :--- | :--- | :--- | :--- | :--- |
| `chain-4` | Linear chain (A→B→C→D) | 4 | 3 | Single component, D is dangling |
| `cycle-3` | Directed cycle (A→B→C→A) | 3 | 3 | Strongly connected cycle, symmetric rank distribution |
| `dangling-3` | Dangling path (A→B→C) | 3 | 2 | C has no outgoing edges; tests rank conservation |
| `disconnected-5` | Disconnected components + isolated node | 5 | 2 | Component 1 (A→B), Component 2 (C→D), Isolated (E) |
| `hub-6` | Inward star (5 nodes point to A) | 6 | 5 | A accumulates rank mass; B-F and A are dangling |
| `star-out-5` | Outward star (A points to B,C,D,E) | 5 | 4 | A distributes rank mass to leaves; leaves dangling |
| `mixed-7` | Mixed complex topology | 7 | 5 | Cycle (A→B→C→A), dangling D, isolated E, second component (F→G) |

### Deterministic Scalable Generators

- `generate_chain(n)`: Creates chain $N_1 \to N_2 \to \dots \to N_n$ for $n \ge 1$.
- `generate_cycle(n)`: Creates directed cycle $N_1 \to N_2 \to \dots \to N_n \to N_1$ for $n \ge 2$.
- `generate_star(n)`: Creates outward star $C_{001} \to L_{001}, \dots, L_{n-1}$ for $n \ge 2$.

---

## Detailed Instrumentation API

`calculate_pagerank_detailed(pages, links, damping=0.85, max_iterations=100, tol=1.0e-6)`

Returns dictionary:
```json
{
  "ranking": { "A": 0.333333, "B": 0.333333, "C": 0.333333 },
  "iterations": 12,
  "converged": true,
  "final_error": 8.4e-7
}
```

---

## Parameter Sweeps & Measurements

1. **Single Run** (`run_experiment`): Computes ranking, runtime, iterations, convergence, final error, and structural graph analysis.
2. **Runtime Stability** (`run_repeated_experiment`): Executes experiment $N$ times, computing runtime mean, min, max, and standard deviation.
3. **Damping Sweep** (`run_damping_sweep`): Sweeps damping factors $d \in (0, 1)$ and evaluates rank stability against baseline $d=0.85$ using Step 8 metrics (L1, L2, Cosine, Spearman, Kendall, Top-K overlap, displacements).
4. **Tolerance Sweep** (`run_tolerance_sweep`): Sweeps L1 error threshold $tol > 0$ to observe iteration count and rank stability.
5. **Iteration Cap Sweep** (`run_max_iterations_sweep`): Sweeps max iterations cap to observe non-convergence behavior when capped below convergence limit.
6. **Scalability Sweep** (`run_scalability_sweep`): Evaluates execution time and iterations as a function of node scale $N$.

---

## Output Schema & Serialization

`save_experiment_results(results, output_path)` outputs formatted JSON preserving configuration metadata, execution metrics, and structural graph properties.
