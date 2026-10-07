import { Eye, EyeOff, Flame, Search } from 'lucide-react'
import { LEVEL_LABEL, OrdinalGlyph } from './Badges.jsx'

export default function FilterBar({ filters, setFilters, counts, topics, practiceMode, setPracticeMode, showStatus = true }) {
  const set = (patch) => setFilters((f) => ({ ...f, ...patch }))
  return (
    <div className="filterbar" role="search">
      <div className="segmented" role="radiogroup" aria-label="Level">
        {['all', 'beginner', 'intermediate', 'advanced'].map((level, i) => (
          <button
            key={level}
            className={filters.level === level ? 'on' : ''}
            aria-pressed={filters.level === level}
            onClick={() => set({ level })}
          >
            {i > 0 && <OrdinalGlyph value={i} />}
            {level === 'all' ? 'All levels' : LEVEL_LABEL[level]}
            <span className="count">{counts[level] ?? 0}</span>
          </button>
        ))}
      </div>
      <button
        className={`btn btn-sm btn-hot ${filters.hot ? 'is-on' : ''}`}
        aria-pressed={filters.hot}
        onClick={() => set({ hot: !filters.hot })}
      >
        <Flame size={15} /> Hot only <span className="count">{counts.hot ?? 0}</span>
      </button>
      <select className="select" aria-label="Topic" value={filters.topic} onChange={(e) => set({ topic: e.target.value })}>
        <option value="">All topics</option>
        {topics.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
      {showStatus && (
        <select className="select" aria-label="Progress" value={filters.status} onChange={(e) => set({ status: e.target.value })}>
          <option value="">Any progress</option>
          <option value="todo">Not mastered yet</option>
          <option value="mastered">Mastered</option>
          <option value="review">Review later</option>
        </select>
      )}
      <div className="search-box">
        <Search size={15} />
        <input
          className="input"
          type="search"
          placeholder="Search questions…"
          aria-label="Search questions"
          value={filters.q}
          onChange={(e) => set({ q: e.target.value })}
        />
      </div>
      {setPracticeMode && (
        <button
          className={`btn btn-sm ${practiceMode ? 'is-on' : ''}`}
          aria-pressed={practiceMode}
          onClick={() => setPracticeMode(!practiceMode)}
          title="Hide model answers so you can answer first"
        >
          {practiceMode ? <EyeOff size={15} /> : <Eye size={15} />} Practice mode
        </button>
      )}
    </div>
  )
}

export function applyFilters(items, filters, userItems = {}) {
  const q = filters.q.trim().toLowerCase()
  return items.filter((item) => {
    if (filters.level !== 'all' && item.level !== filters.level) return false
    if (filters.hot && !item.hot) return false
    if (filters.topic && item.topic !== filters.topic) return false
    const status = userItems[item.id]
    if (filters.status === 'todo' && status === 'mastered') return false
    if (filters.status === 'mastered' && status !== 'mastered') return false
    if (filters.status === 'review' && status !== 'review') return false
    if (q) {
      const haystack = `${item.question} ${item.topic} ${item.scenario || ''}`.toLowerCase()
      if (!haystack.includes(q)) return false
    }
    return true
  })
}

export function levelCounts(items) {
  const counts = { all: items.length, beginner: 0, intermediate: 0, advanced: 0, hot: 0 }
  for (const item of items) {
    counts[item.level] = (counts[item.level] || 0) + 1
    if (item.hot) counts.hot += 1
  }
  return counts
}
