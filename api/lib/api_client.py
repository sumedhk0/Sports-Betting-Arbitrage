"""API client for The Odds API - serverless-friendly version."""

import os
import requests
from typing import Dict, List, Optional, Any

from .markets import get_markets_for_sport


class APIError(Exception):
    """Custom exception for API errors."""
    pass


class APIClient:
    """Client for The Odds API with simplified serverless-friendly design."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API client.

        Args:
            api_key: The Odds API key. Falls back to API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('API_KEY')
        if not self.api_key:
            raise APIError("API_KEY not configured")

        self.session = requests.Session()
        self.base_url = 'https://api.the-odds-api.com/v4/'
        self.remaining_credits = None

    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make an API request.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Dict with 'data' and 'remaining' keys
        """
        params = params or {}
        params['apiKey'] = self.api_key

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=25)

            if response.status_code == 429:
                raise APIError("API rate limit exceeded. Try again later.")

            if response.status_code == 401:
                raise APIError("Invalid API key.")

            response.raise_for_status()

            self.remaining_credits = response.headers.get('x-requests-remaining', 'unknown')

            return {
                'data': response.json(),
                'remaining': self.remaining_credits
            }

        except requests.exceptions.Timeout:
            raise APIError("API request timed out.")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")

    def get_sports(self) -> Dict:
        """
        Get list of available sports.

        Returns:
            Dict with sports data and remaining credits
        """
        return self._request('sports/')

    def get_events(self, sport_key: str) -> Dict:
        """
        Get events for a specific sport.

        Args:
            sport_key: Sport identifier (e.g., 'basketball_nba')

        Returns:
            Dict with events data and remaining credits
        """
        return self._request(f'sports/{sport_key}/events')

    def get_event_odds(self, sport_key: str, event_id: str, bookmakers: str = None) -> Dict:
        """
        Get odds for a specific event with player props.

        Args:
            sport_key: Sport identifier
            event_id: Event identifier
            bookmakers: Comma-separated bookmaker keys

        Returns:
            Dict with odds data and remaining credits
        """
        markets = get_markets_for_sport(sport_key)

        params = {
            'markets': markets,
            'oddsFormat': 'american'
        }

        if bookmakers:
            params['bookmakers'] = bookmakers
        else:
            params['regions'] = 'us'

        return self._request(f'sports/{sport_key}/events/{event_id}/odds', params)

    def get_sports_odds(
        self,
        sport_key: str,
        bookmakers: str = None,
        markets: str = 'h2h,spreads,totals',
        odds_format: str = 'american'
    ) -> Dict:
        """
        Get odds for all events in a sport.

        Args:
            sport_key: Sport identifier
            bookmakers: Comma-separated bookmaker keys
            markets: Comma-separated market types
            odds_format: Odds format (american/decimal)

        Returns:
            Dict with odds data and remaining credits
        """
        params = {
            'markets': markets,
            'oddsFormat': odds_format
        }

        if bookmakers:
            params['bookmakers'] = bookmakers
        else:
            params['regions'] = 'us'

        return self._request(f'sports/{sport_key}/odds/', params)
