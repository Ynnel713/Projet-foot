import { fmRadarTierColor } from "../../utils/fmTier";

// Port fidèle de app._radar_svg (Streamlit) : araignée des moyennes par
// catégorie d'attributs FM26, mêmes proportions et couleurs. `selected`
// (nom d'axe) + `onSelect` rendent les axes cliquables -- l'appelant
// (PlayerProfile) s'en sert pour surligner les attributs qui composent
// l'axe choisi dans les colonnes à côté (retour terrain du 28/09/2026).
export default function RadarChart({ categories, size = 230, selected, onSelect }) {
  const n = categories.length;
  if (n < 3) return null;

  const width = size + 150;
  const cx = width / 2;
  const cy = size / 2;
  const maxR = size / 2 - 50;
  const step = (2 * Math.PI) / n;

  const angleFor = (i) => -Math.PI / 2 + i * step;
  const points = categories.map(({ value }, i) => {
    const angle = angleFor(i);
    const r = maxR * Math.max(0, Math.min(1, value / 99));
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  });
  const polygon = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");

  const gridPolygons = [0.25, 0.5, 0.75, 1.0].map((frac) => {
    const pts = categories
      .map((_c, i) => {
        const angle = angleFor(i);
        return `${(cx + maxR * frac * Math.cos(angle)).toFixed(1)},${(cy + maxR * frac * Math.sin(angle)).toFixed(1)}`;
      })
      .join(" ");
    return <polygon key={frac} points={pts} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />;
  });

  return (
    <svg viewBox={`0 0 ${width} ${size}`} width="100%" height={size} style={{ maxWidth: width }}>
      {gridPolygons}
      {categories.map(({ name }, i) => {
        const angle = angleFor(i);
        const ex = cx + maxR * Math.cos(angle);
        const ey = cy + maxR * Math.sin(angle);
        const isSelected = name === selected;
        return (
          <line
            key={i}
            x1={cx}
            y1={cy}
            x2={ex}
            y2={ey}
            stroke={isSelected ? "rgba(61,220,112,0.55)" : "rgba(255,255,255,0.08)"}
            strokeWidth={isSelected ? 2 : 1}
          />
        );
      })}
      <polygon points={polygon} fill="#1e8e3e55" stroke="#3ddc70" strokeWidth="2" />
      {points.map(([x, y], i) => {
        const isSelected = categories[i].name === selected;
        return <circle key={i} cx={x} cy={y} r={isSelected ? 5 : 3} fill="#3ddc70" />;
      })}
      {categories.map(({ name, value }, i) => {
        const angle = angleFor(i);
        const lx = cx + (maxR + 34) * Math.cos(angle);
        const ly = cy + (maxR + 34) * Math.sin(angle);
        const anchor = Math.abs(lx - cx) < 5 ? "middle" : lx < cx ? "end" : "start";
        const isSelected = name === selected;
        return (
          <g
            key={i}
            onClick={onSelect ? () => onSelect(isSelected ? null : name) : undefined}
            style={onSelect ? { cursor: "pointer" } : undefined}
          >
            {isSelected && (
              <circle cx={lx} cy={ly - 3} r={30} fill="rgba(61,220,112,0.1)" />
            )}
            <text
              x={lx}
              y={ly - 8}
              textAnchor={anchor}
              fontFamily="Manrope, sans-serif"
              fontSize="14"
              fontWeight="800"
              fill={isSelected ? "#ffffff" : "rgba(230,230,235,0.8)"}
            >
              {name}
            </text>
            <text x={lx} y={ly + 11} textAnchor={anchor} fontFamily="Manrope, sans-serif" fontSize="17" fontWeight="800" fill={fmRadarTierColor(value)}>
              {value.toFixed(0)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
