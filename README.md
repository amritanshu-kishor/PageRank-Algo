# Mini Search Engine using PageRank Algorithm

This project is a full-stack web application that simulates a search engine's ranking mechanism using the PageRank algorithm. It allows you to visually build a network of connected web pages, including real website URLs, and see how PageRank scores are iteratively computed and assigned.

## Features

- **Frontend**: A modern, dark-themed responsive UI built with HTML, CSS, and Vanilla JavaScript.
- **Graph Visualization**: Interactive, dynamic graph visualization using [Cytoscape.js](https://js.cytoscape.org/). Nodes scale dynamically based on their PageRank scores.
- **Backend API**: A Python Flask backend that handles the iterative PageRank logic without relying on built-in library solvers.
- **Website URL support**: You can add real website URLs as pages/nodes and manually define the directed URL-to-URL connections.
- **Correct PageRank logic**: The PageRank calculation is implemented with the iterative formula `PR(A) = (1-d)/N + d * sum(PR(Ti)/C(Ti))`.

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

## Using Real Website URLs

You can use real website URLs in the graph, but the connections between those URLs should be entered manually for a clear and controlled PageRank demo.

1. Start both the backend and frontend.
2. Open `http://localhost:8000`.
3. Add each website URL as a webpage/node, for example:
   ```text
   https://example.com
   https://example.com/about
   https://example.com/contact
   ```
4. Manually add directed connections between URLs. For example, if the home page links to the about page:
   ```text
   Source: https://example.com
   Target: https://example.com/about
   ```
5. Click **Calculate PageRank**.

The application does not need the website's IP address. It needs page URLs and directed link connections. Once those pages and links are supplied, the PageRank algorithm logic is correct and computes rankings from that graph.

## Project Structure

- `backend/app.py`: Flask application with the REST API.
- `backend/crawler.py`: Experimental same-domain crawler for URL input.
- `backend/pagerank.py`: Core logic for the manual iterative PageRank algorithm.
- `frontend/index.html`: Main layout and UI structure.
- `frontend/style.css`: Modern card-based UI and dark theme.
- `frontend/script.js`: Graph manipulation and API communication.
