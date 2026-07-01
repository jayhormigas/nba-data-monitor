# NBA Stats Validation Suite

An automated data-quality framework that runs validation rules against the
**official NBA stats API** and visualizes the results in a React dashboard.

---

## What it does

Pulls live NBA data (teams, standings, rosters, and the daily scoreboard) and
runs **18 data-quality rules** against it, catching issues such as:

- Wrong number of teams in the league or a conference
- Negative scores or win/loss records
- Duplicate team or player IDs
- Jersey numbers outside the valid 0-99 range
- Win percentages outside the mathematically possible 0.0-1.0 range
- Missing required fields
- Duplicate game IDs on the scoreboard
- The NBA API silently changing its response structure (contract tests)

Results are shown three ways: the **pytest test suite** (pass/fail in the
terminal + an HTML report), and a **React dashboard** that displays every
rule's status with category breakdowns and a pass-rate trend chart.

---

## Tech stack

| Part | Technology |
|------|------------|
| Data source | `nba_api` (official NBA stats, no API key needed) |
| Validation logic | Python — pure, fully unit-tested functions |
| Test suite | `pytest` (unit, integration, contract) + `pytest-cov` |
| Dashboard | React + Vite |
| CI/CD | GitHub Actions, runs daily on a cron schedule |

---

## Project structure

```
nba-data-monitor/
├── nba_client.py          # Talks to the NBA API (the data layer)
├── validators.py          # The 18 data-quality rules (pure functions)
├── generate_report.py     # Runs rules on live data -> writes JSON for the dashboard
├── requirements.txt
├── pytest.ini
├── .github/workflows/
│   └── ci.yml             # Daily automated test pipeline
├── tests/
│   ├── unit/              # 57 tests, fake data, no network
│   ├── integration/       # Live NBA API data-quality checks
│   └── contract/          # Detects NBA API schema changes
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

1. `nba_client.py` fetches raw data from the NBA API.
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

Run the full suite (needs internet — hits the live NBA API):

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
| Integration | 24 | Rules run against live Lakers/Celtics rosters, standings, scoreboard |
| Contract | 14 | Confirms the NBA API still returns the expected structure |

---

## CI/CD

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs:

- on every push and pull request to `main`, and
- automatically every day at 9:00 AM EST via a cron schedule.

It runs the unit tests first, then the live integration + contract tests, and
uploads the HTML test report as a build artifact.

---

## Concepts demonstrated

- **Data-quality testing** against a real production API
- **Test isolation** with hand-built mock data (unit tests never touch the network)
- **Contract testing** to catch breaking changes in a third-party API
- **Session-scoped fixtures** so live data is fetched once, not per test
- **Scheduled CI** (cron) rather than only push-triggered runs
- **Separation of concerns** — data layer, rules, tests, and UI are decoupled
