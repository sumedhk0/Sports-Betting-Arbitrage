import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime, timezone


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


def probability_to_american_odds(prob):
    """Convert decimal probability to American odds format"""
    if prob >= 0.5:
        # Negative odds (favorite)
        return -(prob * 100) / (1 - prob)
    else:
        # Positive odds (underdog)
        return ((1 - prob) * 100) / prob


def filterFutureEvents(kalshi_data):
    """Remove events that have already started or are ongoing"""
    current_time = datetime.now(timezone.utc)
    future_games = []

    for game in kalshi_data.get('games', []):
        try:
            scheduled_str = game.get('scheduled', '')
            scheduled_time = datetime.fromisoformat(scheduled_str.replace('Z', '+00:00'))
            if scheduled_time > current_time:
                future_games.append(game)
        except (ValueError, AttributeError):
            # Skip games with invalid or missing scheduled time
            continue

    return future_games


def getKalshiOdds():
    """Fetch Kalshi market data from Parse.bot API"""
    load_dotenv()
    api_key = os.getenv('PARSEBOT_API_KEY')

    if not api_key:
        raise Exception("PARSEBOT_API_KEY not found in .env file")

    url = 'https://api.parse.bot/scraper/8f119691-6b3a-4dc3-ad7a-d67893c85b9c/fetch_all_odds'
    payload = {}
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch Kalshi data: {e}") from e


def matchKalshiToOddsAPI(kalshi_game, odds_api_event):
    """Determine if a Kalshi game matches an Odds API event based on team names"""
    # Extract Kalshi teams
    kalshi_teams = {team.lower().strip() for team in kalshi_game.get('teams', [])}
    print(f"Kalshi Teams: {kalshi_teams}")
    # Extract Odds API teams
    api_teams = {
        odds_api_event.get('home_team', '').lower().strip(),
        odds_api_event.get('away_team', '').lower().strip()
    }
    print(f"API Teams: {api_teams}")
    print()
    # Match if both team sets are equal (order-independent)
    return kalshi_teams == api_teams and len(kalshi_teams) == 2


def transformKalshiToOddsDict(game):
    """Transform Kalshi game data into oddsDict format"""
    oddsDict = {
        'h2h': {},
        'spreads': {},
        'totals': {}
    }

    # Process head-to-head (moneyline) markets
    for h2h_outcome in game.get('head_to_head', []):
        outcome_name = h2h_outcome.get('outcome', '')
        yes_prob = h2h_outcome.get('yes_prob')

        if outcome_name and yes_prob is not None and 0 <= yes_prob <= 1:
            odds = probability_to_american_odds(yes_prob)
            if outcome_name not in oddsDict['h2h']:
                oddsDict['h2h'][outcome_name] = []
            oddsDict['h2h'][outcome_name].append(('Kalshi', odds))

    # Process spreads
    for spread in game.get('spreads', []):
        team = spread.get('team', '')
        line = spread.get('line')
        yes_prob = spread.get('yes_prob')

        if team and line is not None and yes_prob is not None and 0 <= yes_prob <= 1:
            odds = probability_to_american_odds(yes_prob)
            if team not in oddsDict['spreads']:
                oddsDict['spreads'][team] = []
            oddsDict['spreads'][team].append(('Kalshi', odds, float(line)))

    # Process totals (over/under)
    for total in game.get('totals', []):
        line = total.get('line')
        over_prob = total.get('over_prob')
        under_prob = total.get('under_prob')

        if line is not None:
            line_float = float(line)

            # Process Over
            if over_prob is not None and 0 <= over_prob <= 1:
                over_odds = probability_to_american_odds(over_prob)
                if 'Over' not in oddsDict['totals']:
                    oddsDict['totals']['Over'] = []
                oddsDict['totals']['Over'].append(('Kalshi', over_odds, line_float))

            # Process Under
            if under_prob is not None and 0 <= under_prob <= 1:
                under_odds = probability_to_american_odds(under_prob)
                if 'Under' not in oddsDict['totals']:
                    oddsDict['totals']['Under'] = []
                oddsDict['totals']['Under'].append(('Kalshi', under_odds, line_float))

    return oddsDict


def mergeOddsDicts(target, source):
    """Merge Kalshi odds into existing oddsDict"""
    for market_key in ['h2h', 'spreads', 'totals']:
        if market_key in source:
            for outcome, odds_list in source[market_key].items():
                if outcome not in target[market_key]:
                    target[market_key][outcome] = []
                target[market_key][outcome].extend(odds_list)


def scanAllGames():
    allBookmakers=set()
    client=APIClient()
    sports=client.getSports()
    active_sports=[
        sport for sport in sports
        if '_winner' not in sport['key'].lower() and sport.get('active', True)
    ]

    all_opportunities = []

    # Fetch Kalshi data once and filter for future events
    try:
        kalshi_data = getKalshiOdds()
        future_kalshi_games = filterFutureEvents(kalshi_data)
        matched_tickers = set()
    except Exception as e:
        print(f"Warning: Failed to fetch Kalshi data: {e}")
        future_kalshi_games = []
        matched_tickers = set()

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
                allBookmakers.add(bookmaker['title'])
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

            event_info = {
                'home_team': event['home_team'],
                'away_team': event['away_team'],
                'sport': key
            }

            # Try to find matching Kalshi game and merge data
            matching_kalshi = None
            for kalshi_game in future_kalshi_games:
                
                if matchKalshiToOddsAPI(kalshi_game, event):
                    matching_kalshi = kalshi_game
                    break

            # If match found, merge Kalshi odds
            if matching_kalshi:
                kalshi_odds = transformKalshiToOddsDict(matching_kalshi)
                mergeOddsDicts(oddsDict, kalshi_odds)
                allBookmakers.add('Kalshi')
                matched_tickers.add(matching_kalshi.get('event_ticker', ''))

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
        print(f"Sport: {opp['sport']}")
        print(f"Market: {opp['market']}")
        print(f"Bet Distribution:")
        for outcome, details in opp['opportunities'].items():
            print(f"  {outcome}: {details['odds']} at {details['bookmaker']} | Bet: {details['bet_percentage']:.2f}% (${details['bet_amount_1000']:.2f})")
        print(f"{'-'*70}\n")

    print("All Bookmakers Encountered:")
    for bookmaker in allBookmakers:
        print(bookmaker)
    
    
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
    
    

def testNewAPI():
    load_dotenv()
    api_key = os.getenv('PARSEBOT_API_KEY')
    
    session = requests.Session()
    url = 'https://api.parse.bot/scraper/8f119691-6b3a-4dc3-ad7a-d67893c85b9c/fetch_all_odds'
    payload={}
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": api_key
    }

    
    resp=requests.post(url,json=payload,headers=headers)
    print(resp.json())

if __name__ == "__main__":
    scanAllGames()
    #testNewAPI()