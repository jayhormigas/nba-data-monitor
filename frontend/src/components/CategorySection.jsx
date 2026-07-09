// CategorySection.jsx — one section of the rule list (e.g. all "Teams" rules),
// with an optional expandable panel showing the raw data behind those rules.
//
// Props:
//   - category: the section name, like "Teams"
//   - checks: an array of check objects in that category
//   - data: the full raw-data object (results.data); used for the "Show data" panel

import { useState } from "react";
import RuleRow from "./RuleRow.jsx";
import DataPanel from "./DataPanel.jsx";
import CategoryIcon from "./CategoryIcon.jsx";

export default function CategorySection({ category, checks, data }) {
  // Count how many rules in this section passed, for the little header badge.
  const passed = checks.filter((c) => c.passed).length;
  const total = checks.length;
  const allPassed = passed === total;

  // Whether the raw-data panel under this section is expanded.
  const [showData, setShowData] = useState(false);

  // Only offer the toggle if we actually have data for this category.
  const hasData = Boolean(
    data && (
      (category === "Teams" && data.teams?.length) ||
      (category === "Standings" && data.standings?.length) ||
      (category === "Rosters" && data.rosters?.length) ||
      (category === "Scoreboard" && data.games?.length)
    )
  );

  return (
    <section className="category">
      <div className="category-header">
        <h2 className="category-title">
          <CategoryIcon category={category} />
          {category}
        </h2>
        {/* Badge turns green only if every rule in the section passed */}
        <span className={`category-badge ${allPassed ? "all-pass" : "has-fail"}`}>
          {passed}/{total}
        </span>

        {hasData && (
          <button
            className="data-toggle"
            onClick={() => setShowData((open) => !open)}
            aria-expanded={showData}
          >
            {showData ? "Hide data ▲" : "Show data ▾"}
          </button>
        )}
      </div>

      <div className="rule-list">
        {/* Render one RuleRow per check in this category */}
        {checks.map((check, i) => (
          <RuleRow key={i} check={check} />
        ))}
      </div>

      {showData && (
        <div className="data-panel">
          <DataPanel category={category} data={data} />
        </div>
      )}
    </section>
  );
}
