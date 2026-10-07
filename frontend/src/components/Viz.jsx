import { useState } from 'react'

/* Small, dependency-free chart primitives following the data-viz rules:
   stat tiles for headline numbers, same-ramp meters for ratios, thin single-hue
   bars with values at the tip, and hover/focus tooltips that never gate a value. */

export function compact(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-'
  if (Math.abs(n) >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}K`
  return String(n)
}

export function StatTile({ label, value, sub, icon: Icon, children }) {
  return (
    <div className="stat-tile">
      <div className="stat-label">
        {Icon && <Icon size={15} aria-hidden="true" />}
        {label}
      </div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {children}
    </div>
  )
}

export function Meter({ value, max = 1, label }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (100 * value) / max)) : 0
  return (
    <div className="meter" role="meter" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-label={label}>
      <div style={{ width: `${pct}%` }} />
    </div>
  )
}

/**
 * Horizontal bar list. items: [{key, label, value, max, display, tooltip: {title, lines}}]
 * One series -> one colour for every bar; the value is printed at the tip.
 */
export function BarList({ items, onSelect, ariaLabel }) {
  const [hover, setHover] = useState(null)
  const max = Math.max(1, ...items.map((i) => i.max ?? i.value))
  return (
    <div className="barlist" role="list" aria-label={ariaLabel}>
      {items.map((item) => {
        const pct = Math.max(0, Math.min(100, (100 * item.value) / (item.max ?? max)))
        const interactive = Boolean(onSelect)
        return (
          <div
            key={item.key}
            role="listitem"
            className="bar-row"
            tabIndex={0}
            style={interactive ? { cursor: 'pointer' } : undefined}
            onMouseEnter={() => setHover(item.key)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(item.key)}
            onBlur={() => setHover(null)}
            onClick={interactive ? () => onSelect(item) : undefined}
            onKeyDown={interactive ? (e) => e.key === 'Enter' && onSelect(item) : undefined}
            aria-label={`${item.label}: ${item.display ?? item.value}`}
          >
            <span className="bar-label" title={item.label}>
              {item.label}
            </span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="bar-value">{item.display ?? item.value}</span>
            {hover === item.key && item.tooltip && (
              <div className="viz-tooltip" role="tooltip">
                <strong>{item.tooltip.title}</strong>
                {(item.tooltip.lines || []).map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/** Sparkline of 0-100 values: history in the muted ink, the latest point in the accent. */
export function Sparkline({ values, width = 140, height = 34 }) {
  if (!values || values.length < 2) return null
  const pad = 5
  const step = (width - pad * 2) / (values.length - 1)
  const y = (v) => pad + (height - pad * 2) * (1 - Math.max(0, Math.min(100, v)) / 100)
  const points = values.map((v, i) => `${pad + i * step},${y(v)}`).join(' ')
  const lastX = pad + (values.length - 1) * step
  const lastY = y(values[values.length - 1])
  return (
    <svg className="sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points} fill="none" stroke="var(--viz-muted)" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={lastX} cy={lastY} r="4" fill="var(--accent)" stroke="var(--surface)" strokeWidth="2" />
    </svg>
  )
}
