# System Architecture & Application Flow

This document details the baseline architecture of the PageRank-Algo application as verified during the Phase 1 — Step 1 audit.

---

## 1. System Architecture Diagram

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
         │
         ▼
backend/graph_analyzer.py (Structural Graph Analysis Layer)
         │
         ▼
backend/pagerank.py (Iterative Power Method Solver)
         │
         ▼
HTTP Response JSON (Sorted PageRank Scores + Structural Analysis + Graph Data)
         │
         ▼
frontend/script.js (Cytoscape Graph Animation & UI Rendering)
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
  - Animates graph nodes (resizing diameter from 42px to 96px based on PageRank score ratio) and highlights top-ranked node (`#f0a202`) and top inbound edges.

### 2.3 HTTP API Layer (`backend/app.py`)
- **Technology**: Python 3.10+, Flask 3.0.2, Flask-CORS 4.0.0.
- **Responsibility**:
  - Exposes RESTful JSON endpoints (`/calculate` and `/crawl`).
  - Manages Cross-Origin Resource Sharing (CORS) headers for local frontend access (`http://localhost:8000`, `http://127.0.0.1:8000`).
  - Validates request payloads and formats error responses.
  - Invokes core algorithm and crawler modules.

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

---

## 3. Detailed Request / Response Flows

### 3.1 PageRank Calculation Flow (`POST /calculate`)

1. **User Action**: User clicks "Calculate PageRank" button in frontend.
2. **Client Preparation**: `script.js` extracts node IDs (`cy.nodes().map(n => n.id())`) and edge pairs (`cy.edges().map(e => [e.data('source'), e.data('target')])`).
3. **HTTP Request**: `script.js` sends `POST http://127.0.0.1:5000/calculate` with JSON body:
   ```json
   {
     "pages": ["A", "B", "C"],
     "links": [["A", "B"], ["B", "C"]]
   }
   ```
4. **Flask Handler**: `calculate()` in `app.py` receives request, validates presence of `pages` and `links`.
5. **Algorithm Execution**: `app.py` calls `calculate_pagerank(pages, links)` in `pagerank.py`.
6. **Sorting**: `app.py` sorts output scores descending: `{"C": 0.4744, "B": 0.3412, "A": 0.1844}`.
7. **HTTP Response**: Returns `200 OK` with JSON object of page-to-score mappings.
8. **UI Update**: `script.js` calls `displayResults()` to populate the ranking leaderboard and `animateGraph()` to scale node dimensions and highlight top authority nodes.

### 3.2 Web Crawling & PageRank Flow (`POST /crawl`)

1. **User Action**: User enters URL (e.g., `https://quotes.toscrape.com`) and page limit (e.g., 5), then clicks "Find links".
2. **HTTP Request**: `script.js` sends `POST http://127.0.0.1:5000/crawl` with JSON body:
   ```json
   {
     "url": "https://quotes.toscrape.com",
     "max_pages": 5
   }
   ```
3. **Flask Handler**: `crawl()` in `app.py` receives request and validates `url`.
4. **Crawling Execution**: `app.py` calls `crawl_site(url, max_pages)` in `crawler.py`.
   - `crawler.py` normalizes URL, fetches pages via `requests.Session`, parses HTML using `BeautifulSoup`, extracts internal same-domain links, and returns `{"pages": [...], "links": [...]}`.
5. **Algorithm Execution**: `app.py` passes extracted `graph['pages']` and `graph['links']` directly into `calculate_pagerank()`.
6. **HTTP Response**: Returns `200 OK` with JSON body:
   ```json
   {
     "pages": [...],
     "links": [...],
     "scores": { ... }
   }
   ```
7. **UI Update**: `script.js` clears existing graph, populates newly crawled nodes and edges, applies `cose` layout, displays crawl summary message, and renders ranking results.

### 3.3 Ranking Comparison Flow (`POST /compare`)

1. **Client Request**: Client sends `POST http://127.0.0.1:5000/compare` with JSON body:
   ```json
   {
     "ranking_a": {"A": 0.4, "B": 0.3, "C": 0.3},
     "ranking_b": {"A": 0.5, "B": 0.3, "C": 0.2},
     "top_k": [1, 2, 3]
   }
   ```
2. **Flask Handler**: `compare()` in `app.py` validates presence of `ranking_a` and `ranking_b`.
3. **Execution**: Invokes `compare_rankings()` in `ranking_comparator.py`.
4. **Validation & Alignment**: Validates node IDs and score numerics; aligns node ordering lexicographically.
5. **Metric Calculation**: Calculates L1/L2 distance, cosine similarity, Spearman correlation, Kendall tau-b, top-k overlap, and rank displacement statistics.
6. **HTTP Response**: Returns `200 OK` with JSON containing all mathematical metrics, or `400 Bad Request` if vector validation fails.

