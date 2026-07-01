"""
generate_report.py
------------------
This script runs every data quality rule against LIVE NBA data and
writes the results to a JSON file that the React dashboard reads.

Run it from the project root with:
    python generate_report.py

What it produces:
  frontend/public/results.json
      A snapshot of the latest run: a timestamp, summary counts, and
      every rule's pass/fail status grouped by category. The dashboard
      fetches this file and displays it.

  frontend/public/results-history.json
      A running log of past runs (capped at the 30 most recent). Each
      entry is just the summary numbers. The dashboard uses this to draw
      the "pass rate over time" trend chart.

Why a JSON file instead of a live connection?
  The React dashboard is a pure frontend app — it can't run Python or
  call the NBA API directly (browsers block cross-origin API calls, and
  my validators are written in Python). So this script acts as the
  bridge: Python does the work and saves the results; React just reads
  and displays them. Re-run this script whenever you want fresh data.
"""

import json
import os
import sys
from datetime import datetime, timezone

import requests   # used only to catch the NBA API's network errors

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
)

# Where to write the output files (inside the frontend's public folder
# so Vite serves them to the dashboard at /results.json).
PUBLIC_DIR   = os.path.join(os.path.dirname(__file__), "frontend", "public")
RESULTS_FILE = os.path.join(PUBLIC_DIR, "results.json")
HISTORY_FILE = os.path.join(PUBLIC_DIR, "results-history.json")

# Max number of past runs to keep in the history log.
HISTORY_LIMIT = 30

LAKERS_ID = 1610612747


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


def main():
    print("Fetching live NBA data and running validation rules...\n")
    client = NBAClient()

    # --- Fetch all the data we need up front ---
    # get_all_teams() reads bundled data and never hits the network, so it's
    # safe outside the try. The standings and roster calls DO hit stats.nba.com,
    # which can hang/time out (it geo-blocks and rate-limits aggressively). If
    # that happens we don't want a wall of red traceback — we keep whatever
    # results.json already exists so the dashboard still works, and exit cleanly.
    teams = client.get_all_teams()
    try:
        standings = client.get_standings_df().to_dict("records")
        roster = client.get_roster_df(LAKERS_ID).to_dict("records")
    except requests.exceptions.RequestException as e:
        print("\nCould not reach the live NBA API (stats.nba.com).")
        print(f"  Reason: {e.__class__.__name__} - the server accepted the")
        print("  connection but never sent data back. This is almost always the")
        print("  NBA blocking/rate-limiting your network, not a bug in this code.\n")
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

        # Roster rules (spot-checking the Lakers)
        run_check("Rosters", "Roster is not empty (>=10 players)",
                  validate_roster_not_empty, roster),
        run_check("Rosters", "No duplicate player IDs",
                  validate_no_duplicate_player_ids, roster),
        run_check("Rosters", "Jersey numbers are valid",
                  validate_jersey_numbers_are_numeric, roster),
        run_check("Rosters", "All players have names",
                  validate_players_have_names, roster),
    ]

    # --- Summarize ---
    total  = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    failed = total - passed
    pass_rate = round((passed / total) * 100, 1) if total else 0
    timestamp = datetime.now(timezone.utc).isoformat()

    results = {
        "generated_at": timestamp,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
        },
        "checks": checks,
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
