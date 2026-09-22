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

---

## Phase 1 — Step 4: Graph Edge-Case Handling

### Date: 2026-09-20

### Objective
Establish deliberate, predictable, and robust handling of malformed, incomplete, unusual, and pathological graph inputs before reaching the PageRank calculation core, ensuring clean HTTP 400 error reporting and mathematical validity across all graph topologies.

### Issues Identified & Solved

| Edge Case | Old / Unchecked Behavior | Hardened / New Behavior |
| :--- | :--- | :--- |
| `pages` not a list (string, dict, None) | Iterated characters (string) or crashed with TypeError | `ValueError` with descriptive message (HTTP 400) |
| Node identifier not string (None, int, bool) | Accepted into dictionary, broke serialization or crashed | `ValueError` requiring non-empty string (HTTP 400) |
| Empty / whitespace-only node identifier | Accepted empty string as node key | `ValueError` requiring non-empty string (HTTP 400) |
| `links` not a list (string, dict, None) | Crashed with TypeError | `ValueError` with descriptive message (HTTP 400) |
| Edge not a 2-element sequence | Sliced strings accidentally or crashed with `IndexError` | `ValueError` requiring `[source, target]` pair (HTTP 400) |
| Edge source/target not string or empty | Accepted None/empty or crashed during set operations | `ValueError` requiring non-empty strings (HTTP 400) |
| Invalid damping ($\le 0, \ge 1$, NaN, inf) | Infinite loop or incorrect values | `ValueError` requiring $d \in (0, 1)$ finite float (HTTP 400) |
| Invalid tol ($\le 0$, NaN, inf) | Silent non-convergence or all-iteration execution | `ValueError` requiring positive finite float (HTTP 400) |
| Invalid max_iterations ($< 1$, bool, float) | Zero iteration / early exit | `ValueError` requiring positive integer $\ge 1$ (HTTP 400) |
| Isolated single node / empty graph | Handled in core | Explicitly verified, mass conserved |
| Dangling chains, star graphs, complete graphs | Handled in core | Explicitly verified with dedicated topology tests |

### Artifacts Created / Modified

- **`backend/graph_validator.py`**: Created validation module establishing the input contract; exact 2-element check `len(edge) == 2` enforced for all edges.
- **`backend/app.py`**: Updated `/calculate` endpoint to validate graph structure and parameters, returning HTTP 400 on `ValueError`.
- **`backend/pagerank.py`**: Added direct validation for `tol` and `max_iterations` parameters.
- **`tests/test_graph_edge_cases.py`**: Created 48 unit, edge-case, topological, and API tests (including edge length boundaries).
- **`docs/graph-contract.md`**: Created formal data contract documentation.
- **`docs/architecture.md`**: Updated data flow diagram to include validator boundary and corrected PageRank solver description (in-iteration dangling redistribution without post-hoc normalization).

### Test Results

| Test Suite | Tests Passed | Tests Skipped | Tests Failed |
| :--- | :--- | :--- | :--- |
| `tests/test_api_baseline.py` | 8 | 0 | 0 |
| `tests/test_pagerank_baseline.py` | 6 | 2 (expected) | 0 |
| `tests/test_pagerank_correctness.py` | 36 | 0 | 0 |
| `tests/test_graph_edge_cases.py` | 48 | 0 | 0 |
| **Total** | **98** | **2** | **0** |

---

## STEP 4 — COMPLETE

Date: 2026-09-20 (Final review fixes: 2026-09-22)

Verified:
* Graph input boundary defined and enforced via `graph_validator.py`
* Exact 2-element edge constraint (`len(edge) == 2`) strictly validated
* Malformed node and edge structures return descriptive `ValueError` and HTTP 400
* Pathological topologies (empty, single node, complete, star, isolated, disconnected) verified
* Numerical parameters (`damping`, `tol`, `max_iterations`) validated at both API and core layers
* 48 comprehensive tests in `tests/test_graph_edge_cases.py`
* All 98 non-skipped tests pass cleanly and reproducibly across multiple runs
* `docs/graph-contract.md` created, `docs/architecture.md` and `docs/research-log.md` updated
* No PageRank algorithm changes, no crawler modifications, no frontend changes, no Step 5 work started

---

## Phase 1 — Step 5: Graph Analysis Layer

### Date: 2026-09-22

### Objective
Create a reusable, deterministic Graph Analysis Layer (`backend/graph_analyzer.py`) that computes structural graph properties (node count, edge count, density, degrees, dangling & isolated node counts, WCC, SCC) on top of the validated graph contract established in Step 4.

### Capabilities Implemented & Tested

1. **`node_count`**: Number of unique validated nodes in the graph.
2. **`edge_count`**: Number of unique valid directed edges (excluding duplicates and unknown node references).
3. **`density`**: Directed graph density $E / (N \times (N - 1))$ for $N \ge 2$, and $0.0$ for $N < 2$.
4. **`in_degree`**: Mapping of every node ID to its in-degree count (including $0$).
5. **`out_degree`**: Mapping of every node ID to its out-degree count (including $0$).
6. **`dangling_node_count`**: Count of nodes with `out_degree == 0`.
7. **`isolated_node_count`**: Count of nodes with `in_degree == 0 AND out_degree == 0`.
8. **`weakly_connected_components`**: WCC discovery treating edges as undirected connections; output ordered deterministically.
9. **`strongly_connected_components`**: SCC discovery via Tarjan's algorithm for directed mutual reachability; output ordered deterministically.
10. **`POST /analyze`**: API endpoint exposing structural graph analysis with `HTTP 400` validation error handling.

### Artifacts Created / Modified

- **`backend/graph_analyzer.py`**: Created deterministic graph structural analysis module.
- **`backend/app.py`**: Added `POST /analyze` API endpoint using `analyze_graph()`.
- **`tests/test_graph_analysis.py`**: Created 14 unit and API integration tests covering all 10 topological cases.
- **`docs/graph-analysis.md`**: Created formal documentation for graph structural analysis.
- **`docs/architecture.md`**: Updated system diagram and layer descriptions to include `graph_analyzer.py` and `/analyze`.

### Test Results

| Test Suite | Tests Passed | Tests Skipped | Tests Failed |
| :--- | :--- | :--- | :--- |
| `tests/test_api_baseline.py` | 8 | 0 | 0 |
| `tests/test_pagerank_baseline.py` | 6 | 2 (expected) | 0 |
| `tests/test_pagerank_correctness.py` | 36 | 0 | 0 |
| `tests/test_graph_edge_cases.py` | 48 | 0 | 0 |
| `tests/test_graph_analysis.py` | 14 | 0 | 0 |
| **Total** | **112** | **2** | **0** |

---

## STEP 5 — COMPLETE

Date: 2026-09-22

Verified:
* Deterministic graph structural analysis layer established in `backend/graph_analyzer.py`
* All 10 structural properties computed accurately and deterministically
* Reuses Step 4 `graph_validator.py` as source of truth for graph validity
* 14 comprehensive tests added in `tests/test_graph_analysis.py` (112 total tests pass)
* `POST /analyze` API endpoint added and verified
* `docs/graph-analysis.md` created, `docs/architecture.md` and `docs/research-log.md` updated
* No PageRank algorithm changes, no crawler modifications, no frontend redesign, no Step 6 work started

---

## Phase 1 — Step 6: Crawler Hardening

### Date: 2026-09-22

### Objective
Harden the existing web crawler (`backend/crawler.py`) so that it provides a technically reliable, reproducible, and deterministic same-host crawling layer with strict URL normalization, domain boundary security, failure resilience, and full compatibility with the Step 4 graph validator.

### Original Crawler Inspection Findings & Defects Addressed

| Area | Original Behavior / Defect | Hardened Behavior |
| :--- | :--- | :--- |
| **URL Normalization** | Basic `urldefrag` + trailing slash strip | Full `normalize_url`: strips fragments, lowercases host, handles scheme-relative `//host`, strips default ports (`:80`/`:443`), preserves query strings, rejects non-HTTP schemes (`mailto:`, `javascript:`, `tel:`, `data:`). |
| **Domain Boundary** | Exact string comparison on `netloc` | Strict `is_same_host` checking effective host (ignoring default ports). Prevents off-domain crawling, sub-domain expansion, and malicious host suffixes like `example.com.evil.com`. |
| **Redirects** | Followed redirects blindly without checking final host | Rejects redirect targets that lead off-domain (`response.url` must pass `is_same_host`). |
| **Non-HTML Resources** | Checked `text/html` string | Checked `text/html` or `application/xhtml+xml`. Excludes images, PDFs, ZIPs, and non-HTML assets from crawl targets. |
| **Failures & Timeouts** | Caught `RequestException`, but added failed pages to `visited` output | Catches `RequestException` & timeouts (`REQUEST_TIMEOUT = 8s`), records failed URLs in metadata (`pages_failed`), excludes non-HTML/4xx/5xx URLs from returned graph nodes. Fallback ensures single unresolvable seed URL returns seed node for baseline API compatibility. |
| **Relative URLs** | `urljoin(base_url, href)` | Preserves exact response URL (including trailing directory slash) for resolving relative paths (`/about`, `../contact`, `./team`). |
| **Determinism** | Standard BFS with set storage | Deterministic traversal order using DOM anchor sequence, queue FIFO, and lexicographically sorted `pages` and `links` arrays. |
| **Graph Contract Compatibility** | Basic edge filtering | 100% compatible with `graph_validator.py`. Verified via unit tests passing crawler output to `validate_graph`. |

### Artifacts Created / Modified

- **`backend/crawler.py`**: Hardened URL normalization, domain boundary checks, redirect handling, non-HTML filtering, and metadata reporting while preserving `fetch_html` for baseline compatibility.
- **`tests/test_crawler.py`**: Created 25 unit and integration tests using mocked HTTP responses (0 external live network dependencies).
- **`docs/crawler.md`**: Created formal documentation for web crawler specifications and contracts.
- **`docs/architecture.md`**: Updated data flow diagram and crawler component description.

### Test Execution Matrix (3 Consecutive Runs)

| Test Suite | Run 1 | Run 2 | Run 3 |
| :--- | :--- | :--- | :--- |
| `tests/test_api_baseline.py` | 8 Passed | 8 Passed | 8 Passed |
| `tests/test_pagerank_baseline.py` | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped |
| `tests/test_pagerank_correctness.py` | 36 Passed | 36 Passed | 36 Passed |
| `tests/test_graph_edge_cases.py` | 48 Passed | 48 Passed | 48 Passed |
| `tests/test_graph_analysis.py` | 14 Passed | 14 Passed | 14 Passed |
| `tests/test_crawler.py` | 25 Passed | 25 Passed | 25 Passed |
| **Total** | **137 Passed, 2 Skipped** | **137 Passed, 2 Skipped** | **137 Passed, 2 Skipped** |

---

## STEP 6 — COMPLETE

Date: 2026-09-22

Verified:
* Existing crawler inspected and documented before modification
* URL normalization canonicalized and tested (`normalize_url`)
* Fragment, relative URL, scheme, default port, and query string policies implemented and tested
* Host/domain boundary strictly enforced (`is_same_host`), rejecting malicious sub-domains and off-domain redirects
* Non-HTML resources (`image/png`, `application/pdf`, `application/zip`) excluded via Content-Type checking
* HTTP status errors (4xx, 5xx) and timeouts handled gracefully without crashing crawl loop
* Page limit (`max_pages`) strictly enforced without off-by-one errors
* Crawl ordering is deterministic for deterministic input
* Crawler output directly satisfies Step 4 `graph_validator.py`
* 25 dedicated mock crawler tests added in `tests/test_crawler.py` (0 live internet dependencies)
* All 137 non-skipped tests pass consistently across 3 consecutive runs
* `docs/crawler.md` created, `docs/architecture.md` and `docs/research-log.md` updated
* No PageRank algorithm changes, no crawler improvements beyond scope, no frontend redesign, no Step 7 work started

---

## Phase 1 — Step 7: Crawler → Graph → PageRank Integration

### Date: 2026-09-22

### Objective
Integrate the hardened crawler, graph validator, graph analyzer, and PageRank computational engine into a unified, sequential, reproducible data pipeline:
`Crawler -> Graph Validator -> Graph Analysis -> PageRank Engine -> API Result`.

### Invariants & Pipeline Verification

1. **Boundary Enforcement**: Raw crawler output `(raw_pages, raw_links)` is strictly passed into `validate_graph()` before reachability/ranking execution. Malformed graphs fail at the validator boundary with `HTTP 400` without reaching PageRank.
2. **Node & Edge Consistency**:
   $$\text{Set}(Pages_{\text{crawler}}) = \text{Set}(Pages_{\text{validated}}) = \text{Set}(Nodes_{\text{analysis}}) = \text{Set}(Nodes_{\text{pagerank}})$$
3. **Rank Coverage & Mass Conservation**: Every node in the validated graph receives a PageRank score, and total rank mass sums to $1.0 \quad (\pm 10^{-5})$.
4. **Determinism**: Identical mocked crawls produce bitwise identical outputs across repeated runs.

### Artifacts Created / Modified

- **`backend/app.py`**: Updated `POST /crawl` to execute the sequential pipeline (`crawl_site -> validate_graph -> analyze_graph -> calculate_pagerank`).
- **`tests/test_crawler_pagerank_integration.py`**: Created 11 end-to-end integration tests covering chains, cycles, dangling nodes, disconnected graphs, duplicate links, self-loops, isolated nodes, boundary failures, repeated pipeline determinism, and API `/crawl` verification.
- **`docs/pipeline-integration.md`**: Created formal documentation for the integrated pipeline contracts, boundary sequence, and invariants.
- **`docs/architecture.md`**: Updated system architecture diagram to reflect the sequential pipeline.

### Test Execution Matrix (3 Consecutive Runs)

| Test Suite | Run 1 | Run 2 | Run 3 |
| :--- | :--- | :--- | :--- |
| `tests/test_api_baseline.py` | 8 Passed | 8 Passed | 8 Passed |
| `tests/test_pagerank_baseline.py` | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped |
| `tests/test_pagerank_correctness.py` | 36 Passed | 36 Passed | 36 Passed |
| `tests/test_graph_edge_cases.py` | 48 Passed | 48 Passed | 48 Passed |
| `tests/test_graph_analysis.py` | 14 Passed | 14 Passed | 14 Passed |
| `tests/test_crawler.py` | 25 Passed | 25 Passed | 25 Passed |
| `tests/test_crawler_pagerank_integration.py` | 11 Passed | 11 Passed | 11 Passed |
| **Total** | **148 Passed, 2 Skipped** | **148 Passed, 2 Skipped** | **148 Passed, 2 Skipped** |

---

## STEP 7 — COMPLETE

Date: 2026-09-22

Verified:
* Sequential integration pipeline (`Crawler -> Validator -> Analysis -> PageRank`) established in `backend/app.py`
* All 6 data consistency invariants verified across end-to-end tests
* Validation boundary strictly enforced prior to graph analysis and PageRank execution
* 11 dedicated integration tests created in `tests/test_crawler_pagerank_integration.py`
* All 148 non-skipped tests pass consistently across 3 consecutive runs
* `docs/pipeline-integration.md` created, `docs/architecture.md` and `docs/research-log.md` updated
* No PageRank algorithm changes, no frontend redesign, no Step 8 work started

---

## Phase 1 — Step 8: Ranking Comparison Layer

### Date: 2026-09-22

### Objective
Establish an independent, reusable **Ranking Comparison Layer** (`backend/ranking_comparator.py`) to calculate objective mathematical comparison metrics between ranking vectors over the same node set.

### Contract & Invariants
1. **Independence**: Operates independently of the PageRank engine without modifying input ranking vectors or making evaluative superiority claims.
2. **Strict Validation**: Validates dictionary structure, node ID strings, finite numerical scores, and exact node set matching ($V_A = V_B$).
3. **Common Node Alignment**: Aligns score vectors onto a deterministic lexicographical node ordering.
4. **Mathematical Metrics Implemented**:
   - L1 Distance ($\sum |A_i - B_i|$)
   - L2 Distance ($\sqrt{\sum (A_i - B_i)^2}$)
   - Cosine Similarity ($\frac{A \cdot B}{\|A\| \|B\|}$, returning 1.0 for double-zero vectors and 0.0 for single-zero vectors)
   - Spearman Rank Correlation ($\rho$, using fractional average ranks for ties)
   - Kendall Tau-b Rank Correlation ($\tau_b$, explicitly accounting for ties)
   - Top-K Overlap ($\frac{|\text{TopK}(A) \cap \text{TopK}(B)|}{k}$, using score desc then node ID asc tie-breaking)
   - Rank Displacement Statistics (max displacement, mean displacement, per-node displacement)
5. **API Integration**: Exposes `POST /compare` endpoint in `backend/app.py` returning structured JSON metrics.

### Artifacts Created / Modified
- **`backend/ranking_comparator.py`**: Implementation of vector validation, alignment, and 10 comparison metrics.
- **`backend/app.py`**: Integrated `POST /compare` route handler.
- **`tests/test_ranking_comparator.py`**: Created 24 unit & API integration tests covering validation, distance metrics, cosine safety, Spearman/Kendall tie handling, top-k overlap tie-breaking, rank displacements, and HTTP endpoint responses.
- **`docs/ranking-comparison.md`**: Formal specification of the ranking comparison contract and metric formulas.
- **`docs/architecture.md`**: Updated architecture diagram and component specifications.

### Test Execution Matrix (3 Consecutive Runs)

| Test Suite | Run 1 | Run 2 | Run 3 |
| :--- | :--- | :--- | :--- |
| `tests/test_api_baseline.py` | 8 Passed | 8 Passed | 8 Passed |
| `tests/test_pagerank_baseline.py` | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped | 6 Passed, 2 Skipped |
| `tests/test_pagerank_correctness.py` | 36 Passed | 36 Passed | 36 Passed |
| `tests/test_graph_edge_cases.py` | 48 Passed | 48 Passed | 48 Passed |
| `tests/test_graph_analysis.py` | 14 Passed | 14 Passed | 14 Passed |
| `tests/test_crawler.py` | 25 Passed | 25 Passed | 25 Passed |
| `tests/test_crawler_pagerank_integration.py` | 11 Passed | 11 Passed | 11 Passed |
| `tests/test_ranking_comparator.py` | 24 Passed | 24 Passed | 24 Passed |
| **Total** | **172 Passed, 2 Skipped** | **172 Passed, 2 Skipped** | **172 Passed, 2 Skipped** |

---

## STEP 8 — COMPLETE

Date: 2026-09-22

Verified:
* Ranking comparison layer (`backend/ranking_comparator.py`) implemented independently of PageRank solver
* All 10 required mathematical comparison capabilities fully implemented and tested
* Ranking vector validation and common-node alignment strictly enforced
* Spearman and Kendall tau-b tie-handling policies documented and tested
* Cosine similarity zero-vector handling policies documented and tested
* Deterministic tie-breaking established for Top-K overlap and rank displacements
* `POST /compare` API endpoint exposed in `backend/app.py`
* 24 dedicated unit and integration tests added in `tests/test_ranking_comparator.py`
* All 172 non-skipped tests pass consistently across 3 consecutive clean runs
* `docs/ranking-comparison.md` created, `docs/architecture.md` and `docs/research-log.md` updated
* No evaluative claims made, no PageRank algorithm changes, no frontend redesign, no Step 9 work started






