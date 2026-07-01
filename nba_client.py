"""
nba_client.py
-------------
This file is the "data layer" of the project. Its only job is to talk
to the NBA's official stats API (stats.nba.com) and hand back data.

I'm using the `nba_api` Python package, which is an open-source wrapper
that someone built around the NBA's undocumented public endpoints.
It handles all the HTTP request complexity so I can just call clean
Python methods and get data back.

No API key is needed — the NBA exposes this data publicly.
"""

# nba_api.stats.static contains locally-stored reference data (team names,
# IDs, cities, etc.) that never changes. Calling get_teams() here does NOT
# make a network request — it just reads from a bundled JSON file.
from nba_api.stats.static import teams as static_teams

# These are the "endpoint" classes. Each one wraps a specific NBA stats URL.
# When you instantiate one (e.g. LeagueStandings()), it fires an HTTP request
# to stats.nba.com and stores the response. You then call .get_data_frame()
# or .get_dict() to access the data in a format you want.
from nba_api.stats.endpoints import (
    leaguestandings,    # Current W/L records for all 30 teams
    commonteamroster,   # Player roster for a specific team
    scoreboardv2,       # Today's games, scores, and game status
    leaguegamefinder,   # Search for games by team, date range, etc.
)
import time      # Used to measure how long API calls take
import requests  # nba_api uses this under the hood; we catch its timeout errors

# stats.nba.com is notoriously flaky — it will sometimes accept a connection
# and then just hang until the request times out. These settings give each
# call a bounded wait and a couple of automatic retries so that transient
# hiccups don't crash the whole run.
REQUEST_TIMEOUT = 20   # seconds to wait for a single response before giving up
MAX_RETRIES     = 3    # total attempts per call before raising the error


def _with_retries(make_call):
    """
    Run an nba_api endpoint call, retrying on transient network timeouts.

    `make_call` is a zero-argument function (usually a lambda) that performs
    one attempt. If it times out or the connection drops, we wait briefly and
    try again, up to MAX_RETRIES times. If every attempt fails we re-raise the
    last error so the caller can decide how to handle it (see generate_report,
    which falls back to the existing data instead of crashing).
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return make_call()
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  NBA API timed out (attempt {attempt}/{MAX_RETRIES}) - retrying...")
                time.sleep(2)
    raise last_error


class NBAClient:
    """
    A wrapper class around nba_api endpoints.

    I created this class so that the rest of the codebase (the tests and
    generate_report.py) never has to know HOW we get NBA data — just that
    they can ask this class for it. If the nba_api package ever changes,
    I only need to fix it here, not everywhere.

    This pattern is called the "Repository Pattern" in software engineering.
    """

    def get_all_teams(self) -> list:
        """
        Returns a list of all 30 NBA teams as Python dictionaries.

        This is a static call — no network request is made. The nba_api
        package ships with a bundled teams.json file that contains:
          - id           (e.g. 1610612747 for the Lakers)
          - full_name    (e.g. "Los Angeles Lakers")
          - abbreviation (e.g. "LAL")
          - nickname     (e.g. "Lakers")
          - city         (e.g. "Los Angeles")
          - state        (e.g. "California")
          - year_founded (e.g. 1948)

        Because this never hits the network, it's always fast and
        never fails due to connectivity issues.
        """
        return static_teams.get_teams()

    def get_standings(self) -> dict:
        """
        Fetches the current NBA standings and returns raw JSON as a dict.

        The raw response structure from the NBA API looks like:
          {
            "resultSets": [
              {
                "name": "Standings",
                "headers": ["TeamID", "TeamName", "W", "L", "WinPCT", ...],
                "rowSet": [[...], [...], ...]   <- one row per team
              }
            ]
          }

        I use this raw format when I want JSON that serializes cleanly for
        the dashboard to read.
        """
        s = _with_retries(lambda: leaguestandings.LeagueStandings(timeout=REQUEST_TIMEOUT))
        return s.get_dict()

    def get_standings_df(self):
        """
        Same standings data as get_standings(), but returned as a
        pandas DataFrame instead of a raw dict.

        DataFrames are much easier to work with in Python — you can
        filter rows, sort columns, rename headers, etc. I use this
        format in the pytest test suite since it's easier to validate.

        Example of what a row looks like after conversion:
          TeamID | TeamName       | W  | L  | WinPCT | ...
          -------|----------------|----|----|--------|----
          1610..  | Lakers        | 47 | 35 | 0.573  | ...
        """
        s = _with_retries(lambda: leaguestandings.LeagueStandings(timeout=REQUEST_TIMEOUT))
        return s.standings.get_data_frame()

    def get_roster(self, team_id: int) -> dict:
        """
        Fetches the full roster for a team, given their NBA team ID.

        The team_id is a specific number the NBA assigns to each team.
        For example:
          - Lakers  = 1610612747
          - Celtics = 1610612738
          - Warriors = 1610612744

        You can find all IDs using get_all_teams() above.

        Returns a raw, JSON-serializable dict for the dashboard.
        """
        r = _with_retries(lambda: commonteamroster.CommonTeamRoster(
            team_id=team_id, timeout=REQUEST_TIMEOUT))
        return r.get_dict()

    def get_roster_df(self, team_id: int):
        """
        Same as get_roster() but returns a pandas DataFrame.

        Each row in the DataFrame is one player. Columns include:
          PLAYER_ID, PLAYER (full name), NUM (jersey number),
          POSITION, HEIGHT, WEIGHT, AGE, EXP (years experience), etc.

        Used in the test suite so we can easily validate individual
        fields like jersey numbers and player names.
        """
        r = _with_retries(lambda: commonteamroster.CommonTeamRoster(
            team_id=team_id, timeout=REQUEST_TIMEOUT))
        return r.common_team_roster.get_data_frame()

    def get_scoreboard(self) -> dict:
        """
        Fetches today's NBA scoreboard — all games scheduled for today,
        including live scores if games are currently in progress.

        The response contains multiple "result sets" (sub-tables):
          - GameHeader: one row per game with status, arena, etc.
          - LineScore: one row per team per game with current score
          - SeriesStandings: playoff series info (if applicable)
          - LastMeeting: last time these two teams played each other
          - EastConfStandings / WestConfStandings: quick standings view

        I return the raw dict here because it serializes cleanly to JSON
        for the React dashboard to read.
        """
        s = _with_retries(lambda: scoreboardv2.ScoreboardV2(timeout=REQUEST_TIMEOUT))
        return s.get_dict()

    def get_response_time(self) -> float:
        """
        Measures how long it takes the standings endpoint to respond.

        This is used in the integration tests to make sure the NBA API
        is responding within an acceptable time window (< 3 seconds).
        If this test starts failing, it could mean the API is slow or
        the server running the tests has poor connectivity.

        Returns the elapsed time in seconds as a float.
        """
        start = time.time()
        _with_retries(lambda: leaguestandings.LeagueStandings(timeout=REQUEST_TIMEOUT))
        return time.time() - start
