"""GET /api/bookmakers - Return list of supported bookmakers."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from lib.markets import get_bookmakers_list

app = Flask(__name__)


@app.route('/api/bookmakers', methods=['GET'])
def get_bookmakers():
    try:
        bookmakers = get_bookmakers_list()

        response = jsonify({'bookmakers': bookmakers})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Cache-Control', 'public, max-age=86400')
        return response

    except Exception as e:
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
