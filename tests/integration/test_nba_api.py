"""
tests/integration/test_nba_api.py
---------------------------------
Integration tests against the live data source (ESPN's public NBA API).

Unlike the unit tests (which use fake data), these fetch REAL data and
confirm that what the API returns today passes every validation rule.
This is the heart of the monitor: if live NBA data goes bad, these are
the tests that catch it.

They need an internet connection but no API key. To keep the suite fast,
the fixtures below use scope="session" so each dataset is fetched once
and shared across all the tests in this file, instead of re-downloading
per test.
"""

import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from nba_client import NBAClient
from validators import *   # import all the validation rules

# This marker tags every test in this file as "integration". It lets me
# run just these tests with:  pytest -m integration
pytestmark = pytest.mark.integration

# One client instance, reused by all the fixtures below.
CLIENT = NBAClient()

# NBA team IDs for the two teams I spot-check rosters for.
# (Found using CLIENT.get_all_teams() — every team has a permanent ID.)
LAKERS_ID  = 1610612747
CELTICS_ID = 1610612738


# =============================================================================
# FIXTURES
# A "fixture" is a function that prepares data for tests to use. Any test
# that lists a fixture's name as a parameter automatically receives whatever
# the fixture returns.
#
# scope="session" means: run this fixture only ONCE for the whole test run
# and reuse the result. This avoids hammering ESPN with repeated
# identical requests, which keeps the suite fast and polite to their servers.
# =============================================================================

@pytest.fixture(scope="session")
def all_teams():
    """All 30 teams (static data — no network call, always available)."""
    return CLIENT.get_all_teams()

@pytest.fixture(scope="session")
def standings_df():
    """Live standings, as a pandas DataFrame (fetched once)."""
    return CLIENT.get_standings_df()

@pytest.fixture(scope="session")
def lakers_roster_df():
    """The Lakers' current roster (fetched once)."""
    return CLIENT.get_roster_df(LAKERS_ID)

@pytest.fixture(scope="session")
def celtics_roster_df():
    """The Celtics' current roster (fetched once)."""
    return CLIENT.get_roster_df(CELTICS_ID)

@pytest.fixture(scope="session")
def scoreboard():
    """Today's scoreboard data (fetched once)."""
    return CLIENT.get_scoreboard()


# =============================================================================
# TEAM DATA TESTS (static data — fast and always available)
# =============================================================================

class TestTeamsStaticData:
    """
    Runs the team validation rules against the real teams list.
    Each test takes the 'all_teams' fixture, runs one rule, and asserts
    it passed. If a rule fails, pytest prints the rule's error message.
    """

    def test_exactly_30_teams(self, all_teams):
        passed, msg = validate_league_has_30_teams(all_teams)
        assert passed, msg   # if this fails, 'msg' is shown in the output

    def test_no_duplicate_team_ids(self, all_teams):
        passed, msg = validate_no_duplicate_team_ids(all_teams)
        assert passed, msg

    def test_all_teams_have_required_fields(self, all_teams):
        passed, msg = validate_team_required_fields(all_teams)
        assert passed, msg

    def test_all_abbreviations_valid(self, all_teams):
        passed, msg = validate_team_abbreviations_are_valid(all_teams)
        assert passed, msg

    def test_all_ids_are_positive_integers(self, all_teams):
        passed, msg = validate_team_ids_are_positive_integers(all_teams)
        assert passed, msg

    def test_founding_years_realistic(self, all_teams):
        passed, msg = validate_year_founded_is_realistic(all_teams)
        assert passed, msg


# =============================================================================
# STANDINGS TESTS (live data)
# =============================================================================

class TestStandingsDataQuality:
    """
    Runs standings rules against live standings data.

    Note on .to_dict("records"): the standings come back as a pandas
    DataFrame. Calling .to_dict("records") converts it into a plain list
    of dictionaries (one dict per team row), which is the format my
    validator functions expect.
    """

    def test_standings_not_empty(self, standings_df):
        rows = standings_df.to_dict("records")
        passed, msg = validate_standings_has_data(rows)
        assert passed, msg

    def test_standings_has_30_teams(self, standings_df):
        rows = standings_df.to_dict("records")
        passed, msg = validate_standings_has_30_teams(rows)
        assert passed, msg

    def test_win_loss_non_negative(self, standings_df):
        rows = standings_df.to_dict("records")
        passed, msg = validate_win_loss_non_negative(rows)
        assert passed, msg

    def test_win_pct_in_valid_range(self, standings_df):
        rows = standings_df.to_dict("records")
        # The win% column name can vary, so I map it to a consistent key
        # ("WinPCT") before handing the rows to the validator.
        mapped = [{"TeamName": r.get("TeamName", "?"),
                   "WinPCT": r.get("WinPCT", r.get("PCT", 0.5))} for r in rows]
        passed, msg = validate_win_pct_range(mapped)
        assert passed, msg

    def test_no_duplicate_team_names(self, standings_df):
        rows = standings_df.to_dict("records")
        passed, msg = validate_no_duplicate_team_names_in_standings(rows)
        assert passed, msg


# =============================================================================
# ROSTER TESTS (live data) — spot-checking two well-known teams
# =============================================================================

class TestLakersRoster:
    """Validates the Lakers' live roster data."""

    def test_roster_not_empty(self, lakers_roster_df):
        players = lakers_roster_df.to_dict("records")
        passed, msg = validate_roster_not_empty(players)
        assert passed, msg

    def test_no_duplicate_player_ids(self, lakers_roster_df):
        players = lakers_roster_df.to_dict("records")
        passed, msg = validate_no_duplicate_player_ids(players)
        assert passed, msg

    def test_jersey_numbers_valid(self, lakers_roster_df):
        players = lakers_roster_df.to_dict("records")
        passed, msg = validate_jersey_numbers_are_numeric(players)
        assert passed, msg

    def test_all_players_have_names(self, lakers_roster_df):
        players = lakers_roster_df.to_dict("records")
        passed, msg = validate_players_have_names(players)
        assert passed, msg


class TestCelticsRoster:
    """Validates the Celtics' live roster data (same checks as Lakers)."""

    def test_roster_not_empty(self, celtics_roster_df):
        players = celtics_roster_df.to_dict("records")
        passed, msg = validate_roster_not_empty(players)
        assert passed, msg

    def test_no_duplicate_player_ids(self, celtics_roster_df):
        players = celtics_roster_df.to_dict("records")
        passed, msg = validate_no_duplicate_player_ids(players)
        assert passed, msg

    def test_jersey_numbers_valid(self, celtics_roster_df):
        players = celtics_roster_df.to_dict("records")
        passed, msg = validate_jersey_numbers_are_numeric(players)
        assert passed, msg

    def test_all_players_have_names(self, celtics_roster_df):
        players = celtics_roster_df.to_dict("records")
        passed, msg = validate_players_have_names(players)
        assert passed, msg


# =============================================================================
# SCOREBOARD TESTS (live data)
# The scoreboard returns multiple sub-tables ("result sets"). I have to
# dig into the raw structure to pull out the specific tables I need.
# =============================================================================

class TestScoreboard:
    """Validates today's live scoreboard data."""

    def test_scoreboard_returns_dict(self, scoreboard):
        assert isinstance(scoreboard, dict)

    def test_scoreboard_has_result_sets(self, scoreboard):
        # The whole response is organized under a "resultSets" key.
        assert "resultSets" in scoreboard

    def test_game_ids_are_unique(self, scoreboard):
        result_sets = scoreboard.get("resultSets", [])
        # Find the "GameHeader" table (one row per game).
        headers = next((rs for rs in result_sets if rs.get("name") == "GameHeader"), None)

        # If there are no games today (e.g. offseason), skip this test
        # instead of failing it. pytest.skip() marks it as skipped.
        if headers is None or not headers.get("rowSet"):
            pytest.skip("No games on today's scoreboard")

        # The data is row-based, so I find which column holds GAME_ID,
        # then pull that value out of every row.
        col = headers["headers"].index("GAME_ID")
        game_headers = [{"GAME_ID": row[col]} for row in headers["rowSet"]]
        passed, msg = validate_scoreboard_game_ids_unique(game_headers)
        assert passed, msg

    def test_scores_non_negative(self, scoreboard):
        result_sets = scoreboard.get("resultSets", [])
        # The "LineScore" table has one row per team per game, with points.
        line_score = next((rs for rs in result_sets if rs.get("name") == "LineScore"), None)
        if line_score is None or not line_score.get("rowSet"):
            pytest.skip("No line score data today")

        headers  = line_score["headers"]
        pts_col  = headers.index("PTS")
        abbr_col = headers.index("TEAM_ABBREVIATION")
        rows = [{"TEAM_ABBREVIATION": r[abbr_col], "PTS": r[pts_col] or 0}
                for r in line_score["rowSet"]]
        passed, msg = validate_scores_non_negative(rows)
        assert passed, msg
