import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from crawler import crawl_site
from pagerank import calculate_pagerank
from graph_validator import validate_graph, validate_pagerank_params
from graph_analyzer import analyze_graph

app = Flask(__name__)

cors_origins = os.environ.get(
    'CORS_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000'
).split(',')

# Enable CORS for the local frontend.
CORS(app, origins=[origin.strip() for origin in cors_origins if origin.strip()])

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        if not isinstance(data, dict) or 'pages' not in data or 'links' not in data:
            return jsonify({'error': 'Invalid input format. Expected pages and links.'}), 400
            
        # Validate graph structure and node/edge contracts
        pages, links = validate_graph(data['pages'], data['links'])

        # Validate optional numeric parameters if present
        params = validate_pagerank_params(
            damping=data.get('damping'),
            tol=data.get('tol'),
            max_iterations=data.get('max_iterations')
        )
        
        # Calculate PageRank
        pr_scores = calculate_pagerank(pages, links, **params)
        
        # Sort the scores in descending order
        sorted_scores = dict(sorted(pr_scores.items(), key=lambda item: item[1], reverse=True))
        
        return jsonify(sorted_scores), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()

        if not isinstance(data, dict) or 'pages' not in data or 'links' not in data:
            return jsonify({'error': 'Invalid input format. Expected pages and links.'}), 400

        summary = analyze_graph(data['pages'], data['links'])
        return jsonify(summary), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/crawl', methods=['POST'])
def crawl():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'url' not in data:
            return jsonify({'error': 'Invalid input format. Expected url.'}), 400

        # Step 1: Execute Crawler
        crawl_res = crawl_site(data['url'], data.get('max_pages', 12))
        raw_pages = crawl_res.get('pages', [])
        raw_links = crawl_res.get('links', [])

        if not raw_pages:
            return jsonify({'error': 'No crawlable pages found for that URL.'}), 400

        # Step 2: Validate Graph via Step 4 Boundary
        pages, links = validate_graph(raw_pages, raw_links)

        # Step 3: Structural Graph Analysis
        analysis_summary = analyze_graph(pages, links, validate=False)

        # Step 4: PageRank Calculation
        pr_scores = calculate_pagerank(pages, links)
        sorted_scores = dict(sorted(pr_scores.items(), key=lambda item: item[1], reverse=True))

        return jsonify({
            'pages': pages,
            'links': links,
            'scores': sorted_scores,
            'analysis': analysis_summary,
            'metadata': {
                'pages_crawled': crawl_res.get('pages_crawled', len(pages)),
                'pages_failed': crawl_res.get('pages_failed', 0),
                'start_url': crawl_res.get('start_url'),
                'max_pages': crawl_res.get('max_pages')
            }
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', '5000'))
    app.run(debug=debug, host=host, port=port)
