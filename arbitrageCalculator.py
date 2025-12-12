import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

class APIKeysExhaustedException(Exception):
    """Raised when all API keys have been exhausted"""
    pass

americanFootballMarkets='player_assists,player_defensive_interceptions,player_field_goals,player_kicking_points,player_pass_attempts,player_pass_completions,player_pass_interceptions,player_pass_longest_completion,player_pass_rush_yds,player_pass_rush_reception_tds,player_pass_rush_reception_yds,player_pass_tds,player_pass_yds,player_pass_yds_q1,player_pats,player_receptions,player_reception_longest,player_reception_tds,player_reception_yds,player_rush_attempts,player_rush_longest,player_rush_reception_tds,player_rush_reception_yds,player_rush_tds,player_rush_yds,player_sacks,player_solo_tackles,player_tackles_assists'
basketballMarkets='player_points,player_points_q1,player_rebounds,player_rebounds_q1,player_assists,player_assists_q1,player_threes,player_blocks,player_steals,player_blocks_steals,player_turnovers,player_points_rebounds_assists,player_points_rebounds,player_points_assists,player_rebounds_assists,player_field_goals,player_frees_made,player_frees_attempts'
baseballMarkets='batter_home_runs,batter_hits,batter_total_bases,batter_rbis,batter_runs_scored,batter_hits_runs_rbis,batter_singles,batter_doubles,batter_triples,batter_walks,batter_strikeouts,batter_stolen_bases,pitcher_strikeouts,pitcher_hits_allowed,pitcher_walks,pitcher_earned_runs,pitcher_outs'
iceHockeyMarkets='player_points,player_power_play_points,player_assists,player_blocked_shots,player_shots_on_goal,player_goals,player_total_saves'
aussieRulesMarkets='player_disposals,player_afl_fantasy_points'
soccerMarkets='player_shots_on_target,player_shots,player_assists'

class APIClient:
    def __init__(self):
        load_dotenv()
        # Load multiple API keys (comma-separated) or fall back to single key
        api_keys_str = os.getenv('API_KEYS', '')
        if api_keys_str:
            self.api_keys = [k.strip() for k in api_keys_str.split(',') if k.strip()]
        else:
            single_key = os.getenv('API_KEY', '')
            self.api_keys = [single_key] if single_key else []

        if not self.api_keys:
            raise Exception("No API keys found. Set API_KEYS or API_KEY in .env file.")

        self.current_key_index = 0
        self.session = requests.Session()
        self.baseURL = 'https://api.the-odds-api.com/v4/'
        print(f"Loaded {len(self.api_keys)} API key(s)")

    def _rotate_key(self):
        """Switch to next available API key"""
        self.current_key_index += 1
        if self.current_key_index >= len(self.api_keys):
            raise APIKeysExhaustedException("All API keys exhausted. No more requests available.")
        print(f"Rotating to API key {self.current_key_index + 1}/{len(self.api_keys)}")

    def _make_request(self, endpoint, params):
        """Make request with automatic key rotation on rate limit (429)"""
        while self.current_key_index < len(self.api_keys):
            params['apiKey'] = self.api_keys[self.current_key_index]
            try:
                response = self.session.get(endpoint, params=params)

                if response.status_code == 429:
                    print(f"[Key {self.current_key_index + 1}] Rate limit hit")
                    self._rotate_key()
                    continue

                if response.status_code == 401:
                    print(f"[Key {self.current_key_index + 1}] Quota exhausted or invalid key")
                    self._rotate_key()
                    continue

                response.raise_for_status()

                remaining = response.headers.get('x-requests-remaining', 'unknown')
                print(f"[Key {self.current_key_index + 1}/{len(self.api_keys)}] Requests remaining: {remaining}")

                return response

            except requests.exceptions.RequestException as e:
                raise Exception(f"Network error: {e}") from e

        raise Exception("All API keys exhausted. No more requests available.")

    def getEvents(self, sportKey):
        endpoint = f'{self.baseURL}sports/{sportKey}/events'
        params = {}
        response = self._make_request(endpoint, params)
        return response.json()

    def getEventOdds(self, sportKey, eventId):
        endpoint = f'{self.baseURL}sports/{sportKey}/events/{eventId}/odds'
        params = {
            'regions': 'us',
            'markets': '',
            'oddsFormat': 'american'
        }
        if sportKey == 'americanfootball_nfl' or sportKey == 'americanfootball_ncaaf' or sportKey == 'americanfootball_cfl':
            params['markets'] = americanFootballMarkets
        elif sportKey == 'basketball_nba' or sportKey == 'basketball_ncaab' or sportKey == 'basketball_wbna':
            params['markets'] = basketballMarkets
        elif sportKey == 'baseball_mlb':
            params['markets'] = baseballMarkets
        elif sportKey == 'icehockey_nhl':
            params['markets'] = iceHockeyMarkets
        elif sportKey == 'aussierules_afl':
            params['markets'] = aussieRulesMarkets
        elif sportKey == 'soccer_epl' or sportKey == 'soccer_france_ligue_one' or sportKey == 'soccer_germany_bundesliga' or sportKey == 'soccer_italy_serie_a' or sportKey == 'soccer_spain_la_liga' or sportKey == 'soccer_usa_mls':
            params['markets'] = soccerMarkets

        response = self._make_request(endpoint, params)
        return response.json()

    def getSports(self):
        endpoint = f'{self.baseURL}sports/'
        params = {}
        response = self._make_request(endpoint, params)
        return response.json()

    def getSportsOdds(
        self,
        sport_key: str,
        regions: str = 'us',
        markets: str = 'h2h,spreads,totals',
        odds_format: str = 'american'
    ):
        endpoint = f'{self.baseURL}sports/{sport_key}/odds/'
        params = {
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }
        response = self._make_request(endpoint, params)
        return response.json()


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

    try:
        for sport in active_sports:
            sport_Key=sport['key']
            eventsK=client.getEvents(sportKey=sport_Key)
            for key in eventsK:
                event_id=key['id']
                event_odds_data = client.getEventOdds(sportKey=sport_Key, eventId=event_id)
                l=''
                if sport_Key=='americanfootball_nfl' or sport_Key=='americanfootball_ncaaf' or sport_Key=='americanfootball_cfl':
                    l=americanFootballMarkets.split(',')
                elif sport_Key=='basketball_nba' or sport_Key=='basketball_ncaab' or sport_Key=='basketball_wbna':
                    l=basketballMarkets.split(',')
                elif sport_Key=='baseball_mlb':
                    l=baseballMarkets.split(',')
                elif sport_Key=='icehockey_nhl':
                    l=iceHockeyMarkets.split(',')
                elif sport_Key=='aussierules_afl':
                    l=aussieRulesMarkets.split(',')
                elif sport_Key=='soccer_epl' or sport_Key=='soccer_france_ligue_one' or sport_Key=='soccer_germany_bundesliga' or sport_Key=='soccer_italy_serie_a' or sport_Key=='soccer_spain_la_liga' or sport_Key=='soccer_usa_mls':
                    l=soccerMarkets.split(',')
                odds_dictionary={ke: {} for ke in l} if l else {}
                unpaired_odds_dict={ke: {} for ke in l} if l else {}
            
                for bookmaker in event_odds_data.get('bookmakers', []):
                    for market in bookmaker['markets']:
                        market_key=market['key']
                        for outcome in market['outcomes']:
                            
                            if 'description' not in outcome:
                                break
                            outcome_name=outcome['name']
                            outcome_odds=outcome['price']
                            outcome_description=outcome['description']
                            outcome_point=outcome.get('point',None)
                            bookmaker_name = bookmaker.get('title', bookmaker.get('key', 'Unknown'))
                            player_key = f"{outcome_description}|||{outcome_point}"

                            if market_key not in odds_dictionary:
                                odds_dictionary[market_key] = {}
                            if player_key not in odds_dictionary[market_key]:
                                odds_dictionary[market_key][player_key] = {}

                            odds_dictionary[market_key][player_key][bookmaker_name] = {
                                'over/under': outcome_name,
                                'odds': outcome_odds,
                                'player_name': outcome_description,
                                'point': outcome_point
                            }

                commense_time_iso=key.get('commence_time',None)
                is_valid_time, formatted_time = parse_and_filter_event_time(commense_time_iso)
                event_info={
                    'home_team': key['home_team'],
                    'away_team': key['away_team'],
                    'sport': sport_Key,
                    'commence_time': formatted_time,
                    'is_valid_time': is_valid_time
                }
                if not event_info['is_valid_time']:
                    continue

                for market_key, market_data in odds_dictionary.items():
                    for player_key, player_props in market_data.items():
                        result = analyzePlayerPropArbitrage(player_props)
                        if result and result['roi'] > 0:
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
                                'market': f"{market_key} - {result.get('player_name', 'Unknown')}",
                                'roi': result['roi'],
                                'commence_time': event_info['commence_time'],
                                'opportunities': opportunities_dict
                            }
                            all_opportunities.append(opportunity)

            odds_data=client.getSportsOdds(sport_key=sport_Key)
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
                    'sport': sport_Key,
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

    except APIKeysExhaustedException:
        print(f"\n[!] API keys exhausted. Stopping scan and showing results found so far...")

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

def analyzePlayerPropArbitrage(player_props):
    if not player_props:
        return None

    over_odds = []
    under_odds = []
    player_name = None
    point = None

    for bookmaker, data in player_props.items():
        if data['over/under'] == 'Over':
            over_odds.append((bookmaker, data['odds']))
        else:
            under_odds.append((bookmaker, data['odds']))
        player_name = data.get('player_name')
        point = data.get('point')

    if not over_odds or not under_odds:
        return None

    best_over = max(over_odds, key=lambda x: x[1])
    best_under = max(under_odds, key=lambda x: x[1])

    arb_result = ArbitrageAgent.findArbitrage(best_over[1], best_under[1])

    if arb_result['roi'] <= 0:
        return None

    return {
        'roi': arb_result['roi'],
        'bookmakers': [best_over[0], best_under[0]],
        'odds': [best_over[1], best_under[1]],
        'outcomes': [f'Over {point}', f'Under {point}'],
        'bet_percentages': arb_result['bet_percentages'],
        'bet_amounts_1000': arb_result['bet_amounts_1000'],
        'player_name': player_name
    }



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

def testEvents():
    client=APIClient()
    sports=client.getSports()
    for sport in sports:
        key=sport['key']
        sportKeys=client.getEvents(sportKey=key)
        for k in sportKeys:
            id=k['id']
            print(client.getEventOdds(sportKey=key,eventId=id))
         

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
    #testEvents()