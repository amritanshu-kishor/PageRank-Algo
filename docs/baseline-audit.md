# Baseline Repository Audit & Verification Report

This document records the exact state, architectural audit, component analysis, algorithm verification, and baseline test results for the `PageRank-Algo` repository as verified during Phase 1 — Step 1.

---

## 1. Repository Structure Audit

### 1.1 Backend Components (`backend/`)

| File | Actual Responsibility | Dependencies | Status |
| ---- | --------------------- | ------------ | ------ |
| `app.py` | Flask REST API web server exposing `/calculate` and `/crawl` endpoints; handles CORS headers, JSON request validation, error handling, score sorting, and process initialization. | `flask`, `flask_cors`, `crawler.py`, `pagerank.py`, `os` | WORKING |
| `pagerank.py` | Pure Python iterative solver for PageRank algorithm; calculates node out-degrees, executes power iteration updates, tests convergence, and performs final vector normalization. | Built-in Python primitives | WORKING |
| `crawler.py` | Web crawler for discovering same-domain HTML pages via BFS; normalizes URLs, extracts `<a>` anchor links, filters cross-domain and self-links, and constructs page/link lists. | `requests`, `bs4` (BeautifulSoup), `urllib.parse`, `collections.deque` | WORKING |
| `requirements.txt` | Defines pinned third-party Python package dependencies required for backend execution. | None | WORKING |
| `.env.example` | Provides environment variable template (`FLASK_APP`, `FLASK_ENV`, `FLASK_DEBUG`, `FLASK_HOST`, `FLASK_PORT`, `CORS_ORIGINS`). | None | WORKING |

### 1.2 Frontend Components (`frontend/`)

| File | Actual Responsibility | Dependencies | Status |
| ---- | --------------------- | ------------ | ------ |
| `index.html` | UI markup defining sidebar menu (stats block, page management, connect tools, analyze buttons, experimental crawl panel, ranking leaderboard) and main graph stage canvas container (`#cy`). | Google Fonts (`Inter`), Cytoscape.js CDN | WORKING |
| `script.js` | Client-side application logic; initializes Cytoscape instance, handles DOM event listeners, manages graph node/edge addition, calls backend APIs via `fetch()`, animates node sizes, and updates ranking UI. | Cytoscape.js (`cytoscape.min.js`), Browser Fetch API | WORKING |
| `style.css` | Styling definitions for dark-themed workspace layout, sidebar controls, buttons, CSS grid stage background, legend badges, and ranking leaderboard item entry animations. | Vanilla CSS3 | WORKING |

### 1.3 Project-Level Files

| File | Purpose |
| ---- | ------- |
| `start_backend.ps1` | PowerShell helper script to execute `backend/app.py` using virtual environment Python interpreter (`.\venv\Scripts\python.exe`). |
| `start_frontend.ps1` | PowerShell helper script to start standard HTTP server on port 8000 serving `frontend/` directory. |
| `README.md` | Documentation guide covering project features, virtual environment setup, backend/frontend startup commands, and manual URL input usage. |
| `.gitignore` | Specifies files ignored by Git repository (virtual environment `venv/`, bytecode `__pycache__/`, `.env` files, editor settings). |

---

## 2. Baseline Architecture & API Endpoint Audit

### 2.1 API Endpoint Specification

#### Endpoint 1: `POST /calculate`
* **HTTP Method**: `POST`
* **Route**: `/calculate`
* **Request JSON Payload**:
  ```json
  {
    "pages": ["A", "B", "C"],
    "links": [["A", "B"], ["B", "C"]]
  }
  ```
* **Validation**: Checks if payload is valid JSON and contains top-level keys `'pages'` and `'links'`. Returns HTTP `400` with `{'error': 'Invalid input format. Expected pages and links.'}` if missing.
* **Internal Function Called**: `calculate_pagerank(pages, links)` from `backend/pagerank.py`.
* **Response JSON**: Dictionary mapping page names to PageRank float scores, sorted in descending order of rank.
  ```json
  {
    "C": 0.47441217150760717,
    "B": 0.34117104656523745,
    "A": 0.18441678192715535
  }
  ```
* **HTTP Status Codes**: `200 OK` on success; `400 Bad Request` on invalid input format; `500 Internal Server Error` on unexpected exception.
* **Error Handling**: Wrapped in top-level `try...except Exception as e`, returning `jsonify({'error': str(e)}), 500`.

#### Endpoint 2: `POST /crawl`
* **HTTP Method**: `POST`
* **Route**: `/crawl`
* **Request JSON Payload**:
  ```json
  {
    "url": "https://quotes.toscrape.com",
    "max_pages": 8
  }
  ```
* **Validation**: Checks if payload is JSON and contains `'url'`. Returns `400` if missing. Optional `'max_pages'` defaults to 12 (clamped between 1 and 30 by crawler).
* **Internal Functions Called**: `crawl_site(url, max_pages)` from `backend/crawler.py` followed by `calculate_pagerank(pages, links)`.
* **Response JSON**:
  ```json
  {
    "pages": ["https://quotes.toscrape.com/", "..."],
    "links": [["https://quotes.toscrape.com/", "https://quotes.toscrape.com/login"]],
    "scores": {
      "https://quotes.toscrape.com/": 0.4512,
      "...": 0.1234
    }
  }
  ```
* **HTTP Status Codes**: `200 OK` on success; `400 Bad Request` on invalid URL format or zero pages found; `500 Internal Server Error` on unexpected exception.
* **Error Handling**: Catches `ValueError` returning HTTP `400`, catches `Exception` returning HTTP `500`.

---

## 3. PageRank Algorithm Implementation Audit (`backend/pagerank.py`)

| Aspect / Behavior | Detailed Code Findings | Status |
| ----------------- | ---------------------- | ------ |
| **Initialization** | Initializes equal probability rank vector $PR(p) = 1.0 / N$ for all pages $p \in \text{pages}$, where $N = \text{len(pages)}$. If $N=0$, returns `{}`. | WORKING |
| **Damping Factor ($d$)** | Parameter $d = 0.85$ (default keyword argument in signature). | WORKING |
| **Maximum Iterations** | Parameter `max_iterations = 100` (default keyword argument). | WORKING |
| **Convergence Tolerance** | Parameter `tol = 1.0e-6` (default keyword argument). Check computes $L_1$ norm diff: $\sum_{p} |PR_{new}(p) - PR_{old}(p)| < \text{tol}$. | WORKING |
| **Outgoing-Degree Calculation** | Initializes `out_degree = {page: 0}`. Iterates over `(source, target)` in `links` and increments `out_degree[source]` if `source in out_degree`. | WORKING |
| **Iterative Update** | Update formula: `new_pr[page] = ((1.0 - d) / N) + (d * rank_sum)` where `rank_sum` sums `pr[source] / out_degree[source]` for all edges matching `target == page`. | WORKING |
| **Convergence Condition** | Evaluated after updating all nodes in an iteration. If total difference `< tol`, prints iteration count and breaks loop early. | WORKING |
| **Final Normalization** | Post-hoc normalization after iteration loop finishes: `total_pr = sum(pr.values())`; if `total_pr > 0`, divides each node's score by `total_pr`. | PARTIALLY HANDLED |
| **Duplicate Edges** | Code comment assumes unique edges. If duplicates exist in `links`, `out_degree[source]` increments for each duplicate and inner matching loop accumulates `pr[source]/out_degree` multiple times. Out-degree and rank contribution grow proportionally. | PARTIALLY HANDLED |
| **Dangling Nodes** | Nodes with `out_degree[source] == 0` do not distribute rank to any target during power iterations. Rank leaks out of the system during iterations. The post-hoc final normalization forces rank sum to 1.0 at the end, but the iteration trajectory does NOT match standard PageRank (which redistributes dangling rank evenly to all $N$ nodes at every iteration). | PARTIALLY HANDLED |
| **Disconnected Nodes** | Isolated nodes with 0 in-degree and 0 out-degree receive minimal rank $(1-d)/N$ each iteration, retain their rank (since they don't distribute), and are normalized at the end. | WORKING |
| **Self-Loops** | Source == Target matches inner loop condition `target == page`. Source distributes $1/\text{out\_degree}$ of its rank back to itself. | WORKING |
| **Invalid Edges** | If `links` contains edge $(S, T)$ where $T \notin \text{pages}$, $T$ is ignored, but $S$ increments `out_degree[S]`. Rank is lost to non-existent node $T$. | NOT HANDLED |
| **Empty Graph** | $N=0$ condition checked at entry: `if N == 0: return {}`. | WORKING |

---

## 4. Web Crawler Audit (`backend/crawler.py`)

| Aspect / Behavior | Detailed Code Findings | Status |
| ----------------- | ---------------------- | ------ |
| **URL Normalization** | `normalize_url(raw_url)`: strips whitespace, prepends `https://` if scheme omitted, strips fragments via `urldefrag()`, lowercases scheme and hostname, removes trailing slash unless path is `"/"`. | WORKING |
| **HTTP/HTTPS Handling** | Forces `https://` default if scheme missing; filters out non-`http`/`https` schemes. | WORKING |
| **Fragment Removal** | Handled via `urldefrag(raw_url)`. | WORKING |
| **Trailing Slash Behavior** | Strips trailing slash if path != `"/"`. | WORKING |
| **Query-String Behavior** | Preserved in `urlunparse()`. | WORKING |
| **Redirect Behavior** | `session.get(..., allow_redirects=True)` follows HTTP 301/302 redirects. | WORKING |
| **Same-Domain Restriction** | Extracts `root_host = urlparse(start_url).netloc.lower()`. Any link where `urlparse(target_url).netloc.lower() != root_host` is discarded. | WORKING |
| **Crawl Strategy** | Breadth-First Search (BFS) using `collections.deque` queue. | WORKING |
| **Visited-Page Tracking** | Uses `visited` set to prevent re-crawling pages. Stops when `len(visited) >= max_pages`. | WORKING |
| **Duplicate Link Filtering** | Edges collected in `links = set()`, eliminating duplicate directed edges. | WORKING |
| **Self-Link Filtering** | Explicitly filtered in `filtered_links`: `edge[0] != edge[1]`. | WORKING |
| **Broken Pages / Bad HTTP** | `fetch_html()` returns `None` if HTTP status $\ge 400$ or `RequestException` occurs. Page remains in `visited` set but no outbound links are added. | PARTIALLY HANDLED |
| **Non-HTML Responses** | Checks `Content-Type` header; returns `None` if `"text/html"` is not present. | WORKING |
| **Request Timeout** | `REQUEST_TIMEOUT = 8` seconds per GET request. | WORKING |
| **User-Agent Header** | Custom header `USER_AGENT = "MiniPageRankCrawler/1.0"`. | WORKING |
| **Maximum Page Limit** | Clamped via `max_pages = max(1, min(int(max_pages or 12), 30))`. Queue additions respect `len(visited) + len(queued) < max_pages`. | WORKING |
| **Error Handling** | Unresolvable domain returns single entry in `visited` with 0 links and HTTP status 200 rather than raising 400 error. | PARTIALLY HANDLED |

---

## 5. Frontend Audit (`frontend/`)

| Aspect / Feature | Detailed Code Findings | Status |
| ---------------- | ---------------------- | ------ |
| **User Workflow** | Supports 1. Add page, 2. Add directed link, 3. Load sample graph, 4. Clear graph, 5. Relayout, 6. Fit canvas, 7. Calculate PageRank, 8. Experimental crawl, 9. Ranking leaderboard, 10. Visual node/edge sizing and color highlighting. | WORKING |
| **Data Payload Format** | Sends explicit JSON payloads to Flask backend matching API contracts. | WORKING |
| **Cytoscape Integration** | Uses Cytoscape.js 3.26.0 with `grid` layout on load, switching dynamically to `circle` ($\le 8$ nodes) or `cose` ($> 8$ nodes). Node diameter scales dynamically between 42px and 96px based on relative PageRank ratio ($score / maxScore$). | WORKING |
| **Graph State Management** | Graph state stored natively in Cytoscape DOM elements (`cy.nodes()`, `cy.edges()`). | WORKING |
| **Node / Edge IDs** | Node ID is normalized string input. Edge ID is formatted as `${source}->${target}`. Duplicate additions prevented via `cy.getElementById(id).empty()`. | WORKING |
| **Ranking Display** | Leaderboard rendered in `<ol id="ranking-list">` using animated list items showing rank position (`#1`), label, and 4-decimal float score (`0.4744`). | WORKING |
| **Error Handling** | Displays native browser `alert()` dialogs for empty input, duplicate node/edge, or API network failures. | WORKING |
| **Loading State** | Toggles `#loading` visual text state during async fetch calls. | WORKING |

---

## 6. Baseline Verification Test Suite Results

The baseline verification tests were executed against the actual backend implementation without modifying any algorithm or crawler code.

### 6.1 Algorithmic Test Suite Results

#### Test A — Simple Chain
* **Input Graph**: Nodes = `['A', 'B', 'C']`, Links = `[['A', 'B'], ['B', 'C']]`
* **Iterations to Convergence**: 4
* **Calculated Output**:
  - `A`: `0.184417`
  - `B`: `0.341171`
  - `C`: `0.474412`
* **Sum of Ranks**: `1.000000`
* **Assessment**: C has highest rank as expected (sinks authority from B).
* **Status**: `PASS (Baseline Recorded)`

#### Test B — Cycle
* **Input Graph**: Nodes = `['A', 'B', 'C']`, Links = `[['A', 'B'], ['B', 'C'], ['C', 'A']]`
* **Iterations to Convergence**: 1
* **Calculated Output**:
  - `A`: `0.333333`
  - `B`: `0.333333`
  - `C`: `0.333333`
* **Sum of Ranks**: `1.000000`
* **Assessment**: Perfect symmetry; all nodes equal 1/3 as mathematically expected.
* **Status**: `PASS (Baseline Recorded)`

#### Test C — Dangling Node
* **Input Graph**: Nodes = `['A', 'B', 'C']`, Links = `[['A', 'B'], ['B', 'C']]` (C has no outgoing edges)
* **Iterations to Convergence**: 4
* **Calculated Output**:
  - `A`: `0.184417`
  - `B`: `0.341171`
  - `C`: `0.474412`
* **Sum of Ranks**: `1.000000`
* **Assessment**: Node C is a dangling node. Rank leaks during iterations and is post-hoc normalized at the end. Final scores match Test A because C has no out-edges in Test A as well.
* **Status**: `OBSERVATION (Dangling rank normalized post-hoc)`

#### Test D — Disconnected Graph
* **Input Graph**: Nodes = `['A', 'B', 'C', 'D']`, Links = `[['A', 'B'], ['C', 'D']]`
* **Iterations to Convergence**: 3
* **Calculated Output**:
  - `A`: `0.175439`
  - `B`: `0.324561`
  - `C`: `0.175439`
  - `D`: `0.324561`
* **Sum of Ranks**: `1.000000`
* **Assessment**: Symmetrical disconnected subgraphs receive equal total rank weight (0.5 per subgraph).
* **Status**: `PASS (Baseline Recorded)`

#### Test E — Self-Loop
* **Input Graph**: Nodes = `['A']`, Links = `[['A', 'A']]`
* **Iterations to Convergence**: 1
* **Calculated Output**:
  - `A`: `1.000000`
* **Sum of Ranks**: `1.000000`
* **Assessment**: Single node retains full rank.
* **Status**: `PASS (Baseline Recorded)`

#### Test F — Duplicate Edge
* **Input Graph**: Nodes = `['A', 'B']`, Links = `[['A', 'B'], ['A', 'B']]`
* **Iterations to Convergence**: 3
* **Calculated Output**:
  - `A`: `0.350877`
  - `B`: `0.649123`
* **Sum of Ranks**: `1.000000`
* **Assessment**: Duplicate link doubles out-degree of A to 2 and doubles matching in inner loop. Output score matches single-edge graph `['A', 'B']` (`A: 0.3509, B: 0.6491`).
* **Status**: `PASS (Baseline Recorded)`

### 6.2 Web Crawler Baseline Verification Result
* **Target Test Site**: `https://quotes.toscrape.com` (Max pages limit: 3)
* **Status**: `PASS`
* **Crawl Result**:
  - Pages Discovered: 3 (`https://quotes.toscrape.com/`, `https://quotes.toscrape.com/author/Albert-Einstein`, `https://quotes.toscrape.com/login`)
  - Edges Discovered: 5
  - PageRank Computation on Crawled Graph: Converged after 16 iterations.

### 6.3 Frontend Verification Result
* **Backend Status**: Flask server started on `http://127.0.0.1:5000` (Verified via HTTP POST requests).
* **Frontend Status**: HTTP server started on `http://127.0.0.1:8000` (Verified via HTTP GET requests).
* **Interactive Chrome Browser Verification**: **PASS (Fully Verified)**
  1. Opened `http://localhost:8000` and verified page title "PageRank Graph Workbench" and main header "PageRank Workbench".
  2. Added custom nodes (`PageA`, `PageB`) via UI inputs.
  3. Added directed link (`PageA` $\to$ `PageB`).
  4. Triggered "Calculate PageRank" — verified `PageB` received highest authority rank (`0.6491`), Top Rank stat badge updated to `PageB`, and node was highlighted in gold on canvas.
  5. Loaded Sample Graph — 6 pages (Home, Docs, Pricing, Support, Blog, Changelog) and 9 links successfully loaded into Cytoscape.
  6. Recalculated Sample Graph PageRank — verified `Docs` achieved top rank (`0.4252`).
  7. Ran Experimental Crawl (`https://quotes.toscrape.com`, limit 5) — verified completed summary (`Found 5 pages and 15 links.`) and automatic PageRank recalculation (`quotes.toscrape.com/` top rank `0.3479`).

---

## 7. Current Limitations & Classification

### 7.1 Mathematical / Algorithmic Limitations
1. **Dangling Node Leaking (LIMITATION)**: Nodes with out-degree = 0 leak rank during power iteration instead of distributing rank evenly to all $N$ nodes at each iteration step. Rank is restored only via post-hoc normalization after convergence.
2. **Post-Hoc Normalization Reliance (DESIGN CHOICE)**: The algorithm relies on post-hoc division by `sum(pr.values())` to guarantee a stochastic probability vector.
3. **No Power Iteration Matrix Representation (DESIGN CHOICE)**: Iteration is implemented via explicit Python loops over edge lists rather than sparse matrix operations (e.g. NumPy / SciPy transition matrices).

### 7.2 Backend Limitations
1. **In-Memory Single-Threaded Execution (LIMITATION)**: Flask application runs synchronously without background worker queues (Celery/Redis) or async I/O for long-running crawls.
2. **Missing Input Graph Validation (BUG)**: Invalid edges referencing targets not present in `pages` cause silent rank leakage without throwing a validation error.

### 7.3 Crawler Limitations
1. **Unresolvable URL Handling (DESIGN CHOICE / LIMITATION)**: Unresolvable or non-existent domain URLs do not trigger an HTTP 400 error; instead, the crawler returns `pages: [start_url]` and 0 links with HTTP status 200.
2. **Synchronous Crawling (LIMITATION)**: Page crawling is performed sequentially using single-threaded `requests.Session`, making multi-page crawls slow.
3. **No Robots.txt Parsing (NOT IMPLEMENTED)**: The crawler does not parse `robots.txt` compliance rules.

### 7.4 Frontend Limitations
1. **Basic Cytoscape Canvas Interaction (DESIGN CHOICE)**: The UI lacks node search, filter by rank threshold, or graph export functions (PNG/SVG/JSON).
2. **Error Alert Dialogs (DESIGN CHOICE)**: Uses primitive `window.alert()` rather than toast notifications or inline field validation messages.

---

## 8. Baseline Audit Summary & Status

* **Repository Audited**: YES
* **Architecture Documented**: YES
* **API Endpoints Verified**: YES
* **PageRank Implementation Audited**: YES
* **Crawler Implementation Audited**: YES
* **Frontend Workflow Audited**: YES
* **Baseline Test Suite Executed**: YES
* **Limitations Classified**: YES
* **Original Implementation Preserved**: YES
