"""
tests/unit/test_validators.py
-----------------------------
Unit tests for the validation rules in validators.py.

Each test feeds a validator some fake, hand-crafted data and asserts it
returns the right (passed, message) result.

No live API calls here, on purpose: unit tests should be fast and reliable, so
instead of hitting the network I build small fake data structures (the make_*
helpers below) that mimic the real API's shape. That also lets me cover edge
cases that are rare in real data, like a team with a negative score.

Reminder: pytest runs every function named test_*, and a failed `assert`
fails that test.
"""

import sys, os, pytest

# This line lets the test file import validators.py from the project root.
# Without it, Python wouldn't know where to find the validators module
# because the tests live in a subfolder (tests/unit/).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Import every validator function I want to test.
from validators import (
    validate_league_has_30_teams,
    validate_no_duplicate_team_ids,
    validate_team_required_fields,
    validate_team_abbreviations_are_valid,
    validate_team_ids_are_positive_integers,
    validate_year_founded_is_realistic,
    validate_standings_has_data,
    validate_standings_has_30_teams,
    validate_win_loss_non_negative,
    validate_win_pct_range,
    validate_no_duplicate_team_names_in_standings,
    validate_roster_not_empty,
    validate_no_duplicate_player_ids,
    validate_jersey_numbers_are_numeric,
    validate_players_have_names,
    validate_game_has_two_teams,
    validate_scores_non_negative,
    validate_scoreboard_game_ids_unique,
)


# =============================================================================
# HELPER FUNCTIONS
# These build fake data shaped like what the data layer returns.
# Each helper has parameters so I can easily create both "good" data
# (which should pass) and "bad" data (which should fail) in my tests.
# =============================================================================

def make_teams(count=30, unique_ids=True):
    """
    Builds a fake list of NBA teams.

    By default it makes 30 valid teams. Setting unique_ids=False makes
    every team share the same ID (1), which I use to test that the
    duplicate-detection rule actually catches duplicates.
    """
    return [
        {
            "id": i if unique_ids else 1,          # unique id, or all 1s
            "full_name": f"Team {i}",
            "abbreviation": f"T{i:02d}"[:3].upper(),  # e.g. "T01" -> always valid
            "city": f"City {i}",
            "state": f"State {i}",
            "year_founded": 1960,                   # a safe, realistic year
        }
        for i in range(1, count + 1)
    ]


def make_standings(count=30, wins=40, losses=42, pct=None, unique_names=True):
    """
    Builds a fake standings table (one row per team).

    pct (win percentage) is auto-calculated from wins/losses unless I
    pass a specific value — handy for testing out-of-range percentages.
    """
    if pct is None:
        pct = round(wins / (wins + losses), 3) if (wins + losses) else 0
    return [
        {
            "TeamName": f"Team{i}" if unique_names else "SameTeam",
            "W": wins, "L": losses, "WinPCT": pct,
        }
        for i in range(count)
    ]


def make_players(count=15, unique_ids=True, jerseys=None, names=True):
    """
    Builds a fake team roster (one dict per player).

    I can control the jersey numbers and whether players have names,
    so I can test those specific validation rules.
    """
    return [
        {
            "PLAYER_ID": i if unique_ids else 1,
            "PLAYER": f"Player {i}" if names else "",      # blank name if names=False
            "NUM": str(jerseys[i] if jerseys and i < len(jerseys) else i % 50),
        }
        for i in range(count)
    ]


# =============================================================================
# TEAM RULE TESTS
# Each "class" below groups together all the tests for one validation rule.
# Grouping with classes keeps the test output organized and readable.
# =============================================================================

class TestLeagueHas30Teams:
    """Tests for validate_league_has_30_teams()."""

    def test_30_teams_passes(self):
        # 30 teams is correct, so this should pass (return True).
        assert validate_league_has_30_teams(make_teams(30))[0]

    def test_29_teams_fails(self):
        # Only 29 teams — the rule should fail and mention "29" in its message.
        passed, msg = validate_league_has_30_teams(make_teams(29))
        assert not passed and "29" in msg

    def test_31_teams_fails(self):
        assert not validate_league_has_30_teams(make_teams(31))[0]

    def test_empty_list_fails(self):
        # An empty list (0 teams) should also fail.
        assert not validate_league_has_30_teams([])[0]


class TestNoDuplicateTeamIds:
    """Tests for validate_no_duplicate_team_ids()."""

    def test_unique_ids_pass(self):
        assert validate_no_duplicate_team_ids(make_teams(unique_ids=True))[0]

    def test_duplicate_ids_fail(self):
        # All teams share id=1 here, so the rule must catch the duplicates.
        passed, msg = validate_no_duplicate_team_ids(make_teams(unique_ids=False))
        assert not passed and "Duplicate" in msg


class TestTeamRequiredFields:
    """Tests for validate_team_required_fields()."""

    def test_complete_teams_pass(self):
        assert validate_team_required_fields(make_teams())[0]

    def test_missing_city_fails(self):
        teams = make_teams(1)
        teams[0]["city"] = ""          # wipe out the city field
        passed, msg = validate_team_required_fields(teams)
        assert not passed and "city" in msg

    def test_missing_abbreviation_fails(self):
        teams = make_teams(1)
        teams[0]["abbreviation"] = ""
        passed, msg = validate_team_required_fields(teams)
        assert not passed and "abbreviation" in msg


class TestTeamAbbreviations:
    """Tests for validate_team_abbreviations_are_valid()."""

    def test_valid_abbreviations_pass(self):
        teams = [{"full_name": "Lakers", "abbreviation": "LAL"},
                 {"full_name": "Heat",   "abbreviation": "MIA"}]
        assert validate_team_abbreviations_are_valid(teams)[0]

    def test_lowercase_abbreviation_fails(self):
        # Abbreviations must be uppercase.
        teams = [{"full_name": "Lakers", "abbreviation": "lal"}]
        assert not validate_team_abbreviations_are_valid(teams)[0]

    def test_too_long_abbreviation_fails(self):
        # 5 characters is too long (max is 3).
        teams = [{"full_name": "Lakers", "abbreviation": "LAKER"}]
        assert not validate_team_abbreviations_are_valid(teams)[0]

    def test_single_char_abbreviation_fails(self):
        # 1 character is too short (min is 2).
        teams = [{"full_name": "X", "abbreviation": "X"}]
        assert not validate_team_abbreviations_are_valid(teams)[0]


class TestTeamIdsArePositive:
    """Tests for validate_team_ids_are_positive_integers()."""

    def test_positive_ids_pass(self):
        assert validate_team_ids_are_positive_integers(make_teams())[0]

    def test_zero_id_fails(self):
        teams = [{"id": 0, "full_name": "Zero Team"}]
        assert not validate_team_ids_are_positive_integers(teams)[0]

    def test_negative_id_fails(self):
        teams = [{"id": -1, "full_name": "Negative Team"}]
        assert not validate_team_ids_are_positive_integers(teams)[0]

    def test_string_id_fails(self):
        # A string where we expect an integer should be rejected.
        teams = [{"id": "abc", "full_name": "String Team"}]
        assert not validate_team_ids_are_positive_integers(teams)[0]


class TestYearFounded:
    """Tests for validate_year_founded_is_realistic()."""

    def test_realistic_years_pass(self):
        assert validate_year_founded_is_realistic(make_teams())[0]

    def test_year_1800_fails(self):
        # The NBA didn't exist in 1800.
        teams = make_teams(1)
        teams[0]["year_founded"] = 1800
        assert not validate_year_founded_is_realistic(teams)[0]

    def test_future_year_fails(self):
        teams = make_teams(1)
        teams[0]["year_founded"] = 2050
        assert not validate_year_founded_is_realistic(teams)[0]

    def test_boundary_year_1940_passes(self):
        # 1940 is exactly the lower bound, so it should pass.
        teams = make_teams(1)
        teams[0]["year_founded"] = 1940
        assert validate_year_founded_is_realistic(teams)[0]


# =============================================================================
# STANDINGS RULE TESTS
# =============================================================================

class TestStandingsHasData:
    """Tests for validate_standings_has_data()."""

    def test_non_empty_standings_pass(self):
        assert validate_standings_has_data(make_standings())[0]

    def test_empty_standings_fail(self):
        assert not validate_standings_has_data([])[0]


class TestStandingsHas30Teams:
    """Tests for validate_standings_has_30_teams()."""

    def test_30_teams_pass(self):
        assert validate_standings_has_30_teams(make_standings(30))[0]

    def test_29_teams_fail(self):
        passed, msg = validate_standings_has_30_teams(make_standings(29))
        assert not passed and "29" in msg


class TestWinLossNonNegative:
    """Tests for validate_win_loss_non_negative()."""

    def test_valid_records_pass(self):
        assert validate_win_loss_non_negative(make_standings())[0]

    def test_negative_wins_fail(self):
        rows = [{"TeamName": "Bad Team", "W": -1, "L": 10, "WinPCT": 0}]
        passed, msg = validate_win_loss_non_negative(rows)
        assert not passed and "negative wins" in msg

    def test_negative_losses_fail(self):
        rows = [{"TeamName": "Bad Team", "W": 10, "L": -1, "WinPCT": 0}]
        assert not validate_win_loss_non_negative(rows)[0]

    def test_zero_wins_and_losses_passes(self):
        # A brand-new season: 0 wins and 0 losses is valid.
        rows = [{"TeamName": "New Team", "W": 0, "L": 0, "WinPCT": 0}]
        assert validate_win_loss_non_negative(rows)[0]


class TestWinPctRange:
    """Tests for validate_win_pct_range()."""

    def test_valid_pct_passes(self):
        assert validate_win_pct_range(make_standings(pct=0.500))[0]

    def test_zero_pct_passes(self):
        assert validate_win_pct_range(make_standings(pct=0.000))[0]

    def test_perfect_pct_passes(self):
        assert validate_win_pct_range(make_standings(pct=1.000))[0]

    def test_pct_above_1_fails(self):
        # You can't win more than 100% of your games.
        rows = [{"TeamName": "Bad", "W": 50, "L": 0, "WinPCT": 1.5}]
        assert not validate_win_pct_range(rows)[0]

    def test_negative_pct_fails(self):
        rows = [{"TeamName": "Bad", "W": 0, "L": 50, "WinPCT": -0.1}]
        assert not validate_win_pct_range(rows)[0]


class TestNoDuplicateTeamNamesInStandings:
    """Tests for validate_no_duplicate_team_names_in_standings()."""

    def test_unique_names_pass(self):
        assert validate_no_duplicate_team_names_in_standings(make_standings(unique_names=True))[0]

    def test_duplicate_names_fail(self):
        passed, msg = validate_no_duplicate_team_names_in_standings(make_standings(unique_names=False))
        assert not passed and "Duplicate" in msg


# =============================================================================
# ROSTER RULE TESTS
# =============================================================================

class TestRosterNotEmpty:
    """Tests for validate_roster_not_empty()."""

    def test_full_roster_passes(self):
        assert validate_roster_not_empty(make_players(15))[0]

    def test_exactly_10_passes(self):
        # 10 is the NBA minimum, so exactly 10 should pass.
        assert validate_roster_not_empty(make_players(10))[0]

    def test_9_players_fails(self):
        passed, msg = validate_roster_not_empty(make_players(9))
        assert not passed and "9" in msg

    def test_empty_roster_fails(self):
        assert not validate_roster_not_empty([])[0]


class TestNoDuplicatePlayerIds:
    """Tests for validate_no_duplicate_player_ids()."""

    def test_unique_ids_pass(self):
        assert validate_no_duplicate_player_ids(make_players(unique_ids=True))[0]

    def test_duplicate_ids_fail(self):
        passed, msg = validate_no_duplicate_player_ids(make_players(unique_ids=False))
        assert not passed and "Duplicate" in msg


class TestJerseyNumbers:
    """Tests for validate_jersey_numbers_are_numeric()."""

    def test_valid_jerseys_pass(self):
        # 0 and 99 are the boundaries; all valid.
        players = make_players(5, jerseys=[0, 3, 23, 34, 99])
        assert validate_jersey_numbers_are_numeric(players)[0]

    def test_jersey_100_fails(self):
        # 100 is above the max of 99.
        players = make_players(1, jerseys=[100])
        passed, msg = validate_jersey_numbers_are_numeric(players)
        assert not passed and "100" in msg

    def test_negative_jersey_fails(self):
        players = [{"PLAYER_ID": 1, "PLAYER": "Test", "NUM": "-1"}]
        assert not validate_jersey_numbers_are_numeric(players)[0]

    def test_empty_jersey_is_allowed(self):
        # A player with no jersey number yet is allowed (returns valid).
        players = [{"PLAYER_ID": 1, "PLAYER": "Test", "NUM": ""}]
        assert validate_jersey_numbers_are_numeric(players)[0]


class TestPlayersHaveNames:
    """Tests for validate_players_have_names()."""

    def test_named_players_pass(self):
        assert validate_players_have_names(make_players())[0]

    def test_empty_name_fails(self):
        passed, msg = validate_players_have_names(make_players(names=False))
        assert not passed and "no name" in msg


# =============================================================================
# SCOREBOARD RULE TESTS
# =============================================================================

class TestGameHasTwoTeams:
    """Tests for validate_game_has_two_teams()."""

    def test_two_teams_passes(self):
        # A normal game: two rows sharing the same GAME_ID.
        line_scores = [{"GAME_ID": "001", "TEAM_ABBREVIATION": "LAL"},
                       {"GAME_ID": "001", "TEAM_ABBREVIATION": "BOS"}]
        assert validate_game_has_two_teams(line_scores, "001")[0]

    def test_one_team_fails(self):
        line_scores = [{"GAME_ID": "001", "TEAM_ABBREVIATION": "LAL"}]
        passed, msg = validate_game_has_two_teams(line_scores, "001")
        assert not passed and "1" in msg

    def test_three_teams_fails(self):
        # Three teams in one game is impossible.
        line_scores = [{"GAME_ID": "001", "TEAM_ABBREVIATION": t} for t in ["LAL", "BOS", "GSW"]]
        assert not validate_game_has_two_teams(line_scores, "001")[0]


class TestScoresNonNegative:
    """Tests for validate_scores_non_negative()."""

    def test_valid_scores_pass(self):
        rows = [{"TEAM_ABBREVIATION": "LAL", "PTS": 110},
                {"TEAM_ABBREVIATION": "BOS", "PTS": 105}]
        assert validate_scores_non_negative(rows)[0]

    def test_zero_score_passes(self):
        # A game that hasn't tipped off yet has 0 points — valid.
        rows = [{"TEAM_ABBREVIATION": "LAL", "PTS": 0}]
        assert validate_scores_non_negative(rows)[0]

    def test_negative_score_fails(self):
        rows = [{"TEAM_ABBREVIATION": "LAL", "PTS": -1}]
        passed, msg = validate_scores_non_negative(rows)
        assert not passed and "negative" in msg


class TestScoreboardGameIdsUnique:
    """Tests for validate_scoreboard_game_ids_unique()."""

    def test_unique_game_ids_pass(self):
        headers = [{"GAME_ID": "001"}, {"GAME_ID": "002"}, {"GAME_ID": "003"}]
        assert validate_scoreboard_game_ids_unique(headers)[0]

    def test_duplicate_game_ids_fail(self):
        headers = [{"GAME_ID": "001"}, {"GAME_ID": "001"}]
        passed, msg = validate_scoreboard_game_ids_unique(headers)
        assert not passed and "Duplicate" in msg

    def test_empty_scoreboard_passes(self):
        # No games today (e.g. offseason) is not an error.
        assert validate_scoreboard_game_ids_unique([])[0]
