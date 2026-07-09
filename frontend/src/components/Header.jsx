// Header.jsx — the top bar of the dashboard.
//
// It shows the project name, a short subtitle, and when the data was last
// generated. It receives two props from App.jsx:
//   - generatedAt: an ISO timestamp string (or null if using sample data)
//   - usingLiveData: true if real results were loaded, false for sample data

export default function Header({ generatedAt, usingLiveData }) {
  // Turn the raw ISO timestamp into a friendly, readable string.
  // e.g. "2026-06-01T14:00:00Z" -> "Jun 1, 2026, 2:00 PM"
  function formatTime(iso) {
    if (!iso) return "sample data";
    const date = new Date(iso);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  return (
    <header className="header">
      <div className="header-inner container">
        <div className="header-left">
          {/* Hand-drawn basketball logo (inline SVG — no image files needed).
              It drops in on page load and spins when hovered. */}
          <div className="logo-ball" aria-hidden="true">
            <svg viewBox="0 0 100 100" width="38" height="38">
              <circle cx="50" cy="50" r="46" fill="var(--accent)" />
              <g stroke="#0a0e14" strokeWidth="5" fill="none" strokeLinecap="round">
                <path d="M4 50h92" />
                <path d="M50 4v92" />
                <path d="M18 18c15 16 15 48 0 64" />
                <path d="M82 18c-15 16-15 48 0 64" />
              </g>
            </svg>
          </div>
          <div>
            <h1 className="title">NBA Stats Validation Suite</h1>
            <p className="subtitle">Live data quality monitoring</p>
          </div>
        </div>

        <div className="header-right">
          {/* A small status dot: green if live data, amber if sample */}
          <span className={`status-dot ${usingLiveData ? "live" : "sample"}`} />
          <div className="header-meta">
            <span className="meta-label">Last run</span>
            <span className="meta-value">{formatTime(generatedAt)}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
