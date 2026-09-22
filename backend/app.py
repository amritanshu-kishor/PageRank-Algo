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
        if not data or 'url' not in data:
            return jsonify({'error': 'Invalid input format. Expected url.'}), 400

        graph = crawl_site(data['url'], data.get('max_pages', 12))
        if not graph['pages']:
            return jsonify({'error': 'No crawlable pages found for that URL.'}), 400

        scores = calculate_pagerank(graph['pages'], graph['links'])
        sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1], reverse=True))

        return jsonify({
            'pages': graph['pages'],
            'links': graph['links'],
            'scores': sorted_scores
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
