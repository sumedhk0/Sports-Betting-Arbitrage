"""GET /api/sports - Return list of active sports."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from lib.api_client import APIClient, APIError

app = Flask(__name__)


@app.route('/api/sports', methods=['GET'])
def get_sports():
    try:
        client = APIClient()
        result = client.get_sports()

        # Filter out winner markets and inactive sports
        sports = [
            {
                'key': sport['key'],
                'title': sport.get('title', sport['key']),
                'group': sport.get('group', 'Other'),
                'active': sport.get('active', True)
            }
            for sport in result['data']
            if '_winner' not in sport['key'].lower() and sport.get('active', True)
        ]

        # Sort by group then title
        sports.sort(key=lambda x: (x['group'], x['title']))

        response = jsonify({
            'sports': sports,
            'remaining_credits': result['remaining']
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except APIError as e:
        response = jsonify({'error': str(e)})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        response = jsonify({'error': f'Internal error: {str(e)}'})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
