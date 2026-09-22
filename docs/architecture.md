# System Architecture & Application Flow

This document details the architecture and endpoint-specific request/response flows of the PageRank-Algo application.

---

## 1. System Architecture Diagram

```text
Browser User Interface
         │
         ▼
frontend/script.js (Cytoscape.js & DOM Event Handler)
         │
         ├───────────────────────────────┬───────────────────────────────┬───────────────────────────────┐
         │ HTTP POST /calculate          │ HTTP POST /analyze            │ HTTP POST /crawl              │ HTTP POST /compare
         ▼                               ▼                               ▼                               ▼
Flask API Server (backend/app.py - Port 5000)
         │                               │                               │                               │
         │                               │                               │                               ▼
         │                               │                               │                     backend/ranking_comparator.py
         │                               │                               ▼                               (Ranking Comparison Layer)
         │                               │                     backend/crawler.py (Hardened BFS Crawler)
         │                               │                               │
         ▼                               ▼                               ▼
backend/graph_validator.py (Input Validation & Normalization Boundary)
         │                               │
         ├───────────────────────────────┤
         ▼                               ▼
backend/pagerank.py             backend/graph_analyzer.py
(Iterative Power Method)        (Structural Analysis Layer)
         │                               │
         ▼                               ▼
HTTP Response JSON               HTTP Response JSON
(Sorted PageRank Scores)         (Structural Metrics, WCC, SCC)
```

---

## 2. Layer Analysis

### 2.1 Browser & UI Layer (`frontend/index.html`, `frontend/style.css`)
- **Technology**: Vanilla HTML5, CSS3, Google Fonts (`Inter`).
- **Responsibility**: Provides a dark-themed interactive panel with controls to manually add nodes, add directed edges, load pre-defined sample graphs, trigger calculations, execute domain crawls, and render graph statistics and rank leaderboards.

### 2.2 Client-Side Logic & Graph Engine Layer (`frontend/script.js`, Cytoscape 3.26.0)
- **Technology**: Vanilla JavaScript ES6+, Cytoscape.js library.
- **Responsibility**:
  - Manages graph state (nodes and edges) inside Cytoscape.js instance.
  - Generates labels and truncates long page names/URLs for clean visual rendering.
  - Dynamically switches graph layout (`circle` for $\le 8$ nodes, `cose` for $> 8$ nodes).
  - Handles async `fetch()` HTTP requests to the backend API (`http://127.0.0.1:5000`).
  - Animates graph nodes (resizing diameter based on PageRank score ratio) and highlights top-ranked node and inbound edges.

### 2.3 HTTP API Layer (`backend/app.py`)
- **Technology**: Python 3.10+, Flask 3.0.2, Flask-CORS 4.0.0.
- **Responsibility**:
  - Exposes RESTful JSON endpoints (`/calculate`, `/analyze`, `/crawl`, `/compare`).
  - Manages Cross-Origin Resource Sharing (CORS) headers for local frontend access (`http://localhost:8000`, `http://127.0.0.1:8000`).
  - Validates request payloads and formats error responses.
  - Delegates execution to specialized backend modules.

### 2.4 Crawler Layer (`backend/crawler.py`)
- **Technology**: Python Requests 2.31.0, BeautifulSoup4 4.12.3, `urllib.parse`.
- **Responsibility**:
  - Performs hardened, deterministic same-host Breadth-First Search (BFS) starting at a seed URL.
  - Normalizes URLs (strips fragments, lowercases host, normalizes paths, preserves query strings).
  - Enforces strict same-host boundary restrictions and rejects off-domain redirects.
  - Filters non-HTML resources (via Content-Type check) and ignores non-HTTP schemes.
  - Handles HTTP status errors (4xx/5xx) and timeouts gracefully without crashing.
  - Returns a clean directed graph compatible with `graph_validator.py`.

### 2.5 Algorithmic Calculation Layer (`backend/pagerank.py`)
- **Technology**: Pure Python iterative solver (no external graph libraries used for solver).
- **Responsibility**:
  - Computes PageRank scores given node list and directed edge list using standard power iteration with in-iteration dangling-node rank redistribution:
    $$PR(i) = \frac{1-d}{N} + d \left[ \frac{\sum_{k \in \text{dangling}} PR(k)}{N} + \sum_{j \to i} \frac{PR(j)}{C(j)} \right]$$
  - Enforces L1-norm convergence check ($\sum |PR_{new}(i) - PR_{old}(i)| < \text{tol}$) or stops at `max_iterations`.
  - Preserves exact total rank mass conservation ($\sum PR(i) = 1.0$) throughout power iteration without relying on post-hoc normalization.

### 2.6 Graph Analysis Layer (`backend/graph_analyzer.py`)
- **Technology**: Pure Python graph analysis algorithms (BFS for WCC, Tarjan's algorithm for SCC).
- **Responsibility**:
  - Computes structural graph metrics (`node_count`, `edge_count`, `density`, `in_degree`, `out_degree`, `dangling_node_count`, `isolated_node_count`).
  - Computes Weakly Connected Components (WCC) and Strongly Connected Components (SCC) deterministically.
  - Generates consolidated structural graph summary JSON object.

### 2.7 Ranking Comparison Layer (`backend/ranking_comparator.py`)
- **Technology**: Pure Python mathematical comparison utilities.
- **Responsibility**:
  - Validates ranking vectors (rejects malformed types, non-numeric values, NaN/inf, and node set mismatches).
  - Aligns ranking vectors onto a deterministic lexicographical node order.
  - Computes L1 distance, L2 distance, Cosine similarity (with zero-vector safety), Spearman rank correlation (with fractional average rank tie handling), Kendall tau-b correlation (handling ties), Top-k overlap (with deterministic tie-breaking), and rank displacement statistics (max, mean, per-node).

### 2.8 Experiment & Measurement Layer (`experiments/`)
- **Technology**: Pure Python experiment framework (`datasets.py`, `config.py`, `runner.py`).
- **Responsibility**:
  - Maintains controlled, static test datasets (`DATASET_A` through `DATASET_G`) and scalable graph generators (`generate_chain`, `generate_cycle`, `generate_star`).
  - Provides detailed execution instrumentation via `calculate_pagerank_detailed()` in `backend/pagerank.py` returning iteration counts, convergence booleans, and final L1 errors.
  - Supports single experiment runs (`run_experiment`), repeated stability runs (`run_repeated_experiment`), and parameter sweeps (`run_damping_sweep`, `run_tolerance_sweep`, `run_max_iterations_sweep`, `run_scalability_sweep`).
  - Integrates with Step 8 ranking comparison infrastructure for rank stability analysis against baseline parameters.
  - Serializes experiment results to machine-readable JSON files via `save_experiment_results()`.

---

## 3. Detailed Request / Response Flows

Each API endpoint in `backend/app.py` executes a specific decoupled workflow:

### 3.1 PageRank Calculation Flow (`POST /calculate`)

1. **User Action**: User clicks "Calculate PageRank" button in frontend.
2. **Client Preparation**: `script.js` extracts node IDs (`pages`) and directed edge pairs (`links`).
3. **HTTP Request**: `script.js` sends `POST /calculate` with payload `{pages, links, damping?, max_iterations?, tol?}`.
4. **Flask Handler**: `calculate()` in `app.py` receives request, validates presence of `pages` and `links`.
5. **Graph Validation**: `graph_validator.py` validates canonical graph contract rules (nodes are non-empty strings, edges are 2-element sequences `[source, target]`).
6. **Algorithm Execution**: `app.py` calls `calculate_pagerank(pages, links)` in `pagerank.py`.
7. **Sorting**: `app.py` sorts output scores descending.
8. **HTTP Response**: Returns `200 OK` with JSON object of page-to-score mappings.

### 3.2 Web Crawling & PageRank Flow (`POST /crawl`)

1. **User Action**: User enters seed URL and page limit (e.g., 5), then clicks "Find links".
2. **HTTP Request**: `script.js` sends `POST /crawl` with payload `{url, max_pages}`.
3. **Flask Handler**: `crawl()` in `app.py` receives request and validates `url`.
4. **Crawling Execution**: `app.py` calls `crawl_site(url, max_pages)` in `crawler.py` (executes bounded BFS, normalizes URLs, enforces same-host boundary, returns `pages` and `links`).
5. **Graph Validation & PageRank Execution**: Extracted graph is validated via `graph_validator.py` and passed to `calculate_pagerank()`.
6. **HTTP Response**: Returns `200 OK` with JSON body containing crawled `pages`, `links`, and computed PageRank `scores`.

### 3.3 Ranking Comparison Flow (`POST /compare`)

1. **Client Request**: Client sends `POST /compare` with payload `{ranking_a, ranking_b, top_k}`.
2. **Flask Handler**: `compare()` in `app.py` validates presence of ranking payloads.
3. **Execution**: Invokes `compare_rankings()` in `ranking_comparator.py`.
4. **Validation & Alignment**: Validates node IDs and score numerics; aligns node ordering lexicographically.
5. **Metric Calculation**: Calculates L1/L2 distance, cosine similarity, Spearman correlation, Kendall tau-b, top-k overlap, and rank displacement statistics.
6. **HTTP Response**: Returns `200 OK` with JSON containing all mathematical metrics, or `400 Bad Request` if vector validation fails.

### 3.4 Structural Graph Analysis Flow (`POST /analyze`)

1. **Client Request**: Client sends `POST /analyze` with payload `{pages, links}`.
2. **Flask Handler**: `analyze()` in `app.py` receives request and validates presence of `pages` and `links`.
3. **Graph Validation & Analysis Execution**: Validates graph via `graph_validator.py` and invokes `analyze_graph()` in `graph_analyzer.py`.
4. **HTTP Response**: Returns `200 OK` with JSON body containing structural properties (`node_count`, `edge_count`, `density`, `in_degree`, `out_degree`, `dangling_node_count`, `isolated_node_count`, `weakly_connected_components`, `strongly_connected_components`).
