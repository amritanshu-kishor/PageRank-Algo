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

#### Test Execution & Verification
- **Test Frameworks Verified**: Python `unittest` (`python -m unittest discover tests`) and `pytest` (`pytest -v tests/`).
- **Test Suite Results**: 16/16 tests passed deterministically in ~3.1s.

---

## Step 2 Completion Status

### STEP 2 — COMPLETE

Date: 2026-09-19

Verified:
* Automated test directory `tests/` created
* JSON graph fixtures created under `tests/fixtures/`
* `test_pagerank_baseline.py` implemented and verified
* `test_api_baseline.py` implemented and verified
* Existing application behavior captured without source code modification
* Baseline test suite executed with 100% pass rate (16/16 passed)
* Step 2 documented in research log

