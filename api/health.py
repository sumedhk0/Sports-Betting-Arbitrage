"""GET /api/health - Health check endpoint."""

import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/api/health', methods=['GET'])
def health_check():
    api_key_configured = bool(os.environ.get('API_KEY'))

    response = jsonify({
        'status': 'healthy',
        'api_key_configured': api_key_configured
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
