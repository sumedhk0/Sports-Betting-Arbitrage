"""Market definitions and bookmaker mappings for sports betting API."""

# Player prop markets by sport
AMERICAN_FOOTBALL_MARKETS = 'player_assists,player_defensive_interceptions,player_field_goals,player_kicking_points,player_pass_attempts,player_pass_completions,player_pass_interceptions,player_pass_longest_completion,player_pass_rush_yds,player_pass_rush_reception_tds,player_pass_rush_reception_yds,player_pass_tds,player_pass_yds,player_pass_yds_q1,player_pats,player_receptions,player_reception_longest,player_reception_tds,player_reception_yds,player_rush_attempts,player_rush_longest,player_rush_reception_tds,player_rush_reception_yds,player_rush_tds,player_rush_yds,player_sacks,player_solo_tackles,player_tackles_assists'

BASKETBALL_MARKETS = 'player_points,player_points_q1,player_rebounds,player_rebounds_q1,player_assists,player_assists_q1,player_threes,player_blocks,player_steals,player_blocks_steals,player_turnovers,player_points_rebounds_assists,player_points_rebounds,player_points_assists,player_rebounds_assists,player_field_goals,player_frees_made,player_frees_attempts'

BASEBALL_MARKETS = 'batter_home_runs,batter_hits,batter_total_bases,batter_rbis,batter_runs_scored,batter_hits_runs_rbis,batter_singles,batter_doubles,batter_triples,batter_walks,batter_strikeouts,batter_stolen_bases,pitcher_strikeouts,pitcher_hits_allowed,pitcher_walks,pitcher_earned_runs,pitcher_outs'

ICE_HOCKEY_MARKETS = 'player_points,player_power_play_points,player_assists,player_blocked_shots,player_shots_on_goal,player_goals,player_total_saves'

AUSSIE_RULES_MARKETS = 'player_disposals,player_afl_fantasy_points'

SOCCER_MARKETS = 'player_shots_on_target,player_shots,player_assists'

# Bookmaker display name to API key mapping
BOOKMAKER_API_KEYS = {
    'BetOnline.ag': 'betonlineag',
    'BetMGM': 'betmgm',
    'BetRivers': 'betrivers',
    'BetUS': 'betus',
    'Bovada': 'bovada',
    'DraftKings': 'draftkings',
    'FanDuel': 'fanduel',
    'LowVig.ag': 'lowvig',
    'MyBookie.ag': 'mybookieag'
}

# Reverse mapping: API key to display name
API_KEY_TO_BOOKMAKER = {v: k for k, v in BOOKMAKER_API_KEYS.items()}

# Sports that use specific market types
AMERICAN_FOOTBALL_SPORTS = ['americanfootball_nfl', 'americanfootball_ncaaf', 'americanfootball_cfl']
BASKETBALL_SPORTS = ['basketball_nba', 'basketball_ncaab', 'basketball_wbna']
BASEBALL_SPORTS = ['baseball_mlb']
ICE_HOCKEY_SPORTS = ['icehockey_nhl']
AUSSIE_RULES_SPORTS = ['aussierules_afl']
SOCCER_SPORTS = ['soccer_epl', 'soccer_france_ligue_one', 'soccer_germany_bundesliga',
                 'soccer_italy_serie_a', 'soccer_spain_la_liga', 'soccer_usa_mls']


def get_markets_for_sport(sport_key: str) -> str:
    """Get the player prop markets string for a given sport key."""
    if sport_key in AMERICAN_FOOTBALL_SPORTS:
        return AMERICAN_FOOTBALL_MARKETS
    elif sport_key in BASKETBALL_SPORTS:
        return BASKETBALL_MARKETS
    elif sport_key in BASEBALL_SPORTS:
        return BASEBALL_MARKETS
    elif sport_key in ICE_HOCKEY_SPORTS:
        return ICE_HOCKEY_MARKETS
    elif sport_key in AUSSIE_RULES_SPORTS:
        return AUSSIE_RULES_MARKETS
    elif sport_key in SOCCER_SPORTS:
        return SOCCER_MARKETS
    return ''


def get_bookmakers_list():
    """Get list of all bookmakers with their API keys."""
    return [
        {'key': api_key, 'name': display_name}
        for display_name, api_key in BOOKMAKER_API_KEYS.items()
    ]
