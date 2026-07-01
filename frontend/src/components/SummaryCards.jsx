// SummaryCards.jsx — the row of four stat cards at the top of the dashboard.
//
// It receives a 'summary' prop (an object like
//   { total: 15, passed: 15, failed: 0, pass_rate: 100.0 })
// and renders one card for each number.

export default function SummaryCards({ summary }) {
  // Define the four cards as data, then map over them to render. Doing it
  // this way (instead of writing four near-identical blocks of JSX) keeps
  // the code short and makes it easy to add or change a card later.
  const cards = [
    { label: "Total Rules", value: summary.total, accent: "neutral" },
    { label: "Passing", value: summary.passed, accent: "pass" },
    { label: "Failing", value: summary.failed, accent: summary.failed > 0 ? "fail" : "neutral" },
    { label: "Pass Rate", value: `${summary.pass_rate}%`, accent: "accent" },
  ];

  return (
    <div className="summary-cards">
      {cards.map((card) => (
        <div key={card.label} className={`card card-${card.accent}`}>
          <span className="card-value">{card.value}</span>
          <span className="card-label">{card.label}</span>
        </div>
      ))}
    </div>
  );
}
