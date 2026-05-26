import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from crawler import crawl_site
from pagerank import calculate_pagerank

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
        
        if not data or 'pages' not in data or 'links' not in data:
            return jsonify({'error': 'Invalid input format. Expected pages and links.'}), 400
            
        pages = data['pages']
        links = data['links']
        
        # Calculate PageRank
        # Input JSON format: {"pages": ["A","B","C"], "links": [["A","B"],["B","C"],["C","A"]]}
        pr_scores = calculate_pagerank(pages, links)
        
        # Sort the scores in descending order
        sorted_scores = dict(sorted(pr_scores.items(), key=lambda item: item[1], reverse=True))
        
        return jsonify(sorted_scores), 200
        
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
