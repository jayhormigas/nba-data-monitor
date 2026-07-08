"""
generate_report.py
------------------
This script runs every data quality rule against LIVE NBA data and
writes the results to a JSON file that the React dashboard reads.

Run it from the project root with:
    python generate_report.py

What it produces:
  frontend/public/results.json
      A snapshot of the latest run: a timestamp, summary counts, every
      rule's pass/fail status grouped by category, and the raw data tables
      (teams, standings, rosters, games) behind the dashboard's "Show data"
      panels. The dashboard fetches this file and displays it.

  frontend/public/results-history.json
      A running log of past runs (capped at the 30 most recent). Each
      entry is just the summary numbers. The dashboard uses this to draw
      the "pass rate over time" trend chart.

Why a JSON file instead of a live connection?
  The React dashboard is a pure frontend app — it can't run Python or
  call the live API directly (browsers block cross-origin API calls, and
  my validators are written in Python). So this script acts as the
  bridge: Python does the work and saves the results; React just reads
  and displays them. Re-run this script whenever you want fresh data.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests   # used only to catch ESPN's network errors

from nba_client import NBAClient
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

# Where to write the output files (inside the frontend's public folder
# so Vite serves them to the dashboard at /results.json).
PUBLIC_DIR   = os.path.join(os.path.dirname(__file__), "frontend", "public")
RESULTS_FILE = os.path.join(PUBLIC_DIR, "results.json")
HISTORY_FILE = os.path.join(PUBLIC_DIR, "results-history.json")

# Max number of past runs to keep in the history log.
HISTORY_LIMIT = 30


def run_check(category, name, validator_fn, data):
    """
    Runs a single validation rule and packages the result into a dict
    that's easy for the dashboard to render.

    Returns something like:
      {"category": "Teams", "rule": "All team IDs are unique",
       "passed": True, "message": "All team IDs are unique"}
    """
    passed, message = validator_fn(data)
    return {
        "category": category,
        "rule": name,
        "passed": passed,
        "message": message,
    }


def run_roster_check(name, validator_fn, rosters, ok_message):
    """
    Run one roster rule against every team's roster. Passes only if all 30
    rosters pass; on the first failure it reports which team broke the rule.
    """
    for team_name, players in rosters.items():
        passed, message = validator_fn(players)
        if not passed:
            return {"category": "Rosters", "rule": name,
                    "passed": False, "message": f"{team_name}: {message}"}
    return {"category": "Rosters", "rule": name,
            "passed": True, "message": ok_message}


def main():
    print("Fetching live NBA data and running validation rules...\n")
    client = NBAClient()

    # --- Fetch all the data we need up front ---
    # get_all_teams() reads bundled data and never hits the network, so it's
    # safe outside the try. Standings, rosters, and the scoreboard come from
    # ESPN, which is reliable — but if it's ever unreachable we don't want a
    # wall of red traceback. We keep whatever results.json already exists so the
    # dashboard still works, and exit cleanly.
    teams = client.get_all_teams()
    try:
        standings = client.get_standings_df().to_dict("records")
        scoreboard = client.get_scoreboard()
        # Fetch every team's roster (one quick ESPN call each) so the monitor
        # validates the whole league, not just one team. Keyed by team name.
        print("  Fetching all 30 rosters from ESPN...")
        rosters = {t["full_name"]: client.get_roster_df(t["id"]).to_dict("records")
                   for t in teams}
    except requests.exceptions.RequestException as e:
        print("\nCould not reach the live NBA data source (ESPN).")
        print(f"  Reason: {e.__class__.__name__}.\n")
        if os.path.exists(RESULTS_FILE):
            print("Good news: an existing results file is already in place, so the")
            print("dashboard will still work with the most recent data.")
            print(f"  ({RESULTS_FILE})")
        else:
            print("No results file exists yet, so the dashboard will fall back to")
            print("its built-in sample data when you start it.")
        print("\nTo view the dashboard now:")
        print("  cd frontend")
        print("  npm run dev")
        sys.exit(0)   # not a crash — this is an expected, handled outcome

    # Pull the scoreboard's two sub-tables (GameHeader, LineScore) into plain
    # lists of dicts so the scoreboard validators can read them by column name.
    result_sets = scoreboard.get("resultSets", [])

    def scoreboard_table(name):
        table = next((rs for rs in result_sets if rs.get("name") == name),
                     {"headers": [], "rowSet": []})
        columns = table.get("headers", [])
        return [dict(zip(columns, row)) for row in table.get("rowSet", [])]

    game_headers = scoreboard_table("GameHeader")   # [{"GAME_ID": ...}, ...]
    line_scores  = scoreboard_table("LineScore")    # [{"GAME_ID","TEAM_ABBREVIATION","PTS"}]
    game_ids     = [g["GAME_ID"] for g in game_headers]

    # --- Run every rule, collecting the results in a list ---
    checks = [
        # Team rules
        run_check("Teams", "League has exactly 30 teams",
                  validate_league_has_30_teams, teams),
        run_check("Teams", "No duplicate team IDs",
                  validate_no_duplicate_team_ids, teams),
        run_check("Teams", "All teams have required fields",
                  validate_team_required_fields, teams),
        run_check("Teams", "All abbreviations are valid",
                  validate_team_abbreviations_are_valid, teams),
        run_check("Teams", "All team IDs are positive integers",
                  validate_team_ids_are_positive_integers, teams),
        run_check("Teams", "Founding years are realistic",
                  validate_year_founded_is_realistic, teams),

        # Standings rules
        run_check("Standings", "Standings contains data",
                  validate_standings_has_data, standings),
        run_check("Standings", "All 30 teams present in standings",
                  validate_standings_has_30_teams, standings),
        run_check("Standings", "Win/loss totals are non-negative",
                  validate_win_loss_non_negative, standings),
        run_check("Standings", "Win percentages are in valid range",
                  validate_win_pct_range, standings),
        run_check("Standings", "No duplicate teams in standings",
                  validate_no_duplicate_team_names_in_standings, standings),

        # Roster rules — run against ALL 30 teams' rosters, not just one
        run_roster_check("Every roster has 10+ players",
                         validate_roster_not_empty, rosters,
                         "All 30 rosters have at least 10 players"),
        run_roster_check("No duplicate player IDs",
                         validate_no_duplicate_player_ids, rosters,
                         "No duplicate player IDs in any of the 30 rosters"),
        run_roster_check("Jersey numbers are valid",
                         validate_jersey_numbers_are_numeric, rosters,
                         "All jersey numbers valid across all 30 rosters"),
        run_roster_check("All players have names",
                         validate_players_have_names, rosters,
                         "Every player on all 30 rosters has a name"),

        # Scoreboard rules (today's games; an empty scoreboard in the
        # offseason still passes these cleanly)
        run_check("Scoreboard", "Game IDs are unique",
                  validate_scoreboard_game_ids_unique, game_headers),
        run_check("Scoreboard", "Scores are non-negative",
                  validate_scores_non_negative, line_scores),
    ]

    # The "2 teams per game" rule applies to a single game at a time, so run it
    # across every game today and pass only if they all check out (vacuously
    # true when there are no games scheduled).
    if game_ids:
        two_teams_ok, two_teams_msg = True, f"All {len(game_ids)} games have exactly 2 teams"
        for gid in game_ids:
            ok, msg = validate_game_has_two_teams(line_scores, gid)
            if not ok:
                two_teams_ok, two_teams_msg = False, msg
                break
    else:
        two_teams_ok, two_teams_msg = True, "No games scheduled today - nothing to validate"
    checks.append({
        "category": "Scoreboard",
        "rule": "Every game has exactly 2 teams",
        "passed": two_teams_ok,
        "message": two_teams_msg,
    })

    # --- Summarize ---
    total  = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    failed = total - passed
    pass_rate = round((passed / total) * 100, 1) if total else 0
    timestamp = datetime.now(timezone.utc).isoformat()

    # Raw data behind the rules, so the dashboard can show it for anyone who
    # wants to eyeball the actual numbers each check ran against.
    games = []
    for gid in game_ids:
        rows  = [ls for ls in line_scores if ls.get("GAME_ID") == gid]
        abbrs = " vs ".join(r.get("TEAM_ABBREVIATION", "?") for r in rows)
        score = " - ".join(str(r.get("PTS", "")) for r in rows)
        games.append({"matchup": abbrs or str(gid), "score": score})

    data = {
        "teams": [{"team": t["full_name"], "abbr": t["abbreviation"],
                   "city": t["city"], "state": t["state"],
                   "founded": t["year_founded"]} for t in teams],
        "standings": [{"team": s["TeamName"], "wins": s["WINS"],
                       "losses": s["LOSSES"], "win_pct": s["WinPCT"]}
                      for s in standings],
        "rosters": [{"team": team_name, "number": p.get("NUM", ""),
                     "player": p.get("PLAYER", "")}
                    for team_name, players in rosters.items() for p in players],
        "games": games,
    }

    results = {
        "generated_at": timestamp,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        },
        "checks": checks,
        "data": data,
    }

    # Make sure the output folder exists, then write the results file.
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    # --- Update the history log ---
    # Read whatever history already exists (or start fresh if none).
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f:
                history = json.load(f)
        except (json.JSONDecodeError, ValueError):
            history = []   # corrupted/empty file — just start over

    history.append({
        "generated_at": timestamp,
        "pass_rate": pass_rate,
        "passed": passed,
        "failed": failed,
    })
    history = history[-HISTORY_LIMIT:]   # keep only the most recent runs

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    # --- Print a readable summary to the terminal ---
    for c in checks:
        icon = "PASS" if c["passed"] else "FAIL"
        print(f"  [{icon}] {c['category']:10} | {c['rule']}")
    print(f"\n{passed}/{total} checks passed ({pass_rate}%)")
    print(f"Results written to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
