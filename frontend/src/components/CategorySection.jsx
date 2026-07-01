// CategorySection.jsx — one section of the rule list (e.g. all "Teams" rules).
//
// Props:
//   - category: the section name, like "Teams"
//   - checks: an array of check objects in that category, each shaped like
//       { rule: "...", passed: true/false, message: "..." }

import RuleRow from "./RuleRow.jsx";

export default function CategorySection({ category, checks }) {
  // Count how many rules in this section passed, for the little header badge.
  const passed = checks.filter((c) => c.passed).length;
  const total = checks.length;
  const allPassed = passed === total;

  return (
    <section className="category">
      <div className="category-header">
        <h2 className="category-title">{category}</h2>
        {/* Badge turns green only if every rule in the section passed */}
        <span className={`category-badge ${allPassed ? "all-pass" : "has-fail"}`}>
          {passed}/{total}
        </span>
      </div>

      <div className="rule-list">
        {/* Render one RuleRow per check in this category */}
        {checks.map((check, i) => (
          <RuleRow key={i} check={check} />
        ))}
      </div>
    </section>
  );
}
