"""POST /api/scan - Scan a sport for arbitrage opportunities."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request
from lib.api_client import APIClient, APIError
from lib.arbitrage import (
    parse_and_filter_event_time,
    analyze_player_prop_arbitrage,
    analyze_market_arbitrage
)
from lib.markets import get_markets_for_sport

app = Flask(__name__)


@app.route('/api/scan', methods=['POST', 'OPTIONS'])
def scan():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        body = request.get_json() or {}

        sport_key = body.get('sport_key')
        bookmakers_list = body.get('bookmakers', [])
        include_props = body.get('include_props', True)

        if not sport_key:
            response = jsonify({'error': 'sport_key is required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        if len(bookmakers_list) < 2:
            response = jsonify({'error': 'At least 2 bookmakers are required'})
            response.status_code = 400
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        bookmakers_str = ','.join(bookmakers_list)
        client = APIClient()
        all_opportunities = []

        # 1. Get main market odds (h2h, spreads, totals)
        main_odds_result = client.get_sports_odds(
            sport_key=sport_key,
            bookmakers=bookmakers_str
        )

        for event in main_odds_result['data']:
            commence_time_iso = event.get('commence_time')
            is_valid_time, formatted_time = parse_and_filter_event_time(commence_time_iso)

            if not is_valid_time:
                continue

            event_info = {
                'home_team': event['home_team'],
                'away_team': event['away_team'],
                'sport': sport_key,
                'commence_time': formatted_time
            }

            # Build odds dictionary
            odds_dict = {'h2h': {}, 'spreads': {}, 'totals': {}}

            for bookmaker in event.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    market_key = market['key']
                    if market_key not in odds_dict:
                        continue

                    for outcome in market.get('outcomes', []):
                        outcome_name = outcome['name']
                        odds = outcome['price']
                        point = outcome.get('point')

                        if outcome_name not in odds_dict[market_key]:
                            odds_dict[market_key][outcome_name] = []

                        if point is not None:
                            odds_dict[market_key][outcome_name].append(
                                (bookmaker['title'], odds, point)
                            )
                        else:
                            odds_dict[market_key][outcome_name].append(
                                (bookmaker['title'], odds)
                            )

            # Analyze each market
            for market_key, market_data in odds_dict.items():
                result = analyze_market_arbitrage(market_data, market_key)

                if result and result['roi'] > 0:
                    opportunity = format_opportunity(event_info, market_key, result)
                    all_opportunities.append(opportunity)

        # 2. Get player prop odds if enabled and markets exist
        prop_markets = get_markets_for_sport(sport_key)
        if include_props and prop_markets:
            try:
                events_result = client.get_events(sport_key)

                for event_data in events_result['data'][:10]:
                    commence_time_iso = event_data.get('commence_time')
                    is_valid_time, formatted_time = parse_and_filter_event_time(commence_time_iso)

                    if not is_valid_time:
                        continue

                    event_id = event_data['id']
                    event_info = {
                        'home_team': event_data['home_team'],
                        'away_team': event_data['away_team'],
                        'sport': sport_key,
                        'commence_time': formatted_time
                    }

                    try:
                        props_result = client.get_event_odds(
                            sport_key, event_id, bookmakers_str
                        )

                        market_list = prop_markets.split(',')
                        props_dict = {m: {} for m in market_list}

                        for bookmaker in props_result['data'].get('bookmakers', []):
                            for market in bookmaker.get('markets', []):
                                market_key = market['key']
                                if market_key not in props_dict:
                                    continue

                                for outcome in market.get('outcomes', []):
                                    if 'description' not in outcome:
                                        continue

                                    outcome_name = outcome['name']
                                    outcome_odds = outcome['price']
                                    outcome_description = outcome['description']
                                    outcome_point = outcome.get('point')
                                    bookmaker_name = bookmaker.get('title', bookmaker.get('key', 'Unknown'))

                                    player_key = f"{outcome_description}|||{outcome_point}"

                                    if player_key not in props_dict[market_key]:
                                        props_dict[market_key][player_key] = {}

                                    props_dict[market_key][player_key][bookmaker_name] = {
                                        'over/under': outcome_name,
                                        'odds': outcome_odds,
                                        'player_name': outcome_description,
                                        'point': outcome_point
                                    }

                        for market_key, market_data in props_dict.items():
                            for player_key, player_props in market_data.items():
                                result = analyze_player_prop_arbitrage(player_props)

                                if result and result['roi'] > 0:
                                    opportunity = format_prop_opportunity(
                                        event_info, market_key, result
                                    )
                                    all_opportunities.append(opportunity)

                    except Exception:
                        continue

            except Exception:
                pass

        # Sort by ROI descending
        all_opportunities.sort(key=lambda x: x['roi'], reverse=True)

        response = jsonify({
            'opportunities': all_opportunities[:50],
            'total_found': len(all_opportunities),
            'remaining_credits': client.remaining_credits
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


def format_opportunity(event_info, market_key, result):
    """Format a main market opportunity."""
    bets = []
    for i, outcome in enumerate(result['outcomes']):
        bets.append({
            'outcome': outcome,
            'bookmaker': result['bookmakers'][i],
            'odds': result['odds'][i],
            'bet_percentage': round(result['bet_percentages'][i], 2),
            'bet_amount_100': round(result['bet_percentages'][i], 2)
        })

    return {
        'event': f"{event_info['home_team']} vs {event_info['away_team']}",
        'sport': event_info['sport'],
        'market': market_key,
        'roi': round(result['roi'], 2),
        'commence_time': event_info['commence_time'],
        'bets': bets
    }


def format_prop_opportunity(event_info, market_key, result):
    """Format a player prop opportunity."""
    bets = []
    for i, outcome in enumerate(result['outcomes']):
        bets.append({
            'outcome': outcome,
            'bookmaker': result['bookmakers'][i],
            'odds': result['odds'][i],
            'bet_percentage': round(result['bet_percentages'][i], 2),
            'bet_amount_100': round(result['bet_percentages'][i], 2)
        })

    player_name = result.get('player_name', 'Unknown')
    market_display = f"{market_key} - {player_name}"

    return {
        'event': f"{event_info['home_team']} vs {event_info['away_team']}",
        'sport': event_info['sport'],
        'market': market_display,
        'roi': round(result['roi'], 2),
        'commence_time': event_info['commence_time'],
        'bets': bets
    }
