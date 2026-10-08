import { useState } from 'react'
import { motion } from 'motion/react'
import { EASE } from '../lib/motion.js'
import { CountUp } from './Motion.jsx'

/* Chart primitives that follow the data-viz rules: a meter's track is a lighter
   step of the fill's ramp, single-series bars share one colour with the value at
   the tip, tooltips appear on hover and keyboard focus but never gate a value. */

const clamp01 = (n) => Math.max(0, Math.min(1, n))

export function Meter({ value, max = 1, label, className = '' }) {
  const pct = max > 0 ? clamp01(value / max) * 100 : 0
  return (
    <div className={`meter ${className}`} role="meter" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value} aria-label={label}>
      <motion.span initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 1, ease: EASE }} />
    </div>
  )
}

/** Radial meter with the value printed in the middle. */
export function ProgressRing({ value, max = 100, size = 120, stroke = 10, label, children, className = '' }) {
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const share = max > 0 ? clamp01(value / max) : 0
  const center = size / 2
  return (
    <div
      className={`ring ${className}`}
      style={{ width: size, height: size }}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={Math.round(value)}
      aria-label={label}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
        <circle className="ring-track" cx={center} cy={center} r={radius} strokeWidth={stroke} />
        <motion.circle
          className="ring-fill"
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - share) }}
          transition={{ duration: 1.2, ease: EASE }}
          transform={`rotate(-90 ${center} ${center})`}
          style={{ opacity: share > 0 ? 1 : 0 }}
        />
      </svg>
      <div className="ring-center">{children}</div>
    </div>
  )
}

const STATUS_TONES = {
  hot: ['--hot-soft', '--hot-ink'],
  ok: ['--ok-soft', '--ok-ink'],
  warn: ['--warn-soft', '--warn-ink'],
  brand: ['--brand-soft', '--brand-ink'],
}

/** Stat tile: label + value (+ sub text, optional icon and extra content). */
export function StatTile({ label, value, sub, icon: Icon, tone, format, children }) {
  const vars = tone ? STATUS_TONES[tone] || [`--c-${tone}-soft`, `--c-${tone}-ink`] : null
  const style = vars ? { '--tile-soft': `var(${vars[0]})`, '--tile-ink': `var(${vars[1]})` } : undefined
  return (
    <div className="stat-tile" style={style}>
      <div className="stat-top">
        <span className="stat-label">{label}</span>
        {Icon && (
          <span className="stat-icon" aria-hidden="true">
            <Icon size={17} />
          </span>
        )}
      </div>
      <div className="stat-value">{typeof value === 'number' ? <CountUp value={value} format={format} /> : value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {children}
    </div>
  )
}

/**
 * Horizontal single-series bars. items: [{ key, label, value, max?, display?, tooltip?: { title, lines } }]
 */
export function BarList({ items, onSelect, ariaLabel }) {
  const [hover, setHover] = useState(null)
  const max = Math.max(1, ...items.map((i) => i.max ?? i.value))
  return (
    <div className="barlist" role="list" aria-label={ariaLabel}>
      {items.map((item, index) => {
        const share = clamp01(item.value / (item.max ?? max))
        const interactive = Boolean(onSelect)
        return (
          <div
            key={item.key}
            role="listitem"
            tabIndex={0}
            className="bar-row"
            style={interactive ? { cursor: 'pointer' } : undefined}
            onMouseEnter={() => setHover(item.key)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(item.key)}
            onBlur={() => setHover(null)}
            onClick={interactive ? () => onSelect(item) : undefined}
            onKeyDown={interactive ? (e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), onSelect(item)) : undefined}
            aria-label={`${item.label}: ${item.display ?? item.value}`}
          >
            <span className="bar-label" title={item.label}>
              {item.label}
            </span>
            <div className="bar-track">
              <motion.div
                className="bar-fill"
                style={{ width: `${Math.max(share * 100, 1.5)}%` }}
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.8, delay: index * 0.05, ease: EASE }}
              />
            </div>
            <span className="bar-value">{item.display ?? item.value}</span>
            {hover === item.key && item.tooltip && (
              <motion.div className="viz-tip" role="tooltip" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.15 }}>
                <strong>{item.tooltip.title}</strong>
                {(item.tooltip.lines || []).map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </motion.div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/**
 * Part-to-whole stacked bar. segments: [{ key, label, value, color }] in a
 * validated adjacent order; the legend carries every value (no in-bar labels).
 */
export function StackedBar({ segments, ariaLabel, unit = '' }) {
  const [hover, setHover] = useState(null)
  const total = segments.reduce((sum, s) => sum + s.value, 0) || 1
  const description = segments.map((s) => `${s.label} ${s.value}`).join(', ')
  return (
    <div>
      <div className="stackbar" role="img" aria-label={`${ariaLabel}: ${description}`}>
        {segments.map((s, i) =>
          s.value > 0 ? (
            <motion.div
              key={s.key}
              className="seg"
              tabIndex={0}
              style={{ background: s.color, flexGrow: s.value, flexBasis: 0 }}
              initial={{ opacity: 0, scaleY: 0.3 }}
              whileInView={{ opacity: 1, scaleY: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: EASE }}
              onMouseEnter={() => setHover(s.key)}
              onMouseLeave={() => setHover(null)}
              onFocus={() => setHover(s.key)}
              onBlur={() => setHover(null)}
              aria-label={`${s.label}: ${s.value}${unit}`}
            >
              {hover === s.key && (
                <div className="viz-tip" role="tooltip" style={{ left: 0 }}>
                  <strong>
                    {s.value}
                    {unit}
                  </strong>
                  {s.label} · {Math.round((100 * s.value) / total)}% of the kit
                </div>
              )}
            </motion.div>
          ) : null,
        )}
      </div>
      <ul className="legend">
        {segments.map((s) => (
          <li key={s.key}>
            <span className="swatch" style={{ background: s.color }} aria-hidden="true" />
            {s.label} <strong>{s.value}</strong>
            <span className="subtle">{Math.round((100 * s.value) / total)}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Sparkline of 0-100 values: history in muted ink, the latest point in the accent. */
export function Sparkline({ values, width = 150, height = 36 }) {
  if (!values || values.length < 2) return null
  const pad = 5
  const step = (width - pad * 2) / (values.length - 1)
  const y = (v) => pad + (height - pad * 2) * (1 - Math.max(0, Math.min(100, v)) / 100)
  const d = values.map((v, i) => `${i ? 'L' : 'M'}${pad + i * step},${y(v)}`).join(' ')
  const lastX = pad + (values.length - 1) * step
  const lastY = y(values[values.length - 1])
  return (
    <svg className="sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <motion.path
        d={d}
        fill="none"
        stroke="var(--ink-3)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: EASE }}
      />
      <circle cx={lastX} cy={lastY} r="4" fill="var(--sec-mark, var(--brand))" stroke="var(--surface)" strokeWidth="2" />
    </svg>
  )
}

/**
 * Topic x level heatmap rendered as a real table (it doubles as the table view):
 * every cell prints its count; colour is a single-hue sequential ramp.
 * rows: [{ key, label }], cols: [{ key, label }], cell(rowKey, colKey) -> { value, lines }
 */
export function Heatmap({ rows, cols, cell, onSelect, caption }) {
  const [hover, setHover] = useState(null)
  let max = 0
  for (const r of rows) for (const c of cols) max = Math.max(max, cell(r.key, c.key).value)
  const step = (v) => (v <= 0 || max <= 0 ? 0 : Math.max(1, Math.ceil((v / max) * 7)))
  return (
    <div>
      <table className="heatmap">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            <th scope="col" className="sr-only">
              Topic
            </th>
            {cols.map((c) => (
              <th key={c.key} scope="col">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => (
            <tr key={r.key}>
              <th scope="row" className="row-head" title={r.label}>
                <span>{r.label}</span>
              </th>
              {cols.map((c, ci) => {
                const data = cell(r.key, c.key)
                const k = step(data.value)
                const id = `${r.key}|${c.key}`
                return (
                  <td key={c.key} style={{ position: 'relative' }}>
                    <motion.button
                      type="button"
                      className={`heat-cell ${k ? `seq-${k}` : 'zero'}`}
                      disabled={!data.value}
                      initial={{ opacity: 0, scale: 0.6 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.35, delay: ri * 0.03 + ci * 0.05, ease: EASE }}
                      onMouseEnter={() => setHover(id)}
                      onMouseLeave={() => setHover(null)}
                      onFocus={() => setHover(id)}
                      onBlur={() => setHover(null)}
                      onClick={() => data.value && onSelect?.(r, c)}
                      aria-label={`${r.label}, ${c.label}: ${data.value} questions`}
                    >
                      {data.value}
                    </motion.button>
                    {hover === id && data.value > 0 && (
                      <div className="viz-tip" role="tooltip" style={{ left: '50%', transform: 'translateX(-50%)' }}>
                        <strong>
                          {data.value} question{data.value === 1 ? '' : 's'}
                        </strong>
                        {r.label} · {c.label}
                        {(data.lines || []).map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="scale-legend" aria-hidden="true">
        <span>Fewer</span>
        <span className="scale">
          {[1, 2, 3, 4, 5, 6, 7].map((k) => (
            <i key={k} className={`seq-${k}`} />
          ))}
        </span>
        <span>More</span>
      </div>
    </div>
  )
}
