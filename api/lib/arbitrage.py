"""Arbitrage calculation and analysis functions."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any


class ArbitrageAgent:
    """Static class for calculating arbitrage opportunities."""

    @staticmethod
    def find_arbitrage(*american_odds: float) -> Dict:
        """
        Calculate arbitrage opportunity from American odds.

        Args:
            *american_odds: One American price per outcome. The caller must
                pass every outcome of the market (2 for h2h/spreads/totals,
                3 for three-way h2h, ...) or the ROI is meaningless.

        Returns:
            Dict with roi, bet_percentages, and bet_amounts_1000
        """
        def american_to_decimal(american_odds: float) -> float:
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1

        if len(american_odds) < 2:
            raise ValueError("find_arbitrage needs at least two outcomes")

        decimal_odds = [american_to_decimal(odds) for odds in american_odds]
        inverse_sum = sum(1/odds for odds in decimal_odds)
        roi = ((1 / inverse_sum) - 1) * 100
        bet_percentages = [(1/odds) / inverse_sum * 100 for odds in decimal_odds]
        bet_amounts_1000 = [pct * 10 for pct in bet_percentages]

        return {
            'roi': roi,
            'bet_percentages': bet_percentages,
            'bet_amounts_1000': bet_amounts_1000
        }


def parse_and_filter_event_time(commence_time_iso: str, minutes_buffer: int = 10) -> Tuple[bool, str]:
    """
    Parse ISO 8601 datetime string and determine if event is still valid for betting.

    Filters out:
    - Games that have already started
    - Games starting within the next N minutes (buffer for order placement)

    Args:
        commence_time_iso: ISO 8601 formatted datetime from API
        minutes_buffer: Minutes to exclude before game start (default 10)

    Returns:
        Tuple of (is_valid: bool, formatted_time: str)
    """
    try:
        if not commence_time_iso:
            return False, "Time unavailable"

        normalized = commence_time_iso.replace('Z', '+00:00')
        utc_time = datetime.fromisoformat(normalized)
        local_time = utc_time.astimezone()

        now = datetime.now(timezone.utc).astimezone()
        buffer_time = now + timedelta(minutes=minutes_buffer)

        is_valid = local_time > buffer_time
        formatted_time = local_time.strftime("%Y-%m-%d %I:%M %p")

        return is_valid, formatted_time

    except (ValueError, AttributeError, TypeError):
        return False, "Time unavailable"


def build_player_prop_odds(bookmakers: List[Dict], market_list: List[str]) -> Dict:
    """
    Collect player prop prices from an event-odds response.

    Args:
        bookmakers: The 'bookmakers' list of The Odds API event odds payload
        market_list: Player prop market keys to collect; others are ignored

    Returns:
        {market_key: {"<player>|||<point>": [entry, ...]}} where each entry
        is {'bookmaker', 'over/under', 'odds', 'player_name', 'point'}.
        There is one entry per (bookmaker, side), so a book's Over and
        Under prices both survive.
    """
    props = {market_key: {} for market_key in market_list}

    for bookmaker in bookmakers:
        bookmaker_name = bookmaker.get('title', bookmaker.get('key', 'Unknown'))
        for market in bookmaker.get('markets', []):
            market_key = market['key']
            if market_key not in props:
                continue
            for outcome in market.get('outcomes', []):
                if 'description' not in outcome:
                    continue
                point = outcome.get('point')
                player_key = f"{outcome['description']}|||{point}"
                props[market_key].setdefault(player_key, []).append({
                    'bookmaker': bookmaker_name,
                    'over/under': outcome['name'],
                    'odds': outcome['price'],
                    'player_name': outcome['description'],
                    'point': point,
                })

    return props


def analyze_player_prop_arbitrage(player_props: List[Dict]) -> Optional[Dict]:
    """
    Analyze one player prop line (a player at a point) for arbitrage.

    Args:
        player_props: Entries from build_player_prop_odds for a single line

    Returns:
        Dict with arbitrage details or None if no opportunity
    """
    if not player_props:
        return None

    over_odds = []
    under_odds = []
    player_name = None
    point = None

    for data in player_props:
        bookmaker = data['bookmaker']
        if data['over/under'] == 'Over':
            over_odds.append((bookmaker, data['odds']))
        elif data['over/under'] == 'Under':
            under_odds.append((bookmaker, data['odds']))
        player_name = data.get('player_name')
        point = data.get('point')

    if not over_odds or not under_odds:
        return None

    best_over = max(over_odds, key=lambda x: x[1])
    best_under = max(under_odds, key=lambda x: x[1])

    arb_result = ArbitrageAgent.find_arbitrage(best_over[1], best_under[1])

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


def analyze_market_arbitrage(market_data: Dict, market_key: str) -> Optional[Dict]:
    """
    Analyze a market for arbitrage opportunities.

    Args:
        market_data: Dict of outcome data with odds from various bookmakers
        market_key: Type of market (h2h, spreads, totals)

    Returns:
        Dict with arbitrage details or None if no opportunity
    """
    if not market_data or len(market_data) < 2:
        return None

    if market_key in ['spreads', 'totals']:
        # Group prices into lines where the outcomes are complementary, i.e.
        # exactly one of them wins (pushes aside). An arbitrage must cover
        # every possible result, so only such groups may be combined.
        #   totals:  Over X pairs with Under X, so the line is X.
        #   spreads: Team A -X pairs with Team B +X. Group by the point as
        #            seen from one fixed reference team, so A -1.5 and B +1.5
        #            land together while A -1.5 and B -1.5 (both lose on a
        #            one-goal game) stay apart.
        reference = min(market_data)
        line_groups = {}
        for outcome, odds_list in market_data.items():
            for item in odds_list:
                if len(item) < 3:
                    continue
                bookmaker, odds, point = item[0], item[1], item[2]
                if market_key == 'spreads' and outcome != reference:
                    line = -point
                else:
                    line = point
                line_groups.setdefault(line, {}).setdefault(outcome, []).append(
                    (bookmaker, odds, point)
                )

        best_result = None
        best_roi = float('-inf')

        for outcomes in line_groups.values():
            if len(outcomes) < len(market_data):
                # Some outcome has no price at this line: no full coverage.
                continue

            best_odds = []
            bookmakers_used = []
            outcome_names = []

            for outcome, odds_list in outcomes.items():
                bookmaker, odds, point = max(odds_list, key=lambda x: x[1])
                sign = '+' if market_key == 'spreads' and point > 0 else ''
                best_odds.append(odds)
                bookmakers_used.append(bookmaker)
                outcome_names.append(f"{outcome} {sign}{point}")

            arb_result = ArbitrageAgent.find_arbitrage(*best_odds)
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
        # H2H market
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

        arb_result = ArbitrageAgent.find_arbitrage(*best_odds)
        return {
            'roi': arb_result['roi'],
            'bookmakers': bookmakers_used,
            'odds': best_odds,
            'outcomes': outcome_names,
            'bet_percentages': arb_result['bet_percentages'],
            'bet_amounts_1000': arb_result['bet_amounts_1000']
        }
