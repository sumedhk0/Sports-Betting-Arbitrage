"""Arbitrage calculation and analysis functions."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any


class ArbitrageAgent:
    """Static class for calculating arbitrage opportunities."""

    @staticmethod
    def find_arbitrage(odds1: float, odds2: float, odds3: float = None) -> Dict:
        """
        Calculate arbitrage opportunity from American odds.

        Args:
            odds1: First outcome American odds
            odds2: Second outcome American odds
            odds3: Optional third outcome American odds (for 3-way markets)

        Returns:
            Dict with roi, bet_percentages, and bet_amounts_1000
        """
        def american_to_decimal(american_odds: float) -> float:
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1

        odds_list = [odds1, odds2]
        if odds3 is not None:
            odds_list.append(odds3)

        decimal_odds = [american_to_decimal(odds) for odds in odds_list]
        inverse_sum = sum(1/odds for odds in decimal_odds)
        roi = (1 - inverse_sum) * 100
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


def analyze_player_prop_arbitrage(player_props: Dict) -> Optional[Dict]:
    """
    Analyze player prop market for arbitrage opportunities.

    Args:
        player_props: Dict of bookmaker data with over/under odds

    Returns:
        Dict with arbitrage details or None if no opportunity
    """
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
        # Group by point value
        point_groups = {}
        for outcome, odds_list in market_data.items():
            for item in odds_list:
                if len(item) >= 3:
                    bookmaker, odds, point = item[0], item[1], item[2]
                else:
                    continue
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
                arb_result = ArbitrageAgent.find_arbitrage(*best_odds[:3])
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

        arb_result = ArbitrageAgent.find_arbitrage(*best_odds[:3])
        return {
            'roi': arb_result['roi'],
            'bookmakers': bookmakers_used,
            'odds': best_odds,
            'outcomes': outcome_names,
            'bet_percentages': arb_result['bet_percentages'],
            'bet_amounts_1000': arb_result['bet_amounts_1000']
        }
