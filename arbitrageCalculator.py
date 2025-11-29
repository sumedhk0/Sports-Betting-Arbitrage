import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv


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


        

def scanAllGames():
    client=APIClient()
    sports=client.getSports()
    active_sports=[
        sport for sport in sports
        if '_winner' not in sport['key'].lower() and sport.get('active', True)
    ]

    # Initialize list to collect all arbitrage opportunities
    all_opportunities = []

    for sport in active_sports:
        key=sport['key']
        
        odds_data=client.getSportsOdds(sport_key=key)
        for event in odds_data:

            # Initialize oddsDict with market types as keys
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

                        # Get point value if it exists (for spreads and totals)
                        point = outcome.get('point', None)

                        # Initialize outcome list if it doesn't exist
                        if market_key in oddsDict:
                            if outcome_name not in oddsDict[market_key]:
                                oddsDict[market_key][outcome_name] = []

                            # Store odds with bookmaker and point (if applicable)
                            if point is not None:
                                oddsDict[market_key][outcome_name].append((bookmaker['title'], odds, point))
                            else:
                                oddsDict[market_key][outcome_name].append((bookmaker['title'], odds))

            # Analyze all markets for this event
            event_info = {
                'home_team': event['home_team'],
                'away_team': event['away_team'],
                'sport': key
            }

            # Collect opportunities from ALL markets
            for market_key, market_data in oddsDict.items():
                result = analyzeMarketArbitrage(market_data, market_key)

                if result:
                    # Format the opportunity
                    opportunities_dict = {}
                    for i, outcome in enumerate(result['outcomes']):
                        opportunities_dict[outcome] = {
                            'bookmaker': result['bookmakers'][i],
                            'odds': result['odds'][i]
                        }

                    opportunity = {
                        'event': f"{event_info['home_team']} vs {event_info['away_team']}",
                        'sport': event_info['sport'],
                        'market': market_key,
                        'roi': result['roi'],
                        'opportunities': opportunities_dict
                    }
                    all_opportunities.append(opportunity)

    # Sort all opportunities by ROI in descending order and select top 3
    all_opportunities.sort(key=lambda x: x['roi'], reverse=True)
    top_3 = all_opportunities[:3]

    # Print summary of top 3 opportunities
    print(f"\n{'='*70}")
    print(f"TOP 3 ARBITRAGE OPPORTUNITIES (from {len(all_opportunities)} total)")
    print(f"{'='*70}\n")

    for rank, opp in enumerate(top_3, 1):
        print(f"#{rank} - ROI: {opp['roi']:.2f}%")
        print(f"Event: {opp['event']}")
        print(f"Sport: {opp['sport']}")
        print(f"Market: {opp['market']}")
        print(f"Bet Distribution:")
        for outcome, details in opp['opportunities'].items():
            print(f"  {outcome}: {details['odds']} at {details['bookmaker']}")
        print(f"{'-'*70}\n")

    # Return only the top 3 opportunities
    return top_3


def analyzeMarketArbitrage(market_data, market_key):
    """
    Analyze a single market to find the best arbitrage opportunity.

    Args:
        market_data: Dict with outcomes as keys and list of (bookmaker, odds, point) tuples
        market_key: The market type (e.g., 'h2h', 'spreads', 'totals')

    Returns:
        Dict with roi, bookmakers_used, odds_used, outcome_names, or None if insufficient data
    """
    if not market_data or len(market_data) < 2:
        return None

    # For spreads and totals, we need to group by point value
    if market_key in ['spreads', 'totals']:
        # Group outcomes by point value
        point_groups = {}
        for outcome, odds_list in market_data.items():
            for bookmaker, odds, point in odds_list:
                if point not in point_groups:
                    point_groups[point] = {}
                if outcome not in point_groups[point]:
                    point_groups[point][outcome] = []
                point_groups[point][outcome].append((bookmaker, odds))

        # Find best arbitrage across all point groups
        best_result = None
        best_roi = float('-inf')

        for point, outcomes in point_groups.items():
            if len(outcomes) < 2:
                continue

            # Find best odds for each outcome in this point group
            best_odds = []
            bookmakers_used = []
            outcome_names = []

            for outcome, odds_list in outcomes.items():
                # Find highest odds for this outcome
                best_odd = max(odds_list, key=lambda x: x[1])
                best_odds.append(best_odd[1])
                bookmakers_used.append(best_odd[0])
                outcome_names.append(f"{outcome} {point}")

            if len(best_odds) >= 2:
                roi = ArbitrageAgent.findArbitrage(*best_odds)
                if roi > best_roi:
                    best_roi = roi
                    best_result = {
                        'roi': roi,
                        'bookmakers': bookmakers_used,
                        'odds': best_odds,
                        'outcomes': outcome_names
                    }

        return best_result

    else:
        # For h2h and other markets without points
        best_odds = []
        bookmakers_used = []
        outcome_names = []

        for outcome, odds_list in market_data.items():
            if not odds_list:
                continue
            # Find highest odds for this outcome (odds_list contains (bookmaker, odds) tuples)
            best_odd = max(odds_list, key=lambda x: x[1])
            best_odds.append(best_odd[1])
            bookmakers_used.append(best_odd[0])
            outcome_names.append(outcome)

        if len(best_odds) < 2:
            return None

        roi = ArbitrageAgent.findArbitrage(*best_odds)
        return {
            'roi': roi,
            'bookmakers': bookmakers_used,
            'odds': best_odds,
            'outcomes': outcome_names
        }


def findBestArbitrageForEvent(oddsDict, event_info):
    """
    Find the best arbitrage opportunity across all markets for a single event.

    Args:
        oddsDict: Dict with market keys and their corresponding market data
        event_info: Dict with event details (home_team, away_team, sport)

    Returns:
        Dict with best arbitrage opportunity details, or None if no opportunities found
    """
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

    # Format the result
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
        return roi
    
    

if __name__ == "__main__":
    scanAllGames()