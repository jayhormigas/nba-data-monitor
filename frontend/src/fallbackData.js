// fallbackData.js — built-in sample data.
//
// The dashboard tries to load real results from /results.json (which is
// created when you run generate_report.py). If that file doesn't exist yet,
// the dashboard falls back to this sample so it still renders something
// meaningful on first launch instead of an empty screen.
//
// Once you run `python generate_report.py`, the real results.json takes over.

const fallbackResults = {
  generated_at: null,
  summary: { total: 15, passed: 15, failed: 0, pass_rate: 100.0 },
  checks: [
    { category: "Teams", rule: "League has exactly 30 teams", passed: true, message: "League has exactly 30 teams" },
    { category: "Teams", rule: "No duplicate team IDs", passed: true, message: "All team IDs are unique" },
    { category: "Teams", rule: "All teams have required fields", passed: true, message: "All teams have required fields" },
    { category: "Teams", rule: "All abbreviations are valid", passed: true, message: "All abbreviations are valid" },
    { category: "Teams", rule: "All team IDs are positive integers", passed: true, message: "All team IDs are positive integers" },
    { category: "Teams", rule: "Founding years are realistic", passed: true, message: "All founding years are in realistic range" },
    { category: "Standings", rule: "Standings contains data", passed: true, message: "Standings has 30 entries" },
    { category: "Standings", rule: "All 30 teams present in standings", passed: true, message: "All 30 teams present in standings" },
    { category: "Standings", rule: "Win/loss totals are non-negative", passed: true, message: "All teams have non-negative win/loss records" },
    { category: "Standings", rule: "Win percentages are in valid range", passed: true, message: "All win percentages are in valid range [0.0, 1.0]" },
    { category: "Standings", rule: "No duplicate teams in standings", passed: true, message: "No duplicate teams in standings" },
    { category: "Rosters", rule: "Roster is not empty (>=10 players)", passed: true, message: "Roster has 17 players (>=10)" },
    { category: "Rosters", rule: "No duplicate player IDs", passed: true, message: "All 17 player IDs are unique" },
    { category: "Rosters", rule: "Jersey numbers are valid", passed: true, message: "All jersey numbers are in valid range" },
    { category: "Rosters", rule: "All players have names", passed: true, message: "All players have names" },
  ],
};

export default fallbackResults;
