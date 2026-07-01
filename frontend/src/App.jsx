// App.jsx — the top-level component for the dashboard.
//
// This component is responsible for:
//   1. Loading the validation results (from /results.json) when the page opens
//   2. Loading the run history (from /results-history.json) for the trend chart
//   3. Passing that data down to the smaller display components
//
// Quick refresher: useState holds values that trigger a re-render when they
// change; useEffect(fn, []) runs once when the page first loads; and data is
// handed down to child components through "props".

import { useState, useEffect } from "react";
import Header from "./components/Header.jsx";
import SummaryCards from "./components/SummaryCards.jsx";
import CategorySection from "./components/CategorySection.jsx";
import TrendChart from "./components/TrendChart.jsx";

// Fallback data shown if the JSON files can't be loaded (for example, before
// generate_report.py has ever been run). This keeps the dashboard from
// looking broken on first launch.
import fallbackResults from "./fallbackData.js";

export default function App() {
  // --- State variables ---
  // 'results' holds the latest validation run. Starts as the fallback data.
  const [results, setResults] = useState(fallbackResults);
  // 'history' holds the list of past runs for the trend chart.
  const [history, setHistory] = useState([]);
  // 'loading' tracks whether we're still fetching, so we can show a message.
  const [loading, setLoading] = useState(true);
  // 'usingLiveData' tells the user whether they're seeing real generated
  // results or the built-in sample data.
  const [usingLiveData, setUsingLiveData] = useState(false);

  // --- Load data once, when the component first appears on screen ---
  // The empty array [] at the end means "only run this once, on mount".
  useEffect(() => {
    async function loadData() {
      try {
        // Try to fetch the results file produced by generate_report.py.
        // import.meta.env.BASE_URL is "/" in local dev and "/nba-data-monitor/"
        // in the deployed GitHub Pages build, so the path works in both places.
        const res = await fetch(`${import.meta.env.BASE_URL}results.json`);
        if (res.ok) {
          const data = await res.json();
          setResults(data);
          setUsingLiveData(true);
        }
      } catch (e) {
        // If the fetch fails, we silently keep using the fallback data.
        console.log("Using built-in sample data (results.json not found).");
      }

      try {
        // Fetch the history file for the trend chart (same base-path logic).
        const res = await fetch(`${import.meta.env.BASE_URL}results-history.json`);
        if (res.ok) {
          setHistory(await res.json());
        }
      } catch (e) {
        console.log("No history file found.");
      }

      setLoading(false);
    }

    loadData();
  }, []);

  // --- Group the individual checks by their category ---
  // The raw data is a flat list of checks. For display, we want them grouped
  // into sections (Teams, Standings, Rosters). reduce() builds an object like:
  //   { Teams: [...], Standings: [...], Rosters: [...] }
  const grouped = results.checks.reduce((acc, check) => {
    if (!acc[check.category]) acc[check.category] = [];
    acc[check.category].push(check);
    return acc;
  }, {});

  return (
    <div className="app">
      {/* Top bar with the project title and last-run time */}
      <Header
        generatedAt={results.generated_at}
        usingLiveData={usingLiveData}
      />

      <main className="container">
        {/* The four stat cards: total, passing, failing, pass rate */}
        <SummaryCards summary={results.summary} />

        {/* The trend chart, only shown if we have history to display */}
        {history.length > 0 && <TrendChart history={history} />}

        {/* One section per category, each listing its rules */}
        <div className="sections">
          {Object.keys(grouped).map((category) => (
            <CategorySection
              key={category}
              category={category}
              checks={grouped[category]}
            />
          ))}
        </div>
      </main>
    </div>
  );
}
