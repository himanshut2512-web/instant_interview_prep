import { Flame, Sparkles } from 'lucide-react'

export const LEVELS = ['beginner', 'intermediate', 'advanced']
export const LEVEL_LABEL = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced', mixed: 'Mixed' }

/** Three ascending bars filled up to `value` (1-3): shows order without relying on colour. */
export function OrdinalGlyph({ value }) {
  return (
    <span className="level-glyph" aria-hidden="true">
      {[1, 2, 3].map((n) => (
        <i key={n} className={n <= value ? 'on' : ''} />
      ))}
    </span>
  )
}

export function LevelBadge({ level }) {
  const value = LEVELS.indexOf(level) + 1 || 2
  return (
    <span className="chip" title={`${LEVEL_LABEL[level] || level} level`}>
      <OrdinalGlyph value={value} />
      {LEVEL_LABEL[level] || level}
    </span>
  )
}

export function HotBadge({ reason }) {
  return (
    <span className="chip chip-hot" title={reason || 'Frequently asked'}>
      <Flame size={12} />
      Hot
    </span>
  )
}

const PRIORITY_VALUE = { high: 3, medium: 2, low: 1 }

export function PriorityTag({ priority }) {
  const label = { high: 'High priority', medium: 'Medium', low: 'Low' }[priority] || priority
  return (
    <span className={`chip ${priority === 'high' ? 'chip-sec' : ''}`}>
      <OrdinalGlyph value={PRIORITY_VALUE[priority] || 2} />
      {label}
    </span>
  )
}

export function NewBadge() {
  return (
    <span className="chip chip-brand" title="Generated on demand">
      <Sparkles size={12} />
      New
    </span>
  )
}

export function ModeBadge({ mode, label }) {
  const text = label || (mode === 'ai' ? 'AI mode' : 'Demo mode')
  return (
    <span className={`mode-badge ${mode}`} title={mode === 'ai' ? 'Claude-powered with live web research' : 'Offline knowledge base'}>
      <span className="dot" />
      <span className="txt">{text}</span>
    </span>
  )
}
