"""
validators.py
-------------
This file contains all the data quality rules for the project.

Each function takes in some NBA data (a list of teams, a list of players,
etc.) and returns a tuple: (passed: bool, message: str).

  - If the data looks correct, passed=True and message explains what passed.
  - If something looks wrong, passed=False and message explains what failed.

IMPORTANT DESIGN DECISION: These functions are completely "pure" — they
don't make any network calls, don't read from files, and don't have any
side effects. They just take data in and return a result. This makes them
extremely easy to test in isolation (see tests/unit/test_validators.py).

The pytest test suite calls these functions with real live NBA data.
generate_report.py calls them too and writes the results to JSON, which
the React dashboard reads so you can see pass/fail visually.

Think of this file as the "rulebook" — it defines what valid NBA data
should look like, and the test suite + dashboard enforce those rules.
"""

# Type hints make the code easier to read and catch bugs early.
# Result is just a shorthand for "a tuple of (bool, str)".
from typing import Tuple, List
Result = Tuple[bool, str]


# =============================================================================
# TEAM VALIDATION RULES
# These rules run against the static teams list from nba_api.
# Since this data doesn't change (teams don't appear/disappear mid-season),
# these rules should always pass unless nba_api's bundled data is broken.
# =============================================================================

def validate_league_has_30_teams(teams: list) -> Result:
    """
    Checks that the NBA has exactly 30 teams.

    This sounds obvious, but it's a good sanity check — if nba_api ever
    returns a partial list (e.g. due to a bug), we want to catch it
    immediately rather than having downstream tests silently fail.
    """
    count = len(teams)
    if count == 30:
        return True, "League has exactly 30 teams"
    return False, f"Expected 30 teams, got {count}"


def validate_no_duplicate_team_ids(teams: list) -> Result:
    """
    Checks that every team has a unique ID.

    Each NBA team has a permanent numeric ID assigned by the league
    (e.g. Lakers = 1610612747). If two teams somehow share an ID,
    any lookup by team_id would return the wrong data.

    Quick trick: compare len(list) to len(set(list)). A set drops repeats,
    so if the set is shorter, some IDs showed up more than once.
    """
    ids = [t["id"] for t in teams]
    if len(ids) == len(set(ids)):
        return True, "All team IDs are unique"
    # Find which IDs appear more than once to include in the error message
    dupes = [i for i in ids if ids.count(i) > 1]
    return False, f"Duplicate team IDs: {set(dupes)}"


def validate_team_required_fields(teams: list) -> Result:
    """
    Checks that every team has the five fields we depend on.

    If any of these fields are missing or empty, other parts of the
    project (like the dashboard) will break when trying to display
    team information. Better to catch it here with a clear error.
    """
    required = ["id", "full_name", "abbreviation", "city", "state"]
    for team in teams:
        # dict.get() returns None if the key doesn't exist, which is falsy
        missing = [f for f in required if not team.get(f)]
        if missing:
            return False, f"Team '{team.get('full_name', '?')}' missing: {missing}"
    return True, "All teams have required fields"


def validate_team_abbreviations_are_valid(teams: list) -> Result:
    """
    Checks that team abbreviations are 2-3 uppercase letters.

    Valid examples: LAL, BOS, GSW, MIA, NY (2 chars for Knicks)
    Invalid examples: "lal" (lowercase), "LAKER" (too long), "" (empty)

    Abbreviations are used heavily in scoreboard displays and
    need to be consistent to match how scores are reported.
    """
    for team in teams:
        abbr = team.get("abbreviation", "")
        if not (2 <= len(abbr) <= 3) or not abbr.isupper():
            return False, f"Invalid abbreviation: '{abbr}' for {team.get('full_name')}"
    return True, "All abbreviations are valid"


def validate_team_ids_are_positive_integers(teams: list) -> Result:
    """
    Checks that all team IDs are positive integers.

    The NBA uses large positive integers for team IDs (like 1610612747).
    A zero, negative number, or non-integer would indicate corrupted data.
    We also check isinstance(tid, int) because JSON parsing can sometimes
    return numbers as strings depending on how the data is structured.
    """
    for team in teams:
        tid = team.get("id")
        if not isinstance(tid, int) or tid <= 0:
            return False, f"Invalid team ID: {tid} for {team.get('full_name')}"
    return True, "All team IDs are positive integers"


def validate_year_founded_is_realistic(teams: list) -> Result:
    """
    Checks that founding years fall within a realistic NBA range (1940-2010).

    The NBA was founded in 1946, but some franchises trace their history
    to the BAA (Basketball Association of America) which started in 1946.
    I use 1940 as the lower bound to be safe.

    The upper bound of 2010 accounts for the Charlotte Hornets expansion
    (2004) and any future expansions while ruling out obviously wrong values
    like 0, 9999, or whatever the current year is.
    """
    for team in teams:
        year = team.get("year_founded", 0)
        if not (1940 <= year <= 2010):
            return False, f"{team.get('full_name')} has unrealistic founding year: {year}"
    return True, "All founding years are in realistic range"


# =============================================================================
# STANDINGS VALIDATION RULES
# These rules run against live standings data fetched from ESPN.
# Unlike the static team data, standings change daily during the season.
# =============================================================================

def validate_standings_has_data(standings_rows: list) -> Result:
    """
    Checks that the standings response isn't empty.

    During the offseason, the standings endpoint might return zero rows.
    This check flags that case so we know the other standings tests
    can be skipped (they'll be marked as "skipped" in pytest output).
    """
    if len(standings_rows) > 0:
        return True, f"Standings has {len(standings_rows)} entries"
    return False, "Standings is empty"


def validate_standings_has_30_teams(standings_rows: list) -> Result:
    """
    Checks that all 30 teams appear in the standings.

    If a team is missing from standings, it likely means the API
    returned a filtered or paginated response instead of the full data.
    This would cause us to miss data quality issues for that team.
    """
    count = len(standings_rows)
    if count == 30:
        return True, "All 30 teams present in standings"
    return False, f"Expected 30 teams in standings, got {count}"


def validate_win_loss_non_negative(standings_rows: list) -> Result:
    """
    Checks that no team has negative wins or losses.

    Wins and losses are always counts — they can be 0 (brand new season
    or no games played) but they can never be negative. A negative value
    would indicate corrupted data from the API.

    Note: I check for both "W" and "WINS" as column names because the
    nba_api response headers can vary slightly depending on the endpoint
    version being called.
    """
    for row in standings_rows:
        # Support both column name formats the API might return
        wins   = row.get("WINS", row.get("W", 0))
        losses = row.get("LOSSES", row.get("L", 0))
        team   = row.get("TeamName", row.get("TEAM_NAME", "Unknown"))
        if wins < 0:
            return False, f"{team} has negative wins: {wins}"
        if losses < 0:
            return False, f"{team} has negative losses: {losses}"
    return True, "All teams have non-negative win/loss records"


def validate_win_pct_range(standings_rows: list) -> Result:
    """
    Checks that every team's win percentage is between 0.0 and 1.0.

    Win percentage = wins / games played. So:
      - 0.0 means a team has lost every single game (0-82 record)
      - 1.0 means a team has won every single game (82-0 record)
      - Anything outside this range is mathematically impossible

    I convert to float() explicitly because the API sometimes returns
    percentages as strings (e.g. "0.573") instead of numbers.
    """
    for row in standings_rows:
        pct  = row.get("WinPCT", row.get("PCT", 0.5))
        team = row.get("TeamName", row.get("TEAM_NAME", "Unknown"))
        try:
            pct = float(pct)
            if not (0.0 <= pct <= 1.0):
                return False, f"{team} win% out of range: {pct}"
        except (TypeError, ValueError):
            return False, f"{team} has non-numeric win%: {pct}"
    return True, "All win percentages are in valid range [0.0, 1.0]"


def validate_no_duplicate_team_names_in_standings(standings_rows: list) -> Result:
    """
    Checks that no team name appears more than once in the standings.

    If the API returns duplicate rows for the same team, any stats
    based on standings (like "what's the top team?") would be wrong.
    This is an internal consistency check on the API response itself.
    """
    names = [row.get("TeamName", row.get("TEAM_NAME", "")) for row in standings_rows]
    if len(names) == len(set(names)):
        return True, "No duplicate teams in standings"
    dupes = [n for n in names if names.count(n) > 1]
    return False, f"Duplicate teams in standings: {set(dupes)}"


# =============================================================================
# ROSTER VALIDATION RULES
# These rules validate player data for a specific team's roster.
# =============================================================================

def validate_roster_not_empty(players: list) -> Result:
    """
    Checks that a team has at least 10 players on their roster.

    NBA rules require a minimum of 10 players on an active roster
    (teams can have up to 15 standard contracts + 2 two-way contracts).
    If a roster comes back with fewer than 10, the data is incomplete.
    """
    count = len(players)
    if count >= 10:
        return True, f"Roster has {count} players (>=10)"
    return False, f"Roster too small: only {count} players"


def validate_no_duplicate_player_ids(players: list) -> Result:
    """
    Checks that no two players on a roster share the same player ID.

    Like team IDs, every NBA player has a unique permanent ID.
    Duplicate IDs would mean a player is listed twice, which could
    throw off any stats aggregation or lookups by player.
    """
    ids = [p.get("PLAYER_ID", p.get("id")) for p in players if p.get("PLAYER_ID") or p.get("id")]
    if len(ids) == len(set(ids)):
        return True, f"All {len(ids)} player IDs are unique"
    dupes = [i for i in ids if ids.count(i) > 1]
    return False, f"Duplicate player IDs: {set(dupes)}"


def validate_jersey_numbers_are_numeric(players: list) -> Result:
    """
    Checks that jersey numbers are valid integers between 0 and 99.

    NBA rules allow jersey numbers 00 through 99. Some players have
    no number assigned yet (e.g. newly signed players), so an empty
    string is allowed. But if a number IS listed, it must be numeric
    and in range.

    Note: jerseys are stored as strings in the API (e.g. "23", "00")
    so I convert to int() for the range check.
    """
    for player in players:
        jersey = player.get("NUM", player.get("jersey", ""))
        if jersey and jersey.strip():
            try:
                num = int(jersey.strip())
                if not (0 <= num <= 99):
                    return False, f"Jersey #{jersey} out of range for {player.get('PLAYER', 'Unknown')}"
            except (ValueError, TypeError):
                # A jersey value that can't be converted to int is invalid
                return False, f"Non-numeric jersey '{jersey}' for {player.get('PLAYER', 'Unknown')}"
    return True, "All jersey numbers are in valid range"


def validate_players_have_names(players: list) -> Result:
    """
    Checks that every player on the roster has a non-empty name.

    A player with no name would break any display that shows the roster.
    This catches cases where the API returns a player record with a
    blank or whitespace-only name field.
    """
    for player in players:
        name = player.get("PLAYER", player.get("full_name", "")).strip()
        if not name:
            return False, f"Player with ID {player.get('PLAYER_ID', '?')} has no name"
    return True, "All players have names"


# =============================================================================
# SCOREBOARD VALIDATION RULES
# These rules validate today's live game data from the scoreboard endpoint.
# =============================================================================

def validate_game_has_two_teams(game_line_scores: list, game_id: str) -> Result:
    """
    Checks that a specific game has exactly 2 team entries in the line score.

    The line score table has one row per team per game, so each game_id
    should appear exactly twice (once for home team, once for away team).
    If it appears once, data for one team is missing. If it appears three
    or more times, there's a duplication problem.

    Args:
        game_line_scores: All line score rows across all games today
        game_id: The specific game ID to check
    """
    # Filter to just the rows that belong to this specific game
    teams_in_game = [g for g in game_line_scores if g.get("GAME_ID") == game_id]
    count = len(teams_in_game)
    if count == 2:
        return True, f"Game {game_id} has exactly 2 teams"
    return False, f"Game {game_id} has {count} team entries, expected 2"


def validate_scores_non_negative(game_line_scores: list) -> Result:
    """
    Checks that all team scores on today's scoreboard are >= 0.

    Scores are cumulative points and can never be negative. A negative
    score would indicate corrupted data. Note: "None" scores are valid
    for games that haven't started yet — I convert None to 0 using
    "or 0" so the comparison still works correctly.
    """
    for row in game_line_scores:
        # "or 0" handles the case where PTS is None (game not started)
        pts  = row.get("PTS", 0) or 0
        team = row.get("TEAM_ABBREVIATION", "?")
        if pts < 0:
            return False, f"{team} has negative score: {pts}"
    return True, "All scores are non-negative"


def validate_scoreboard_game_ids_unique(game_headers: list) -> Result:
    """
    Checks that no two games on today's scoreboard share the same game ID.

    Each game gets a unique ID from the NBA. Duplicate game IDs would
    mean the same game is being reported twice, which would corrupt
    any aggregated stats or displays that use the scoreboard.
    """
    ids = [g.get("GAME_ID") for g in game_headers if g.get("GAME_ID")]
    if len(ids) == len(set(ids)):
        return True, f"All {len(ids)} game IDs are unique"
    return False, "Duplicate game IDs found in scoreboard"
