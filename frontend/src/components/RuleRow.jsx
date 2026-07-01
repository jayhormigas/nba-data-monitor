// RuleRow.jsx — a single row showing one validation rule's result.
//
// Props:
//   - check: one check object, shaped like
//       { rule: "No duplicate team IDs", passed: true, message: "All team IDs are unique" }
//
// The row shows a PASS/FAIL pill, the rule name, and the detailed message
// the validator returned.

export default function RuleRow({ check }) {
  return (
    <div className={`rule-row ${check.passed ? "passed" : "failed"}`}>
      {/* Status pill: green PASS or red FAIL */}
      <span className="rule-status">
        {check.passed ? "PASS" : "FAIL"}
      </span>

      <div className="rule-text">
        <span className="rule-name">{check.rule}</span>
        {/* The message is the exact string the Python validator returned */}
        <span className="rule-message">{check.message}</span>
      </div>
    </div>
  );
}
