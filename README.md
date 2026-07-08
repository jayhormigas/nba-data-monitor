# NBA Stats Validation Suite

An automated data-quality framework that pulls **live NBA data** from ESPN's
public API, runs 18 validation rules against it, and publishes the results to
a React dashboard that refreshes itself every day.

**[View the live dashboard →](https://jayhormigas.github.io/nba-data-monitor/)**

---

## What it does

Pulls live NBA data (teams, standings, all 30 team rosters, and the daily
scoreboard) and runs **18 data-quality rules** against it, catching issues
such as:

- Wrong number of teams in the league or a conference
- Negative scores or win/loss records
- Duplicate team or player IDs
- Jersey numbers outside the valid 0-99 range
- Win percentages outside the mathematically possible 0.0-1.0 range
- Missing required fields
- Duplicate game IDs on the scoreboard
- The data source silently changing its response structure (contract tests)

Results show up in three places: the **pytest test suite** (pass/fail in the
terminal), the **HTML test report** CI uploads as an artifact, and a **React
dashboard** that displays every rule's status with category breakdowns, a
pass-rate trend chart, and expandable "Show data" panels holding the raw
numbers behind each category — so anyone can verify a check by hand.

---

## Tech stack

| Part | Technology |
|------|------------|
| Data source | ESPN's public NBA API (standings, rosters, scoreboard) + `nba_api` static team data — no API key needed |
| Validation logic | Python — pure, fully unit-tested functions |
| Test suite | `pytest` (unit, integration, contract) + `pytest-cov` |
| Dashboard | React + Vite |
| CI/CD | GitHub Actions — daily tests + daily data refresh, deployed to GitHub Pages |

---

## Project structure

```
nba-data-monitor/
├── nba_client.py          # Fetches live data from ESPN (the data layer)
├── validators.py          # The 18 data-quality rules (pure functions)
├── generate_report.py     # Runs rules on live data -> writes JSON for the dashboard
├── requirements.txt
├── pytest.ini
├── .github/workflows/
│   ├── ci.yml             # Daily automated test pipeline
│   └── deploy.yml         # Daily data refresh + GitHub Pages deploy
├── tests/
│   ├── unit/              # 57 tests, fake data, no network
│   ├── integration/       # Live-data quality checks against ESPN
│   └── contract/          # Detects data-source schema changes
└── frontend/              # React dashboard (Vite)
    ├── src/
    │   ├── App.jsx
    │   ├── components/
    │   └── styles.css
    └── public/
        ├── results.json          # Latest run (created by generate_report.py)
        └── results-history.json  # Past runs for the trend chart
```

---

## How the pieces fit together

1. `nba_client.py` fetches live data from ESPN's public NBA endpoints and
   normalizes it into the shapes the validators expect.
2. `validators.py` defines the rules that decide whether data is valid.
3. The **test suite** runs those rules against live data and fails loudly if
   anything is wrong.
4. `generate_report.py` runs the same rules and saves the results as JSON.
5. The **React dashboard** reads that JSON and displays it visually.

---

## Setup

### 1. Python side

```bash
pip install -r requirements.txt
```

Run the unit tests (fast, no internet needed):

```bash
python -m pytest tests/unit/ -v
```

Run the full suite (needs internet — hits ESPN's live API):

```bash
python -m pytest -v
```

### 2. Generate dashboard data (optional, needs internet)

```bash
python generate_report.py
```

This writes the latest results into `frontend/public/`. If you skip this step,
the dashboard shows built-in sample data instead.

### 3. Frontend side

```bash
cd frontend
npm install
npm run dev
```

Then open the URL it prints (usually http://localhost:3000).

---

## Test coverage

| Layer | Tests | Purpose |
|-------|-------|---------|
| Unit | 57 | Every rule tested with fake data, including edge cases |
| Integration | 23 | Rules run against live Lakers/Celtics rosters, standings, scoreboard |
| Contract | 14 | Confirms the data layer still returns the expected structure |

---

## CI/CD

Two GitHub Actions workflows run on every push to `main` and daily at
9:00 AM EST (14:00 UTC):

- **`ci.yml` — the test pipeline.** Runs the unit tests first, then the live
  integration + contract tests, and uploads the HTML test report and coverage
  as build artifacts.
- **`deploy.yml` — the refresh + deploy pipeline.** Re-runs all 18 rules
  against that morning's live data, rebuilds the React dashboard, publishes it
  to GitHub Pages (with an automatic retry if GitHub's deploy backend hiccups),
  and commits the refreshed results back so the trend chart accumulates real
  history.

---

## Concepts demonstrated

- **Data-quality testing** against a real production API
- **Test isolation** with hand-built mock data (unit tests never touch the network)
- **Contract testing** to catch breaking changes in a third-party API
- **Session-scoped fixtures** so live data is fetched once, not per test
- **Scheduled CI/CD** (cron) — daily test runs and a self-refreshing deployed dashboard
- **Separation of concerns** — data layer, rules, tests, and UI are decoupled
