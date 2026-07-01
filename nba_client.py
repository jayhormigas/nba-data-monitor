"""
nba_client.py
-------------
This file is the "data layer" of the project. Its only job is to fetch live
NBA data and hand it back in a consistent shape, so the rest of the codebase
(validators, tests, generate_report) never has to care where the data comes
from.

Data sources:
  - Team list: the `nba_api` package's bundled STATIC team data. This is local
    (no network call) and includes fields we validate, like city, state, and
    founding year.
  - Standings, rosters, and scoreboard: ESPN's public NBA endpoints
    (site.api.espn.com). No API key needed, and — unlike stats.nba.com — they
    respond reliably from cloud servers like GitHub Actions.

Everything gets normalized here into the same field names the validators
expect (e.g. TeamName / WINS / LOSSES / WinPCT for standings). That way, if the
data source ever changes again, this is the only file that has to change.
This is the "Repository Pattern" — the rest of the app depends on the shape,
not the source.
"""

import time
import requests
import pandas as pd

# nba_api ships a bundled teams.json (names, ids, cities, founding years). Reading
# it makes NO network request, so the team list is always fast and available.
from nba_api.stats.static import teams as static_teams

# --- ESPN endpoints ---------------------------------------------------------
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
# level=3 returns standings nested by conference/division; we flatten it below.
ESPN_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?level=3"

# A browser-like User-Agent keeps ESPN happy.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 20   # seconds to wait for a single response before giving up
MAX_RETRIES     = 3    # total attempts per call before raising the error


def _with_retries(make_call):
    """
    Run a network call, retrying a couple of times on transient timeouts.

    `make_call` is a zero-argument function that performs one attempt. If every
    attempt fails we re-raise the last error so the caller can decide what to do
    (generate_report falls back to the existing data instead of crashing).
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return make_call()
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt < MAX_RETRIES:
                print(f"  ESPN request timed out (attempt {attempt}/{MAX_RETRIES}) - retrying...")
                time.sleep(2)
    raise last_error


def _get_json(url):
    """GET a URL and return parsed JSON, with the retry/timeout policy applied."""
    def call():
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    return _with_retries(call)


def _collect_standings_entries(node, acc):
    """
    Walk ESPN's nested standings tree and collect every team "entry".

    ESPN groups standings by conference and division, so the team rows are
    buried at different depths. This recursively gathers them all; the caller
    de-duplicates by team id.
    """
    if isinstance(node, dict):
        standings = node.get("standings")
        if isinstance(standings, dict) and "entries" in standings:
            acc.extend(standings["entries"])
        for value in node.values():
            _collect_standings_entries(value, acc)
    elif isinstance(node, list):
        for value in node:
            _collect_standings_entries(value, acc)


# Cache of {team nickname (lowercased): ESPN team id}, built once on first use.
_ESPN_TEAM_ID_CACHE = None


def _espn_team_id_map():
    """Return {nickname_lower: espn_id}, e.g. {"lakers": "13"}. Fetched once."""
    global _ESPN_TEAM_ID_CACHE
    if _ESPN_TEAM_ID_CACHE is None:
        data = _get_json(f"{ESPN_BASE}/teams")
        mapping = {}
        for wrapper in data["sports"][0]["leagues"][0]["teams"]:
            team = wrapper["team"]
            mapping[team["name"].lower()] = team["id"]   # ESPN "name" is the nickname
        _ESPN_TEAM_ID_CACHE = mapping
    return _ESPN_TEAM_ID_CACHE


def _nba_id_to_espn_id(nba_team_id):
    """
    Translate an nba_api team id (e.g. 1610612747) into ESPN's team id (e.g. 13).

    nba_api and ESPN use totally different team ids, so we bridge them by the
    team's nickname ("Lakers"), which both sources agree on.
    """
    nickname = next((t["nickname"] for t in static_teams.get_teams()
                     if t["id"] == nba_team_id), None)
    if nickname is None:
        raise ValueError(f"Unknown nba_api team id: {nba_team_id}")
    espn_id = _espn_team_id_map().get(nickname.lower())
    if espn_id is None:
        raise ValueError(f"No ESPN team found for nickname '{nickname}'")
    return espn_id


class NBAClient:
    """
    A thin wrapper that fetches NBA data and normalizes it for the validators.

    The rest of the codebase (the tests and generate_report.py) only ever talks
    to this class, so it never has to know the data actually comes from ESPN.
    """

    def get_all_teams(self) -> list:
        """
        All 30 NBA teams as dicts (id, full_name, abbreviation, city, state,
        year_founded, ...).

        Static/local — no network request, so it never fails on connectivity.
        """
        return static_teams.get_teams()

    def get_standings(self) -> dict:
        """Raw ESPN standings JSON (used rarely; the _df version is the main one)."""
        return _get_json(ESPN_STANDINGS_URL)

    def get_standings_df(self):
        """
        Current standings as a pandas DataFrame with the columns the validators
        expect: TeamName, WINS, LOSSES, WinPCT (one row per team).

        DataFrames are convenient downstream — callers do .to_dict("records")
        to get a plain list of per-team dicts.
        """
        data = _get_json(ESPN_STANDINGS_URL)

        entries = []
        _collect_standings_entries(data, entries)

        # De-dupe by team id (the tree can list a team at more than one level).
        by_team = {e.get("team", {}).get("id"): e for e in entries}

        rows = []
        for entry in by_team.values():
            stats = {s.get("name"): s.get("value") for s in entry.get("stats", [])}
            rows.append({
                "TeamName": entry["team"]["displayName"],
                "WINS":   int(stats.get("wins", 0)),
                "LOSSES": int(stats.get("losses", 0)),
                "WinPCT": float(stats.get("winPercent", 0.0)),
            })
        return pd.DataFrame(rows)

    def get_roster(self, nba_team_id: int) -> dict:
        """Raw ESPN roster JSON for a team (the _df version is the main one)."""
        espn_id = _nba_id_to_espn_id(nba_team_id)
        return _get_json(f"{ESPN_BASE}/teams/{espn_id}/roster")

    def get_roster_df(self, nba_team_id: int):
        """
        A team's roster as a pandas DataFrame with the columns the validators
        expect: PLAYER_ID, PLAYER (full name), NUM (jersey). One row per player.

        Takes an nba_api team id (like the LAKERS_ID constant used elsewhere)
        and translates it to ESPN's id internally.
        """
        espn_id = _nba_id_to_espn_id(nba_team_id)
        data = _get_json(f"{ESPN_BASE}/teams/{espn_id}/roster")

        athletes = data.get("athletes", [])
        # ESPN sometimes returns a flat list, sometimes groups by position with
        # an "items" list inside each group. Handle both.
        if athletes and isinstance(athletes[0], dict) and "items" in athletes[0]:
            players = [p for group in athletes for p in group.get("items", [])]
        else:
            players = athletes

        rows = [{
            "PLAYER_ID": p.get("id"),
            "PLAYER":    p.get("fullName") or p.get("displayName") or "",
            "NUM":       str(p.get("jersey") or ""),
        } for p in players]
        return pd.DataFrame(rows)

    def get_scoreboard(self) -> dict:
        """
        Today's games, reshaped into the same structure stats.nba.com used, so
        the existing scoreboard validators and tests keep working unchanged:

            {"resultSets": [
                {"name": "GameHeader", "headers": ["GAME_ID"], "rowSet": [...]},
                {"name": "LineScore",
                 "headers": ["GAME_ID", "TEAM_ABBREVIATION", "PTS"], "rowSet": [...]},
            ]}

        Both tables are always present (empty rowSet on days with no games), so
        the contract tests that look for "GameHeader"/"LineScore" always pass.
        """
        data = _get_json(f"{ESPN_BASE}/scoreboard")
        events = data.get("events", [])

        game_header_rows = []
        line_score_rows = []
        for event in events:
            game_id = event.get("id")
            game_header_rows.append([game_id])

            competition = (event.get("competitions") or [{}])[0]
            for competitor in competition.get("competitors", []):
                abbr = competitor.get("team", {}).get("abbreviation", "?")
                # ESPN returns score as a string ("94"); coerce to int for the
                # non-negative check. Missing/blank scores become 0.
                try:
                    pts = int(competitor.get("score"))
                except (TypeError, ValueError):
                    pts = 0
                line_score_rows.append([game_id, abbr, pts])

        return {
            "resultSets": [
                {"name": "GameHeader",
                 "headers": ["GAME_ID"],
                 "rowSet": game_header_rows},
                {"name": "LineScore",
                 "headers": ["GAME_ID", "TEAM_ABBREVIATION", "PTS"],
                 "rowSet": line_score_rows},
            ]
        }

    def get_response_time(self) -> float:
        """
        Measure how long the standings endpoint takes to respond, in seconds.
        Used by the integration tests to sanity-check the API is responsive.
        """
        start = time.time()
        _get_json(ESPN_STANDINGS_URL)
        return time.time() - start
