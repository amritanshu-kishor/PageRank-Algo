# System Architecture & Application Flow

This document details the baseline architecture of the PageRank-Algo application as verified during the Phase 1 — Step 1 audit.

---

## 1. System Architecture Diagram

```text
Browser User Interface
         │
         ▼
frontend/script.js (Cytoscape.js & DOM Event Handler)
         │
         ├───────────────────────────────┐
         │ HTTP POST /calculate          │ HTTP POST /crawl
         ▼                               ▼
Flask API Server (backend/app.py - Port 5000)
         │                               │
         │                               ▼
         │                       backend/crawler.py (Requests / BS4)
         │                               │
         │ ┌─────────────────────────────┘
         ▼ ▼
backend/pagerank.py (Iterative Power Method Solver)
         │
         ▼
HTTP Response JSON (Sorted PageRank Scores / Discovered Graph)
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
  - Performs same-domain Breadth-First Search (BFS) starting at a seed URL.
  - Normalizes URLs, strips fragments, strips trailing slashes, and enforces same host domain filtering.
  - Extracts hyperlink `<a>` tags and builds node list and directed edge list.

### 2.5 Algorithmic Calculation Layer (`backend/pagerank.py`)
- **Technology**: Pure Python iterative solver (no external graph libraries used for solver).
- **Responsibility**:
  - Computes PageRank scores given node list and directed edge list using the classic iterative formula:
    $$PR(A) = \frac{1-d}{N} + d \sum_{T_i \to A} \frac{PR(T_i)}{C(T_i)}$$
  - Enforces convergence check ($\sum |PR_{new} - PR_{old}| < \text{tol}$) or stops at `max_iterations`.
  - Performs post-hoc vector sum normalization.

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
