// TrendChart.jsx — a simple bar chart showing pass rate over recent runs.
//
// I drew this with plain SVG instead of pulling in a charting library. That
// keeps the project's dependencies minimal (just React) and shows the chart
// is genuinely hand-built. Each bar is one past run; its height represents
// that run's pass rate (0-100%).
//
// Props:
//   - history: an array of past runs, each like
//       { generated_at: "...", pass_rate: 100.0, passed: 15, failed: 0 }

export default function TrendChart({ history }) {
  // Chart dimensions (in SVG coordinate units).
  const width = 100;            // the SVG uses a 0-100 viewBox horizontally
  const height = 100;
  const barGap = 1.5;           // gap between bars, in the same units

  // Figure out how wide each bar should be so they all fit side by side.
  const barWidth = (width - barGap * (history.length - 1)) / history.length;

  // Pick a bar color based on how good that run's pass rate was.
  function barColor(rate) {
    if (rate >= 100) return "var(--pass)";
    if (rate >= 90) return "var(--accent)";
    return "var(--fail)";
  }

  // Format a timestamp into a tiny label like "Jun 1".
  function shortDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  // The most recent run is the last item in the history array.
  const latest = history[history.length - 1];

  return (
    <section className="trend">
      <div className="trend-header">
        <h2 className="trend-title">Pass Rate History</h2>
        <span className="trend-sub">Last {history.length} runs</span>
      </div>

      {/* preserveAspectRatio="none" lets the SVG stretch to fill its box */}
      <svg
        className="trend-svg"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
      >
        {/* Faint horizontal guide lines at 50% and 100% */}
        <line x1="0" y1="0" x2={width} y2="0" className="grid-line" />
        <line x1="0" y1={height / 2} x2={width} y2={height / 2} className="grid-line" />

        {/* One bar per historical run */}
        {history.map((run, i) => {
          // SVG's y-axis grows downward, so a tall bar needs a small y value.
          const barHeight = (run.pass_rate / 100) * height;
          const x = i * (barWidth + barGap);
          const y = height - barHeight;
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={barColor(run.pass_rate)}
              className="trend-bar"
            />
          );
        })}
      </svg>

      {/* A small caption showing the latest run's numbers */}
      <div className="trend-footer">
        <span>
          Latest: <strong>{latest.pass_rate}%</strong> ({latest.passed} passed,{" "}
          {latest.failed} failed)
        </span>
        <span className="trend-date">{shortDate(latest.generated_at)}</span>
      </div>
    </section>
  );
}
