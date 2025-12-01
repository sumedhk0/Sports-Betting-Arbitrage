import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone


class APIClient:
    def __init__(self):
        load_dotenv()
        self.api_key= os.getenv('API_KEY')
        self.session= requests.Session()
        self.baseURL= 'https://api.the-odds-api.com/v4/'

    
    
    def getSports(self):
        endpoint=f'{self.baseURL}sports/'
        params= {
            'apiKey': self.api_key
        }
        
        
        try:
            response=self.session.get(endpoint, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}") from e
        
    def getSportsOdds(
        self,
        sport_key: str,
        regions: str = 'us',
        markets: str = 'h2h,spreads,totals',
        odds_format: str= 'american'
    ):
        endpoint=f'{self.baseURL}sports/{sport_key}/odds/'
        params= {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }
        
        
        
        try:
            
            response=self.session.get(endpoint, params=params)
            response.raise_for_status()
            remaining = response.headers.get('x-requests-remaining')
            print(f"API requests remaining: {remaining}")

            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Invalid API key. Please check your ODDS_API_KEY in .env file.") from e
            elif response.status_code == 429:
                raise Exception("API rate limit exceeded. Please wait before making more requests.") from e
            else:
                raise Exception(f"API request failed: {e}") from e

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}") from e


def parse_and_filter_event_time(commence_time_iso: str, minutes_buffer: int = 10):
    """
    Parse ISO 8601 datetime string and determine if event is still valid for betting.

    Filters out:
    - Games that have already started
    - Games starting within the next N minutes (buffer for order placement)

    Args:
        commence_time_iso: ISO 8601 formatted datetime from API (e.g., "2025-12-01T19:30:00Z")
        minutes_buffer: Minutes to exclude before game start (default 10 minutes)

    Returns:
        Tuple of (is_valid: bool, formatted_time: str)
        - is_valid: True if event is in the future and beyond buffer window
        - formatted_time: Event time in local timezone, 12-hour format with date
    """
    try:
        # Handle missing data
        if not commence_time_iso:
            return False, "Time unavailable"

        # Normalize ISO 8601 format (handle both 'Z' and explicit +00:00)
        normalized = commence_time_iso.replace('Z', '+00:00')

        # Parse UTC timestamp
        utc_time = datetime.fromisoformat(normalized)

        # Convert to local system timezone
        local_time = utc_time.astimezone()

        # Get current time with buffer applied
        now = datetime.now(timezone.utc).astimezone()
        buffer_time = now + timedelta(minutes=minutes_buffer)

        # Check if event is valid (hasn't started and beyond buffer)
        is_valid = local_time > buffer_time

        # Format time: "2025-12-01 07:30 PM"
        formatted_time = local_time.strftime("%Y-%m-%d %I:%M %p")

        return is_valid, formatted_time

    except (ValueError, AttributeError, TypeError) as e:
        # If parsing fails, mark as invalid
        return False, "Time unavailable"




def scanAllGames():
    client=APIClient()
    sports=client.getSports()
    active_sports=[
        sport for sport in sports
        if '_winner' not in sport['key'].lower() and sport.get('active', True)
    ]

    all_opportunities = []

    for sport in active_sports:
        key=sport['key']
        
        odds_data=client.getSportsOdds(sport_key=key)
        for event in odds_data:

            oddsDict = {
                'h2h': {},
                'spreads': {},
                'totals': {}
            }

            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    market_key = market['key']

                    for outcome in market['outcomes']:
                        outcome_name = outcome['name']
                        odds = outcome['price']

                        point = outcome.get('point', None)

                        if market_key in oddsDict:
                            if outcome_name not in oddsDict[market_key]:
                                oddsDict[market_key][outcome_name] = []

                            if point is not None:
                                oddsDict[market_key][outcome_name].append((bookmaker['title'], odds, point))
                            else:
                                oddsDict[market_key][outcome_name].append((bookmaker['title'], odds))

            # Extract commence_time from API response
            commence_time_iso = event.get('commence_time', None)

            # Parse, filter, and format the time
            is_valid_time, formatted_time = parse_and_filter_event_time(commence_time_iso)

            event_info = {
                'home_team': event['home_team'],
                'away_team': event['away_team'],
                'sport': key,
                'commence_time': formatted_time,
                'is_valid_time': is_valid_time
            }

            # Skip events that don't meet time filtering criteria
            if not event_info['is_valid_time']:
                continue

            for market_key, market_data in oddsDict.items():
                result = analyzeMarketArbitrage(market_data, market_key)

                if result:
                    opportunities_dict = {}
                    for i, outcome in enumerate(result['outcomes']):
                        opportunities_dict[outcome] = {
                            'bookmaker': result['bookmakers'][i],
                            'odds': result['odds'][i],
                            'bet_percentage': result['bet_percentages'][i],
                            'bet_amount_1000': result['bet_amounts_1000'][i]
                        }

                    opportunity = {
                        'event': f"{event_info['home_team']} vs {event_info['away_team']}",
                        'sport': event_info['sport'],
                        'market': market_key,
                        'roi': result['roi'],
                        'commence_time': event_info['commence_time'],
                        'opportunities': opportunities_dict
                    }
                    all_opportunities.append(opportunity)

    all_opportunities.sort(key=lambda x: x['roi'], reverse=True)
    top_3 = all_opportunities[:3]

    print(f"\n{'='*70}")
    print(f"TOP 3 ARBITRAGE OPPORTUNITIES (from {len(all_opportunities)} total)")
    print(f"{'='*70}\n")

    for rank, opp in enumerate(top_3, 1):
        print(f"#{rank} - ROI: {opp['roi']:.2f}%")
        print(f"Event: {opp['event']}")
        print(f"Starts: {opp['commence_time']}")
        print(f"Sport: {opp['sport']}")
        print(f"Market: {opp['market']}")
        print(f"Bet Distribution:")
        for outcome, details in opp['opportunities'].items():
            print(f"  {outcome}: {details['odds']} at {details['bookmaker']} | Bet: {details['bet_percentage']:.2f}% (${details['bet_amount_1000']:.2f})")
        print(f"{'-'*70}\n")

    return top_3


def analyzeMarketArbitrage(market_data, market_key):
    if not market_data or len(market_data) < 2:
        return None

    if market_key in ['spreads', 'totals']:
        point_groups = {}
        for outcome, odds_list in market_data.items():
            for bookmaker, odds, point in odds_list:
                if point not in point_groups:
                    point_groups[point] = {}
                if outcome not in point_groups[point]:
                    point_groups[point][outcome] = []
                point_groups[point][outcome].append((bookmaker, odds))

        best_result = None
        best_roi = float('-inf')

        for point, outcomes in point_groups.items():
            if len(outcomes) < 2:
                continue

            best_odds = []
            bookmakers_used = []
            outcome_names = []

            for outcome, odds_list in outcomes.items():
                best_odd = max(odds_list, key=lambda x: x[1])
                best_odds.append(best_odd[1])
                bookmakers_used.append(best_odd[0])
                outcome_names.append(f"{outcome} {point}")

            if len(best_odds) >= 2:
                arb_result = ArbitrageAgent.findArbitrage(*best_odds)
                if arb_result['roi'] > best_roi:
                    best_roi = arb_result['roi']
                    best_result = {
                        'roi': arb_result['roi'],
                        'bookmakers': bookmakers_used,
                        'odds': best_odds,
                        'outcomes': outcome_names,
                        'bet_percentages': arb_result['bet_percentages'],
                        'bet_amounts_1000': arb_result['bet_amounts_1000']
                    }

        return best_result

    else:
        best_odds = []
        bookmakers_used = []
        outcome_names = []

        for outcome, odds_list in market_data.items():
            if not odds_list:
                continue
            best_odd = max(odds_list, key=lambda x: x[1])
            best_odds.append(best_odd[1])
            bookmakers_used.append(best_odd[0])
            outcome_names.append(outcome)

        if len(best_odds) < 2:
            return None

        arb_result = ArbitrageAgent.findArbitrage(*best_odds)
        return {
            'roi': arb_result['roi'],
            'bookmakers': bookmakers_used,
            'odds': best_odds,
            'outcomes': outcome_names,
            'bet_percentages': arb_result['bet_percentages'],
            'bet_amounts_1000': arb_result['bet_amounts_1000']
        }


def findBestArbitrageForEvent(oddsDict, event_info):
    best_opportunity = None
    best_roi = float('-inf')
    best_market = None

    for market_key, market_data in oddsDict.items():
        result = analyzeMarketArbitrage(market_data, market_key)

        if result and result['roi'] > best_roi:
            best_roi = result['roi']
            best_market = market_key
            best_opportunity = result

    if best_opportunity is None:
        return None

    opportunities_dict = {}
    for i, outcome in enumerate(best_opportunity['outcomes']):
        opportunities_dict[outcome] = {
            'bookmaker': best_opportunity['bookmakers'][i],
            'odds': best_opportunity['odds'][i]
        }

    return {
        'event': f"{event_info['home_team']} vs {event_info['away_team']}",
        'sport': event_info['sport'],
        'market': best_market,
        'roi': best_roi,
        'opportunities': opportunities_dict
    }


class ArbitrageAgent():
    def findArbitrage(odds1,odds2,odds3=None):
        def american_to_decimal(american_odds):
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1
        decimal_odds=[american_to_decimal(odds) for odds in [odds1,odds2,odds3] if odds is not None]
        inverse_sum=sum(1/odds for odds in decimal_odds)
        roi=(1 - inverse_sum) * 100
        bet_percentages=[(1/odds) / inverse_sum * 100 for odds in decimal_odds]
        bet_amounts_1000=[pct * 10 for pct in bet_percentages]
        return {
            'roi': roi,
            'bet_percentages': bet_percentages,
            'bet_amounts_1000': bet_amounts_1000
        }
    
    

if __name__ == "__main__":
    scanAllGames()