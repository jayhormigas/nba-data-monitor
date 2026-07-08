"""
tests/contract/test_api_schema.py
---------------------------------
Contract tests for the data layer's response structure.

The validators and dashboard depend on NBAClient returning data in a
specific shape — certain keys, certain nesting, certain table names.
That expected shape is an unwritten "contract" between the data layer
and the rest of the project. These tests pin it down: they ignore the
actual values (how many wins the Lakers have) and only check STRUCTURE
(does each team have an "id" field at all?).

Why it matters: ESPN's public API is undocumented and can change without
warning. If a field gets renamed or a response restructured, the data
layer breaks its promised shape and these tests fail FIRST and clearly —
much easier to debug than data-quality tests failing in confusing ways
downstream.
"""

import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from nba_client import NBAClient

# Tag these as "contract" tests so they can be run on their own.
pytestmark = pytest.mark.contract
CLIENT = NBAClient()


# scope="module" means fetch once and reuse within this file.
@pytest.fixture(scope="module")
def teams():
    return CLIENT.get_all_teams()

@pytest.fixture(scope="module")
def scoreboard():
    return CLIENT.get_scoreboard()


# =============================================================================
# STATIC TEAMS — SCHEMA CHECKS
# Confirm each team dict still has the fields my validators rely on.
# =============================================================================

class TestStaticTeamsSchema:

    def test_teams_returns_list(self, teams):
        assert isinstance(teams, list)

    def test_each_team_has_id(self, teams):
        for team in teams:
            assert "id" in team

    def test_each_team_has_full_name(self, teams):
        for team in teams:
            assert "full_name" in team

    def test_each_team_has_abbreviation(self, teams):
        for team in teams:
            assert "abbreviation" in team

    def test_each_team_has_city(self, teams):
        for team in teams:
            assert "city" in team

    def test_each_team_has_year_founded(self, teams):
        for team in teams:
            assert "year_founded" in team


# =============================================================================
# SCOREBOARD — SCHEMA CHECKS
# The scoreboard is a deeply nested structure. These tests confirm the
# nesting and the specific sub-tables ("result sets") I depend on still
# exist with the expected keys.
# =============================================================================

class TestScoreboardSchema:

    def test_scoreboard_is_dict(self, scoreboard):
        assert isinstance(scoreboard, dict)

    def test_scoreboard_has_result_sets(self, scoreboard):
        assert "resultSets" in scoreboard

    def test_result_sets_is_list(self, scoreboard):
        assert isinstance(scoreboard["resultSets"], list)

    def test_each_result_set_has_name(self, scoreboard):
        # Every sub-table should be labeled with a "name".
        for rs in scoreboard["resultSets"]:
            assert "name" in rs

    def test_each_result_set_has_headers(self, scoreboard):
        # "headers" lists the column names for that sub-table.
        for rs in scoreboard["resultSets"]:
            assert "headers" in rs

    def test_each_result_set_has_row_set(self, scoreboard):
        # "rowSet" holds the actual data rows.
        for rs in scoreboard["resultSets"]:
            assert "rowSet" in rs

    def test_game_header_result_set_exists(self, scoreboard):
        # I specifically need the "GameHeader" table for game info.
        names = [rs["name"] for rs in scoreboard["resultSets"]]
        assert "GameHeader" in names

    def test_line_score_result_set_exists(self, scoreboard):
        # I specifically need the "LineScore" table for scores.
        names = [rs["name"] for rs in scoreboard["resultSets"]]
        assert "LineScore" in names
