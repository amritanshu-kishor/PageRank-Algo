# Mini Search Engine using PageRank Algorithm

This project is a full-stack web application that simulates a search engine's ranking mechanism using the PageRank algorithm. It allows you to visually build a network of connected web pages and see how PageRank scores are iteratively computed and assigned.

## Features
- **Frontend**: A modern, dark-themed responsive UI built with HTML, CSS, and Vanilla JavaScript.
- **Graph Visualization**: Interactive, dynamic graph visualization using [Cytoscape.js](https://js.cytoscape.org/). Nodes scale dynamically based on their PageRank scores.
- **Backend API**: A Python Flask backend that handles the iterative PageRank logic without relying on built-in library solvers.
- **Real website crawler**: Enter a starting URL and crawl a small same-domain link graph to calculate PageRank from real page connections.
- **Algorithm implementation**: Implements the iterative PageRank algorithm formula: `PR(A) = (1-d)/N + d * Σ(PR(Ti)/C(Ti))`.

## Setup and Installation

### 1. Create a Local Virtual Environment

```bash
python -m venv venv
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 2. Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Optional Local Environment File

```bash
copy backend\.env.example backend\.env
```

Do not commit `.env` files. They are ignored by Git.

### 4. Start the Backend

```bash
python backend/app.py
```

Or on Windows PowerShell:

```powershell
.\start_backend.ps1
```

The backend API will run on `http://127.0.0.1:5000`.

### 5. Start the Frontend

Since this is a simple HTML/CSS/JS frontend, you can run it using any simple web server to avoid CORS issues if opening directly from the filesystem.

```bash
cd frontend
python -m http.server 8000
```

Or on Windows PowerShell from the project root:

```powershell
.\start_frontend.ps1
```

Open your browser and go to `http://localhost:8000`.

## GitHub Privacy Notes

- Do not commit `venv/`; recreate it with `python -m venv venv`.
- Do not commit `.env` files; use `backend/.env.example` as the template.
- The backend binds to `127.0.0.1` by default so it is not exposed to your network unless you change `FLASK_HOST`.

## Using Real Website Data

1. Start both the backend and frontend.
2. Open `http://localhost:8000`.
3. Paste a website URL into **Crawl Real Website**, for example:
   ```text
   https://quotes.toscrape.com
   ```
4. Choose the maximum number of pages to crawl. Keep this small, such as `5` to `12`, because real sites can have many links.
5. Click **Find Connections**.

The crawler follows same-domain links only. For example, if you enter `https://example.com`, it will only include pages on `example.com`, not external websites.

## Project Structure
- `backend/app.py`: Flask application with the REST API.
- `backend/crawler.py`: Small same-domain crawler for real website URL input.
- `backend/pagerank.py`: Core logic for the manual iterative PageRank algorithm.
- `frontend/index.html`: Main layout and UI structure.
- `frontend/style.css`: Modern card-based UI and dark theme.
- `frontend/script.js`: Graph manipulation and API communication.
