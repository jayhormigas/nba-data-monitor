// DataPanel.jsx — shows the raw data behind a category's rules, so a viewer
// can verify the numbers by hand. Rendered inside CategorySection when the
// "Show data" toggle is open. Which table it renders depends on the category.

export default function DataPanel({ category, data }) {
  if (!data) return null;

  if (category === "Teams" && data.teams) {
    return (
      <DataTable
        headers={["Team ID", "Team", "Abbr", "City", "State", "Founded"]}
        rows={data.teams.map((t) => [
          t.id ?? "—", t.team, t.abbr, t.city, t.state, t.founded,
        ])}
      />
    );
  }

  if (category === "Standings" && data.standings) {
    return (
      <DataTable
        headers={["Team", "W", "L", "Win%"]}
        rows={data.standings.map((s) => [
          s.team, s.wins, s.losses, Number(s.win_pct).toFixed(3),
        ])}
      />
    );
  }

  if (category === "Rosters" && data.rosters) {
    return (
      <DataTable
        scroll
        note={`${data.rosters.length} players across all 30 rosters — scroll to browse`}
        headers={["Team", "#", "Player", "Player ID"]}
        rows={data.rosters.map((r) => [
          r.team, r.number, r.player, r.player_id ?? "—",
        ])}
      />
    );
  }

  if (category === "Scoreboard") {
    const games = data.games || [];
    if (games.length === 0) {
      return <p className="data-empty">No games on the scoreboard right now.</p>;
    }
    return (
      <DataTable
        headers={["Game ID", "Matchup", "Score"]}
        rows={games.map((g) => [g.game_id ?? "—", g.matchup, g.score])}
      />
    );
  }

  return null;
}

// A small reusable table. `scroll` wraps it in a fixed-height scroll box (for
// the long roster list); `note` prints a caption above it.
function DataTable({ headers, rows, scroll, note }) {
  const table = (
    <table className="data-table">
      <thead>
        <tr>{headers.map((h) => <th key={h}>{h}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <>
      {note && <p className="data-note">{note}</p>}
      {scroll ? <div className="data-scroll">{table}</div> : table}
    </>
  );
}
