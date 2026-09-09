"""Arbitrage logic tests.

The same contract is run against both copies of the logic:
  - api/lib/arbitrage.py   (Flask API behind the Next.js UI)
  - arbitrageCalculator.py (CLI)

Run with:  python -m unittest discover -s tests -v
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------

def load_api_lib():
    sys.path.insert(0, str(ROOT / 'api'))
    from lib import arbitrage  # noqa: E402
    return arbitrage


def _stub(name, **attrs):
    """Register a minimal module under `name` if it is not importable."""
    mod = sys.modules.get(name)
    if mod is None:
        try:
            mod = importlib.import_module(name)
        except ImportError:
            mod = types.ModuleType(name)
            sys.modules[name] = mod
    for key, value in attrs.items():
        if not hasattr(mod, key):
            setattr(mod, key, value)
    return mod


def load_cli_module():
    """Import arbitrageCalculator.py with its network/TUI deps stubbed.

    Only the pure arbitrage functions are exercised here, so the stubs never
    get called. This keeps the tests runnable on a bare interpreter.
    """
    _stub('requests')
    _stub('questionary')
    _stub('dotenv', load_dotenv=lambda *a, **k: None)
    _stub('rich')
    _stub('rich.live', Live=object)
    _stub('rich.text', Text=object)
    _stub('rich.console', Console=object)
    spec = importlib.util.spec_from_file_location(
        'arbitrageCalculator', ROOT / 'arbitrageCalculator.py'
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# Shared contract
# --------------------------------------------------------------------------

class ArbitrageContract:
    """Test cases shared by both implementations.

    Subclasses bind: find, analyze_market, analyze_prop, build_props.
    """

    # ---- find_arbitrage -------------------------------------------------

    def test_roi_is_profit_over_total_stake(self):
        # +220 / +220: decimal 3.2 each, implied 0.3125 each, sum 0.625.
        # $100 split 50/50 pays 50 * 3.2 = $160 either way => 60% ROI.
        result = self.find(220, 220)
        self.assertAlmostEqual(result['roi'], 60.0, places=6)
        self.assertAlmostEqual(sum(result['bet_percentages']), 100.0, places=6)

    def test_find_arbitrage_accepts_any_number_of_outcomes(self):
        # Four outcomes at +300 sum to exactly 1.0: no edge, not 33%.
        result = self.find(300, 300, 300, 300)
        self.assertAlmostEqual(result['roi'], 0.0, places=9)
        self.assertEqual(len(result['bet_percentages']), 4)
        for pct in result['bet_percentages']:
            self.assertAlmostEqual(pct, 25.0, places=9)

        result = self.find(350, 350, 350, 350)
        self.assertAlmostEqual(result['roi'], 12.5, places=9)

    def test_find_arbitrage_requires_at_least_two_outcomes(self):
        with self.assertRaises(ValueError):
            self.find(300)
        with self.assertRaises(ValueError):
            self.find()

    # ---- spreads ----------------------------------------------------------

    def test_spreads_reject_two_favourites_on_same_side(self):
        # Screenshot case. DraftKings makes Montreal the favourite, BetMGM
        # makes Pittsburgh the favourite. Montreal -1.5 and Pittsburgh -1.5
        # both lose when the game is decided by one goal, so this is not
        # an arbitrage even though the naive maths says +60%.
        market = {
            'Montréal Canadiens': [('DraftKings', 220, -1.5), ('BetMGM', -280, 1.5)],
            'Pittsburgh Penguins': [('DraftKings', -280, 1.5), ('BetMGM', 220, -1.5)],
        }
        result = self.analyze_market(market, 'spreads')
        self.assertIsNotNone(result)
        self.assertLess(result['roi'], 0)
        self._assert_spread_outcomes_are_complementary(result)

    def test_spreads_pair_opposite_sides_across_books(self):
        # DraftKings favours Montreal; BetMGM and FanDuel favour Pittsburgh.
        # The only real arb is Montreal +1.5 (BetMGM -140) with
        # Pittsburgh -1.5 (FanDuel +250): 0.5833 + 0.2857 = 0.869 => 15.07%.
        # Grouping by raw point would instead pair Montreal -1.5 (+220) with
        # Pittsburgh -1.5 (+250) and report a bogus 67%.
        market = {
            'Montréal Canadiens': [
                ('DraftKings', 220, -1.5), ('BetMGM', -140, 1.5), ('FanDuel', -160, 1.5),
            ],
            'Pittsburgh Penguins': [
                ('DraftKings', -280, 1.5), ('BetMGM', 230, -1.5), ('FanDuel', 250, -1.5),
            ],
        }
        result = self.analyze_market(market, 'spreads')
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['roi'], 15.068493, places=4)
        self._assert_spread_outcomes_are_complementary(result)
        by_outcome = dict(zip(result['outcomes'], result['bookmakers']))
        self.assertEqual(by_outcome, {
            'Montréal Canadiens +1.5': 'BetMGM',
            'Pittsburgh Penguins -1.5': 'FanDuel',
        })

    def test_spreads_with_only_one_side_is_not_an_opportunity(self):
        market = {
            'Montréal Canadiens': [('DraftKings', 220, -1.5)],
            'Pittsburgh Penguins': [('BetMGM', 220, -2.5)],
        }
        self.assertIsNone(self.analyze_market(market, 'spreads'))

    def test_spreads_pick_em_pairs_zero_with_zero(self):
        market = {
            'Home': [('DraftKings', 110, 0.0)],
            'Away': [('BetMGM', 105, 0.0)],
        }
        result = self.analyze_market(market, 'spreads')
        self.assertIsNotNone(result)
        # 1/2.1 + 1/2.05 = 0.4762 + 0.4878 = 0.9640 => 3.73%
        self.assertAlmostEqual(result['roi'], 3.7349, places=3)

    # ---- totals -----------------------------------------------------------

    def test_totals_group_by_point(self):
        market = {
            'Over': [('DraftKings', 105, 5.5), ('BetMGM', -120, 6.5)],
            'Under': [('BetMGM', 100, 5.5), ('DraftKings', -105, 6.5)],
        }
        result = self.analyze_market(market, 'totals')
        self.assertIsNotNone(result)
        # Over 5.5 (+105) + Under 5.5 (+100): 0.4878 + 0.5 = 0.9878 => 1.235%
        self.assertAlmostEqual(result['roi'], 1.2346, places=3)
        self.assertEqual(sorted(result['outcomes']), ['Over 5.5', 'Under 5.5'])

    def test_totals_never_pair_different_points(self):
        market = {
            'Over': [('DraftKings', 300, 6.5)],
            'Under': [('BetMGM', -110, 5.5)],
        }
        self.assertIsNone(self.analyze_market(market, 'totals'))

    # ---- h2h --------------------------------------------------------------

    def test_h2h_three_way_covers_draw(self):
        market = {
            'Home': [('DraftKings', 200)],
            'Draw': [('BetMGM', 300)],
            'Away': [('FanDuel', 250)],
        }
        result = self.analyze_market(market, 'h2h')
        self.assertIsNotNone(result)
        self.assertEqual(len(result['odds']), 3)
        # 0.3333 + 0.25 + 0.2857 = 0.869 => 15.07%
        self.assertAlmostEqual(result['roi'], 15.068493, places=4)

    def test_h2h_does_not_truncate_to_three_outcomes(self):
        market = {name: [('DraftKings', 300)] for name in ['A', 'B', 'C', 'D']}
        result = self.analyze_market(market, 'h2h')
        self.assertIsNotNone(result)
        self.assertEqual(len(result['odds']), 4)
        self.assertAlmostEqual(result['roi'], 0.0, places=9)

    # ---- player props -----------------------------------------------------

    def test_prop_analyzer_uses_best_over_and_best_under(self):
        entries = [
            {'bookmaker': 'DraftKings', 'over/under': 'Over', 'odds': 150,
             'player_name': 'Sidney Crosby', 'point': 0.5},
            {'bookmaker': 'DraftKings', 'over/under': 'Under', 'odds': -200,
             'player_name': 'Sidney Crosby', 'point': 0.5},
            {'bookmaker': 'BetMGM', 'over/under': 'Over', 'odds': 120,
             'player_name': 'Sidney Crosby', 'point': 0.5},
            {'bookmaker': 'BetMGM', 'over/under': 'Under', 'odds': -120,
             'player_name': 'Sidney Crosby', 'point': 0.5},
        ]
        result = self.analyze_prop(entries)
        self.assertIsNotNone(result)
        # Over +150 (DK) 0.4 + Under -120 (MGM) 0.5455 = 0.9455 => 5.77%
        self.assertAlmostEqual(result['roi'], 5.7692, places=3)
        self.assertEqual(result['bookmakers'], ['DraftKings', 'BetMGM'])
        self.assertEqual(result['outcomes'], ['Over 0.5', 'Under 0.5'])
        self.assertEqual(result['player_name'], 'Sidney Crosby')

    def test_prop_analyzer_needs_both_sides(self):
        entries = [
            {'bookmaker': 'DraftKings', 'over/under': 'Over', 'odds': 150,
             'player_name': 'Sidney Crosby', 'point': 0.5},
        ]
        self.assertIsNone(self.analyze_prop(entries))
        self.assertIsNone(self.analyze_prop([]))

    def test_prop_builder_keeps_both_sides_from_one_bookmaker(self):
        # Regression: keying the builder by bookmaker alone made the Under
        # overwrite the Over, so no prop arb was ever detected.
        bookmakers = [
            {'key': 'draftkings', 'title': 'DraftKings', 'markets': [{
                'key': 'player_goals', 'outcomes': [
                    {'name': 'Over', 'description': 'Sidney Crosby', 'point': 0.5, 'price': 150},
                    {'name': 'Under', 'description': 'Sidney Crosby', 'point': 0.5, 'price': -200},
                    {'name': 'Over', 'description': 'Nick Suzuki', 'point': 0.5, 'price': 170},
                    {'name': 'Under', 'description': 'Nick Suzuki', 'point': 0.5, 'price': -230},
                    {'name': 'Over', 'point': 5.5, 'price': -110},  # team total, no description
                ]}, {
                'key': 'h2h', 'outcomes': [{'name': 'Pittsburgh Penguins', 'price': -130}],
            }]},
            {'key': 'betmgm', 'title': 'BetMGM', 'markets': [{
                'key': 'player_goals', 'outcomes': [
                    {'name': 'Over', 'description': 'Sidney Crosby', 'point': 0.5, 'price': 120},
                    {'name': 'Under', 'description': 'Sidney Crosby', 'point': 0.5, 'price': -120},
                ]}]},
        ]
        props = self.build_props(bookmakers, ['player_goals', 'player_assists'])

        self.assertEqual(set(props.keys()), {'player_goals', 'player_assists'})
        self.assertEqual(props['player_assists'], {})

        crosby = props['player_goals']['Sidney Crosby|||0.5']
        self.assertEqual(len(crosby), 4)
        dk_sides = sorted(e['over/under'] for e in crosby if e['bookmaker'] == 'DraftKings')
        self.assertEqual(dk_sides, ['Over', 'Under'])

        result = self.analyze_prop(crosby)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result['roi'], 5.7692, places=3)

    # ---- helpers ----------------------------------------------------------

    def _assert_spread_outcomes_are_complementary(self, result):
        points = []
        for outcome in result['outcomes']:
            points.append(float(outcome.rsplit(' ', 1)[1]))
        self.assertEqual(len(points), 2, result['outcomes'])
        self.assertAlmostEqual(points[0] + points[1], 0.0, places=9,
                               msg=f"not complementary: {result['outcomes']}")


class TestApiLib(ArbitrageContract, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib = load_api_lib()
        cls.find = staticmethod(lib.ArbitrageAgent.find_arbitrage)
        cls.analyze_market = staticmethod(lib.analyze_market_arbitrage)
        cls.analyze_prop = staticmethod(lib.analyze_player_prop_arbitrage)
        cls.build_props = staticmethod(lib.build_player_prop_odds)


class TestCli(ArbitrageContract, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cli = load_cli_module()
        cls.find = staticmethod(cli.ArbitrageAgent.findArbitrage)
        cls.analyze_market = staticmethod(cli.analyzeMarketArbitrage)
        cls.analyze_prop = staticmethod(cli.analyzePlayerPropArbitrage)
        cls.build_props = staticmethod(cli.buildPlayerPropOdds)


if __name__ == '__main__':
    unittest.main()
