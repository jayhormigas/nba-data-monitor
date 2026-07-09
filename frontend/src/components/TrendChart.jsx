// TrendChart.jsx — a hand-drawn SVG bar chart of pass rate over recent runs.
//
// No charting library on purpose: plain SVG keeps the dependencies minimal
// (just React). The chart always draws 10 fixed slots — one per run — so it
// visibly "fills up" as daily runs accumulate; empty slots stay unlit like
// scoreboard segments. Hovering a bar shows the day that run happened.
//
// Props:
//   - history: array of past runs, each like
//       { generated_at: "...", pass_rate: 100.0, passed: 18, failed: 0 }

import { useState } from "react";

const SLOTS = 10; // the chart shows at most the 10 most recent runs

export default function TrendChart({ history }) {
  const runs = history.slice(-SLOTS); // most recent runs, oldest first
  const [hovered, setHovered] = useState(null); // index of the hovered bar

  // Chart geometry (SVG viewBox units).
  const width = 100;
  const height = 100;
  const barGap = 2;
  const barWidth = (width - barGap * (SLOTS - 1)) / SLOTS;

  // Pick a bar color based on how good that run's pass rate was.
  function barColor(rate) {
    if (rate >= 100) return "var(--pass)";
    if (rate >= 90) return "var(--accent)";
    return "var(--fail)";
  }

  // "Thu, Jul 2" — the day a run happened, shown in the hover tooltip.
  function runDay(iso) {
    return new Date(iso).toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  }

  const latest = runs[runs.length - 1];

  return (
    <section className="trend">
      <div className="trend-header">
        <h2 className="trend-title">Pass Rate History</h2>
        <span className="trend-sub">Last {runs.length} runs</span>
      </div>

      <div className="trend-wrap">
        {/* preserveAspectRatio="none" lets the SVG stretch to fill its box */}
        <svg
          className="trend-svg"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
        >
          {/* Faint horizontal guide lines at 50% and 100% */}
          <line x1="0" y1="0" x2={width} y2="0" className="grid-line" />
          <line x1="0" y1={height / 2} x2={width} y2={height / 2} className="grid-line" />

          {/* 10 fixed slots: each gets a faint "unlit" placeholder, plus a
              colored bar if a run exists for that slot. */}
          {Array.from({ length: SLOTS }, (_, i) => {
            const x = i * (barWidth + barGap);
            const run = runs[i];
            const barHeight = run ? (run.pass_rate / 100) * height : 0;
            return (
              <g key={i}>
                <rect x={x} y="0" width={barWidth} height={height} className="trend-slot" />
                {run && (
                  <rect
                    x={x}
                    y={height - barHeight}
                    width={barWidth}
                    height={barHeight}
                    fill={barColor(run.pass_rate)}
                    className="trend-bar"
                    style={{ animationDelay: `${i * 45}ms` }}
                    onMouseEnter={() => setHovered(i)}
                    onMouseLeave={() => setHovered(null)}
                  />
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover tooltip: the day of that run + its numbers */}
        {hovered !== null && runs[hovered] && (
          <div
            className="trend-tip"
            style={{ left: `${Math.min(90, Math.max(10, ((hovered + 0.5) / SLOTS) * 100))}%` }}
          >
            <strong>{runDay(runs[hovered].generated_at)}</strong>
            <span>
              {runs[hovered].pass_rate}% · {runs[hovered].passed} passed,{" "}
              {runs[hovered].failed} failed
            </span>
          </div>
        )}
      </div>

      {/* A small caption showing the latest run's numbers */}
      <div className="trend-footer">
        <span>
          Latest: <strong>{latest.pass_rate}%</strong> ({latest.passed} passed,{" "}
          {latest.failed} failed)
        </span>
        <span className="trend-date">{runDay(latest.generated_at)}</span>
      </div>
    </section>
  );
}
