# Crawler -> Graph Validator -> Graph Analysis -> PageRank Pipeline Integration

This document specifies the integrated end-to-end data pipeline established in Phase 1 — Step 7.

---

## 1. Pipeline Sequence & Data Flow Architecture

The system connects five hardened, deterministic components into a unified research computational pipeline:

```text
               ┌──────────────────────────────────────┐
               │    Raw Seed URL / Input Graph        │
               └──────────────────┬───────────────────┘
                                  │
                                  ▼
               ┌──────────────────────────────────────┐
               │       Crawler (crawler.py)           │
               └──────────────────┬───────────────────┘
                                  │ (raw pages & links)
                                  ▼
               ┌──────────────────────────────────────┐
               │   Graph Validator (validator.py)     │
               └──────────────────┬───────────────────┘
                                  │ (validated pages & links)
                                  ├── Failure ──► Raise ValueError (HTTP 400)
                                  ▼
               ┌──────────────────────────────────────┐
               │   Graph Analyzer (analyzer.py)       │
               └──────────────────┬───────────────────┘
                                  │ (structural graph metrics)
                                  ▼
               ┌──────────────────────────────────────┐
               │     PageRank Engine (pagerank.py)    │
               └──────────────────┬───────────────────┘
                                  │ (sorted PageRank scores)
                                  ▼
               ┌──────────────────────────────────────┐
               │    Consolidated API Result / JSON    │
               └──────────────────────────────────────┘
```

---

## 2. Boundary Contracts & Integration Rules

1. **Crawler Output**: Produces `{"pages": [...], "links": [...], "metadata": {...}}`.
2. **Validation Boundary**: All crawler output must pass through `validate_graph(pages, links)` from `graph_validator.py`. If validation fails, PageRank and Graph Analysis are NOT executed, and an HTTP 400 error is returned.
3. **Graph Analysis Layer**: Consumes the exact validated graph `(valid_pages, valid_links)` and produces structural properties (`node_count`, `edge_count`, `density`, degree maps, `dangling_node_count`, `isolated_node_count`, WCC, SCC).
4. **PageRank Engine**: Consumes the exact validated graph `(valid_pages, valid_links)` and computes normalized PageRank scores using power iteration with in-iteration dangling-node redistribution.

---

## 3. Pipeline Invariants

For every successful execution through the pipeline:

- **Invariant 1 (Node Consistency)**:
  $$\text{Set}(Pages_{\text{crawler}}) = \text{Set}(Pages_{\text{validated}}) = \text{Set}(Nodes_{\text{analysis}}) = \text{Set}(Nodes_{\text{pagerank}})$$
- **Invariant 2 (Edge Consistency)**:
  $$\text{Set}(Links_{\text{validated}}) = \text{Set}(Links_{\text{analysis}}) = \text{Set}(Links_{\text{pagerank}})$$
- **Invariant 3 (Edge Uniqueness)**: Duplicate links from crawling or input are deduplicated before reachability/ranking computations.
- **Invariant 4 (Rank Coverage)**: Every node in the validated graph receives exactly one PageRank score.
- **Invariant 5 (Rank Mass Conservation)**:
  $$\sum_{v \in \text{Pages}} PR(v) = 1.0 \quad (\pm 10^{-5})$$
- **Invariant 6 (Determinism)**: Given identical deterministic input/fixtures, repeated pipeline execution produces bitwise identical JSON results.

---

## 4. API Endpoint Integration (`POST /crawl`)

The `POST /crawl` endpoint in [`backend/app.py`](file:///d:/pagerank/backend/app.py) executes the full pipeline:

```json
{
  "pages": ["https://example.com/", "https://example.com/about"],
  "links": [["https://example.com/", "https://example.com/about"]],
  "scores": {
    "https://example.com/about": 0.574468,
    "https://example.com/": 0.425532
  },
  "analysis": {
    "node_count": 2,
    "edge_count": 1,
    "density": 0.5,
    "in_degree": {"https://example.com/": 0, "https://example.com/about": 1},
    "out_degree": {"https://example.com/": 1, "https://example.com/about": 0},
    "dangling_node_count": 1,
    "isolated_node_count": 0,
    "weakly_connected_components": [["https://example.com/", "https://example.com/about"]],
    "strongly_connected_components": [["https://example.com/"], ["https://example.com/about"]]
  },
  "metadata": {
    "pages_crawled": 2,
    "pages_failed": 0,
    "start_url": "https://example.com/",
    "max_pages": 12
  }
}
```
