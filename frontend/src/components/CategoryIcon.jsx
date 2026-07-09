// CategoryIcon.jsx — a small colored icon next to each dashboard section
// title, picked to match what that category validates: a player for Teams,
// a trophy for Standings, a #23 jersey (a nod to Jordan) for Rosters, and a
// scoreboard panel for Scoreboard. Plain inline SVG shapes, no image files
// or icon library needed.

function TeamsIcon({ color }) {
  // A simple head + shoulders silhouette — one player standing in for the team.
  return (
    <>
      <circle cx="12" cy="7" r="4" fill={color} />
      <path d="M12 13c-4.4 0-8 2-8 6v2h16v-2c0-4-3.6-6-8-6z" fill={color} />
    </>
  );
}

function StandingsIcon({ color }) {
  // A trophy: cup, two handles, stem, and a two-tier base.
  return (
    <>
      <path d="M7 4H17V7C17 9.5 14.8 11 12 11C9.2 11 7 9.5 7 7V4Z" fill={color} />
      <path d="M7 5C4.5 5 4 6.5 4 8C4 9.7 5.5 11 7.3 11" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <path d="M17 5C19.5 5 20 6.5 20 8C20 9.7 18.5 11 16.7 11" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <rect x="11" y="11" width="2" height="4" fill={color} />
      <rect x="8.5" y="15" width="7" height="2" rx="0.6" fill={color} />
      <rect x="7" y="17.4" width="10" height="1.8" rx="0.6" fill={color} />
    </>
  );
}

function RostersIcon({ color }) {
  // A jersey silhouette (shoulders, sleeves, neckline) with "23" on the chest.
  return (
    <>
      <path
        d="M9,4 L4,6.5 L4,10 L7,8.7 L7,21 L17,21 L17,8.7 L20,10 L20,6.5 L15,4 L14,6 L10,6 Z"
        fill={color}
      />
      <text x="12" y="17" textAnchor="middle" fontSize="6.5" fontWeight="700" fill="#fff">
        23
      </text>
    </>
  );
}

function ScoreboardIcon({ color }) {
  // A scoreboard panel: outer frame with two dark digit windows and a base.
  return (
    <>
      <rect x="3" y="5" width="18" height="12" rx="1.5" fill={color} />
      <rect x="5.2" y="7.2" width="5.8" height="7.6" rx="0.6" fill="#0a0e14" />
      <rect x="13" y="7.2" width="5.8" height="7.6" rx="0.6" fill="#0a0e14" />
      <rect x="9" y="19" width="6" height="1.6" rx="0.5" fill={color} />
    </>
  );
}

// One color per category so the icons read as distinct at a glance.
const CATEGORY_ICONS = {
  Teams:      { Icon: TeamsIcon,      color: "#4da6ff" },
  Standings:  { Icon: StandingsIcon,  color: "#f5b942" },
  Rosters:    { Icon: RostersIcon,    color: "#ce1141" },
  Scoreboard: { Icon: ScoreboardIcon, color: "#22d3ee" },
};

export default function CategoryIcon({ category }) {
  const entry = CATEGORY_ICONS[category];
  if (!entry) return null;
  const { Icon, color } = entry;
  return (
    <svg className="category-icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <Icon color={color} />
    </svg>
  );
}
