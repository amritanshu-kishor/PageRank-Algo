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
