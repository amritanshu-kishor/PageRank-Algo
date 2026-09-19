# Reproducible Baseline Test Suite Documentation

This document describes the setup, configuration, execution commands, and verification results for the `PageRank-Algo` baseline test suite established during Phase 1 — Step 2.

---

## 1. Overview & Dependencies

The baseline test suite captures the ground-truth behavior of the core PageRank algorithm and REST API endpoints without modifying existing application logic.

### Dependency Configuration
All runtime and test dependencies are declared in both [`requirements.txt`](file:///d:/pagerank/requirements.txt) (root level) and [`backend/requirements.txt`](file:///d:/pagerank/backend/requirements.txt):

```text
Flask==3.0.2
Flask-Cors==4.0.0
networkx==3.2.1
numpy==1.26.4
beautifulsoup4==4.12.3
requests==2.31.0
pytest==9.1.1
```

---

## 2. Environment Setup & Installation

To run the baseline test suite in a fresh environment:

```bash
# 1. Create a fresh virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 3. Install project and test dependencies
pip install -r requirements.txt
```

---

## 3. Supported Test Execution Commands

Both standard test discovery tools are fully supported and verified:

### Primary Test Command (`pytest`)
```bash
python -m pytest -q
```
or:
```bash
pytest -v tests/
```

### Alternative Test Command (`unittest`)
```bash
python -m unittest discover tests
```

---

## 4. Test Suite Structure

```text
tests/
├── __init__.py
├── test_pagerank_baseline.py
├── test_api_baseline.py
└── fixtures/
    ├── simple_graph.json
    ├── cycle_graph.json
    ├── dangling_graph.json
    ├── disconnected_graph.json
    ├── self_loop_graph.json
    ├── duplicate_edge_graph.json
    └── empty_graph.json
```

---

## 5. Verification Results in Clean Environment

A fresh temporary virtual environment (`test_env`) was created, dependencies were installed via `pip install -r requirements.txt`, and the full suite was executed across multiple clean runs.

### Results Summary

| Field | Verification Outcome |
| ----- | -------------------- |
| **Clean Environment Created** | `test_env` (Fresh Python 3.10 virtual environment) |
| **Dependency Installation** | `pip install -r requirements.txt` (Exited 0) |
| **Total Test Count** | 16 tests |
| **First Run Result (`python -m pytest -q`)** | `16 passed in 3.14s` |
| **Second Run Result (`python -m pytest -q`)** | `16 passed in 3.03s` (Identical deterministic result) |
| **Unittest Entry Point (`python -m unittest discover tests`)** | `Ran 16 tests in 2.73s - OK` |
| **Pytest Verbose Entry Point (`pytest -v tests/`)** | `16 passed in 3.06s` |
| **Source Code Modifications** | 0 application logic changes |

---

## 6. Reproducibility Fixes Applied

1. **Declared Test Dependency**: Added `pytest==9.1.1` to [`backend/requirements.txt`](file:///d:/pagerank/backend/requirements.txt).
2. **Created Root Requirements**: Created root [`requirements.txt`](file:///d:/pagerank/requirements.txt) to enable standard `pip install -r requirements.txt` execution from the repository root.
3. **Clean Environment Validation**: Verified that a clean virtual environment without pre-existing packages builds and executes all 16 baseline tests cleanly without `ModuleNotFoundError`.
