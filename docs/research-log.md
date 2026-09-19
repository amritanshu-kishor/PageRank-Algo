# PageRank Research Project

## Phase 1 — Baseline & Research Foundation

### Step 1 — Baseline Repository Audit

#### Objective
The goal of Step 1 is to perform a comprehensive baseline audit of the existing `PageRank-Algo` codebase without altering any core logic, refactoring code, or implementing new features. This freezes and documents the ground truth of the current repository.

#### Repository Examined
- **Backend**: `backend/app.py`, `backend/pagerank.py`, `backend/crawler.py`, `backend/requirements.txt`, `backend/.env.example`
- **Frontend**: `frontend/index.html`, `frontend/script.js`, `frontend/style.css`
- **Scripts & Config**: `start_backend.ps1`, `start_frontend.ps1`, `README.md`, `.gitignore`

#### Architecture Discovered
- RESTful HTTP API built with Flask binding to port 5000 (`http://127.0.0.1:5000`).
- Frontend served via simple HTTP server on port 8000 (`http://localhost:8000`).
- Two primary API endpoints:
  - `POST /calculate`: Computes PageRank scores from input node list and directed edge list.
  - `POST /crawl`: Performs same-domain BFS crawl starting from target URL, then runs PageRank on discovered graph.
- Interactive visual rendering powered by Cytoscape.js with dynamic node resizing and score ranking leaderboard.

#### Algorithm Discovered
- Implemented in `backend/pagerank.py` (`calculate_pagerank`).
- Pure Python power iteration solver using formula:
  $$PR(A) = \frac{1-d}{N} + d \sum_{T_i \to A} \frac{PR(T_i)}{C(T_i)}$$
- Parameters: Damping factor $d = 0.85$, max iterations = 100, convergence tolerance $\text{tol} = 1.0\text{e-}6$.
- Key behavior: Rank leaks during power iterations for dangling nodes ($\text{out\_degree} = 0$) and is restored via post-hoc vector sum normalization ($\sum PR = 1.0$) at the end of execution.

#### Crawler Discovered
- Implemented in `backend/crawler.py` (`crawl_site`).
- Uses Requests and BeautifulSoup4 to execute same-domain BFS crawling.
- Enforces URL normalization (strips fragments, normalizes scheme/host, removes trailing slash).
- Filters cross-domain links and self-loops (`source != target`).
- Clamps max pages between 1 and 30 (default 12).

#### Frontend Workflow Discovered
- 1. Add page $\to$ 2. Add directed link $\to$ 3. Load sample graph $\to$ 4. Clear graph $\to$ 5. Relayout $\to$ 6. Fit canvas $\to$ 7. Calculate PageRank $\to$ 8. Experimental crawl $\to$ 9. Ranking leaderboard display $\to$ 10. Visual node sizing and top-authority highlighting.

#### Baseline Tests Performed
- **Test A (Simple Chain `A->B->C`)**: Scores `A: 0.1844, B: 0.3412, C: 0.4744`. Converged in 4 iterations. Total rank = 1.0000.
- **Test B (Cycle `A->B->C->A`)**: Scores `A: 0.3333, B: 0.3333, C: 0.3333`. Converged in 1 iteration. Total rank = 1.0000.
- **Test C (Dangling Node `A->B->C`)**: Scores `A: 0.1844, B: 0.3412, C: 0.4744`. Converged in 4 iterations. Total rank = 1.0000.
- **Test D (Disconnected Graph `A->B, C->D`)**: Scores `A: 0.1754, B: 0.3246, C: 0.1754, D: 0.3246`. Converged in 3 iterations. Total rank = 1.0000.
- **Test E (Self-Loop `A->A`)**: Scores `A: 1.0000`. Converged in 1 iteration. Total rank = 1.0000.
- **Test F (Duplicate Edge `A->B, A->B`)**: Scores `A: 0.3509, B: 0.6491`. Converged in 3 iterations. Total rank = 1.0000.
- **Crawler Test (`https://quotes.toscrape.com`)**: Discovered 3 pages and 5 links; PageRank computed successfully in 16 iterations.
- **API Endpoint Verification**: `/calculate` and `/crawl` verified with HTTP 200 responses.

#### Findings
1. Code structure is concise, functional, and decoupled into clear frontend and backend modules.
2. Dependencies are standard and installed in `venv`.
3. PageRank algorithm delivers correct relative rankings for standard graphs, though dangling rank is handled post-hoc rather than in-iteration.

#### Limitations
1. Algorithmic: In-iteration rank leakage for dangling nodes.
2. Backend: Lack of validation for invalid targets in `links`.
3. Crawler: Sequential single-threaded crawling; unresolvable domain returns HTTP 200 with 0 links rather than HTTP 400 error.
4. Frontend: Uses native `window.alert()` dialogs for error reporting.

#### Unresolved / Unverified Items
- **None**: All repository inspection, backend API verification, algorithmic test suite, web crawler execution, and interactive Chrome browser UI workflows (node creation, link connections, PageRank calculations, sample graphs, and web crawling) have been 100% verified.

---

## Step 1 Completion Status

### STEP 1 — COMPLETE

Date: 2026-09-19

Verified:
* Repository audited
* Architecture documented
* API behavior documented
* PageRank implementation documented
* Crawler implementation documented
* Frontend workflow documented
* Baseline tests executed
* Known limitations recorded
* Current baseline preserved

---

### Step 2 — Establish Reproducible Baseline Tests

#### Objective
The goal of Step 2 is to convert the baseline behavior verified during Step 1 into a repeatable, automated test suite in `tests/` that freezes the ground-truth application performance and algorithm scores without altering existing application code.

#### Test Architecture Established
- `tests/__init__.py`: Package initializer.
- `tests/fixtures/*.json`: JSON graph data fixtures for simple, cycle, dangling, disconnected, self-loop, duplicate edge, and empty graphs.
- `tests/test_pagerank_baseline.py`: Unit test suite verifying core algorithm behavior, dangling node rank handling, duplicate edge out-degree accumulation, invalid target link rank leakage, and empty graph entry conditions.
- `tests/test_api_baseline.py`: Integration test suite verifying Flask REST API endpoints (`/calculate` and `/crawl`), request payload validation, error responses, Flask JSON key ordering, and mocked crawling responses.

#### Key Baseline Discoveries Captured in Automated Tests
1. **Invalid Target Links (`test_invalid_target_edge`)**: If `links` contains an edge targeting a node not present in `pages` (`A -> C` where `C` is omitted), target `C` is ignored during rank accumulation while `out_degree[A]` is incremented to 1. Both `A` and `B` receive equal damping rank `0.075` and normalize to `0.5` each.
2. **Flask `jsonify` Key Ordering (`test_calculate_valid_graph`)**: Flask's `jsonify()` serializes dictionary keys in alphabetical order (`JSON_SORT_KEYS`), returning `"A"` before `"B"` in the JSON response payload even though `app.py` sorts items descending by float score value.
3. **Dangling Node In-Iteration Leakage (`test_c_dangling_node_graph`)**: Dangling nodes do not distribute rank during power iteration loops; sum of ranks is restored to 1.0 via post-hoc vector normalization after convergence.

#### Clean Environment Reproducibility Verification
- **Fresh Virtual Environment**: Created fresh `test_env` virtual environment without pre-installed packages.
- **Dependency Installation**: `pip install -r requirements.txt` executed successfully (installed Flask 3.0.2, Flask-Cors 4.0.0, networkx 3.2.1, numpy 1.26.4, beautifulsoup4 4.12.3, requests 2.31.0, pytest 9.1.1).
- **Run 1 (`python -m pytest -q`)**: 16/16 passed in 3.14s.
- **Run 2 (`python -m pytest -q`)**: 16/16 passed in 3.03s (100% deterministic reproducibility).
- **Unittest Entry Point (`python -m unittest discover tests`)**: 16/16 passed in 2.73s.
- **Pytest Entry Point (`pytest -v tests/`)**: 16/16 passed in 3.06s.

---

## STEP 2 — COMPLETE

Date: 2026-09-19

Verified:

* Reproducible test environment established
* Dependencies verified
* Baseline tests executed
* All baseline tests passed
* Tests repeated successfully
* Results reproducible
* Baseline implementation unchanged
* Documentation updated

---

### Step 3 — PageRank Core Hardening

#### Objective

Make the existing classical PageRank implementation mathematically correct, numerically stable, deterministic, and suitable as the trusted computational core for later research experiments. No new algorithms, no UI changes, no crawler changes.

#### Baseline Problems Confirmed

Three mathematical problems in the pre-Step-3 implementation were verified against actual code execution before any changes were made:

1. **Dangling node rank leakage** (`CONFIRMED`): Nodes with no outgoing edges did not redistribute their rank during power iteration. Rank leaked out each step; sum < 1.0 during iteration. Post-hoc division by the sum restored total to 1.0, but this is not the standard PageRank algorithm. It produces a different fixed point.

2. **Invalid target edges inflate out-degree** (`CONFIRMED`): An edge `(A, C)` where `C ∉ pages` incremented `out_degree[A]`, causing `PR(A)/out_degree(A)` to flow to a non-existent node. Rank disappeared from the system each iteration.

3. **Duplicate edges not deduplicated** (`CONFIRMED`): Multiple copies of `(A, B)` in `links` incremented `out_degree[A]` per copy and accumulated `PR(A)/out_degree(A)` per copy in the inner loop. The errors cancelled for the symmetric A→B case (accidental correctness), but the graph semantics were wrong and could misbehave in asymmetric graphs.

4. **No damping factor validation** (`CONFIRMED`): Any float accepted silently, including values ≤ 0, ≥ 1, NaN, infinity.

#### Changes Implemented

**`backend/pagerank.py`** — complete rewrite of `calculate_pagerank`:
- Parameter renamed: `d` → `damping` (clearer variable name; old default 0.85 preserved)
- Damping factor validated: raises `ValueError` for values not strictly in (0, 1), or for NaN/inf
- Node list deduplicated (preserving first-occurrence order) before processing
- Edge filtering: edges where source or target is not in node set are silently discarded
- Edge deduplication: edges converted to a sorted set of tuples before out-degree computation
- Dangling nodes identified: nodes with 0 valid outgoing edges after filtering/dedup
- In-iteration dangling redistribution: `dangling_rank / N` added to every node's update at every iteration, not just post-hoc
- Incoming adjacency precomputed: `incoming[node] = [(src, out_deg), ...]` — eliminates O(E) full-edge-list scan per node per iteration
- Post-hoc normalization **removed**: algorithm now converges naturally to sum ≈ 1.0
- Convergence criterion unchanged: L1 norm `Σ|PR_new(i) - PR_old(i)| < tol`

**`tests/test_pagerank_baseline.py`** — two tests marked `@unittest.skip`:
- `test_c_dangling_node_graph`: asserted pre-Step-3 post-hoc-normalization values (historical record preserved)
- `test_invalid_target_edge`: asserted that invalid target inflated out-degree (historical record preserved)
- Reason documented in skip message; test body unchanged

#### Mathematical Model

```
PR(i) = (1 - d) / N
        + d × [ dangling_rank / N
                + Σ_{j→i valid} PR(j) / outgoing_links(j) ]

where:
  dangling_rank = Σ_{j: dangling} PR(j)
```

This is the standard PageRank formulation equivalent to a row-stochastic transition matrix where dangling node rows are replaced with uniform (1/N) distribution.

#### Tests Added

New file: `tests/test_pagerank_correctness.py`
- 36 tests in 12 classes
- Mass conservation: 6 graph types (simple, cycle, dangling, disconnected, self-loop, all-dangling)
- Cycle symmetry (A=B=C=1/3)
- Dangling redistribution correctness (formula verified at convergence)
- Disconnected graph convergence and symmetry
- Self-loop single-node and mixed-graph
- Duplicate edge deduplication (triple=single)
- Invalid target filtering (3 cases)
- Damping validation (7 cases: valid, zero, one, negative, above-1, NaN, inf)
- Determinism (2 cases: simple and complex graph)
- Convergence (3 cases: fixed-point residual, max_iterations respected, multiple iterations required)
- Numerical stability (5 cases: NaN, inf, negative, empty, single isolated)
- Performance sanity (100-node chain)

#### Test Results

| Run | Old Baseline | New Correctness | Total | Outcome |
|-----|-------------|-----------------|-------|---------|
| 1 | 14 pass, 2 skip | 36 pass | 50 pass, 2 skip | PASS |
| 2 | 14 pass, 2 skip | 36 pass | 50 pass, 2 skip | PASS |
| 3 | 14 pass, 2 skip | 36 pass | 50 pass, 2 skip | PASS |

#### Before vs After

| Graph | Before A | Before B | Before C | After A | After B | After C | Max Diff |
|-------|----------|----------|----------|---------|---------|---------|----------|
| Dangling A→B→C | 0.184417 | 0.341171 | 0.474412 | 0.184417 | 0.341171 | 0.474412 | ~1e-7 |
| Invalid target | A=0.5, B=0.5 | — | — | A=0.5, B=0.5 | — | — | 0 |
| Duplicate A→B×3 | A=0.35088, B=0.64912 | — | — | A=0.35088, B=0.64912 | — | — | ~7e-8 |

For the dangling node case, numerical difference is ~1e-7 (below 6 decimal place precision). Both models give similar values for short chains because teleportation partially compensates. The mathematical mechanism is now correct.

For the invalid target case, the numeric result happens to be identical (0.5/0.5) but for a completely different reason: old mechanism was rank leakage + normalization; new mechanism is correct dangling redistribution of both isolated nodes.

#### Performance Sanity Check

| Graph | Nodes | Edges | Time | Sum |
|-------|-------|-------|------|-----|
| 100-node chain | 100 | 99 | ~2ms | 1.000000 |

No performance regression. Incoming adjacency precomputation reduces inner-loop work.

#### Limitations

- The `d` parameter was renamed from `d` to `damping` in the function signature. Positional calls still work; keyword `d=0.85` calls will now fail with `TypeError`. App.py calls `calculate_pagerank(pages, links)` without the parameter, so no application breakage occurs.
- Step 2 baseline test for duplicate edges (`test_f_duplicate_edge_graph`) still passes because the old accidental behavior (out-degree and accumulation errors cancelled) gives nearly identical numeric results to the correct deduplicated computation. The test is not skipped.
- No crawler work performed.
- No graph analysis performed.
- No new algorithms added.

---

## STEP 3 — COMPLETE

Date: 2026-09-19

Verified:

* Step 1 documentation reviewed
* Step 2 baseline tests reviewed
* Current PageRank implementation understood
* Correct classical PageRank model implemented
* Dangling nodes correctly handled (in-iteration redistribution)
* Invalid target edges handled (filtered before computation)
* Duplicate edges handled consistently (explicit deduplication)
* Self-loops handled (naturally by the formula)
* Disconnected graphs handled (teleportation model)
* Damping factor validated (ValueError for invalid values)
* Convergence criterion documented (L1 norm)
* Deterministic ordering established (preserved input order + sorted edges)
* Numerical stability verified (36 tests pass)
* Correctness tests added (36 tests in test_pagerank_correctness.py)
* Regression tests pass (50 pass, 2 skip — 3 consecutive runs)
* API tests pass (all 8 API baseline tests pass)
* Full test suite passes repeatedly
* Before/after behavior documented
* No crawler work performed
* No graph-analysis work performed
* No ranking-comparison algorithms added
* No Step 4 work performed
* pagerank-core.md created
* research-log.md updated

