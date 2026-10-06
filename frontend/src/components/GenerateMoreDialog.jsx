import { useEffect, useState } from 'react'
import { LoaderCircle, WandSparkles, X } from 'lucide-react'

const SECTION_NOUN = {
  theory: 'theoretical questions',
  practical: 'practical problems',
  scenario: 'scenario-based questions',
  quiz: 'MCQs',
  revision: 'revision notes',
}

export default function GenerateMoreDialog({ open, onClose, section, topics, aiMode, onSubmit }) {
  const [count, setCount] = useState(section === 'quiz' ? 10 : 5)
  const [level, setLevel] = useState('mixed')
  const [topic, setTopic] = useState('')
  const [focus, setFocus] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => e.key === 'Escape' && !busy && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, busy, onClose])

  if (!open) return null
  const isRevision = section === 'revision'

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onSubmit({ section, count: isRevision ? 1 : count, level, topic: topic.trim(), focus: focus.trim() })
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && !busy && onClose()}>
      <form className="dialog" role="dialog" aria-modal="true" aria-labelledby="gen-title" onSubmit={submit}>
        <div className="spread" style={{ marginBottom: 6 }}>
          <h2 id="gen-title" className="row" style={{ margin: 0 }}>
            <WandSparkles size={19} className="icon-accent" />
            {isRevision ? 'Add a revision topic' : `Generate more ${SECTION_NOUN[section]}`}
          </h2>
          <button type="button" className="icon-btn" onClick={onClose} disabled={busy} aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <p className="muted" style={{ fontSize: '0.9rem' }}>
          {aiMode
            ? 'The agent writes fresh content tailored to your resume, JD and company research - without repeating what you already have.'
            : 'Demo mode adds unused content from the built-in knowledge base. Add an API key for freshly generated questions.'}
        </p>
        <div className="stack" style={{ gap: 14 }}>
          {isRevision ? (
            <div className="field">
              <label htmlFor="gen-topic">Topic</label>
              <input
                id="gen-topic"
                className="input"
                list="gen-topic-list"
                value={topic}
                placeholder="e.g. Kafka, Time-series forecasting, Power BI DAX"
                onChange={(e) => setTopic(e.target.value)}
              />
              <datalist id="gen-topic-list">
                {topics.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
              <span className="hint">Leave empty to cover the next planned topic that has no notes yet.</span>
            </div>
          ) : (
            <>
              <div className="field">
                <span className="label">How many</span>
                <div className="segmented" role="radiogroup" aria-label="How many">
                  {[3, 5, 10, 15].map((n) => (
                    <button type="button" key={n} className={count === n ? 'on' : ''} aria-pressed={count === n} onClick={() => setCount(n)}>
                      {n}
                    </button>
                  ))}
                </div>
              </div>
              <div className="field">
                <span className="label">Level</span>
                <div className="segmented" role="radiogroup" aria-label="Level">
                  {['mixed', 'beginner', 'intermediate', 'advanced'].map((l) => (
                    <button type="button" key={l} className={level === l ? 'on' : ''} aria-pressed={level === l} onClick={() => setLevel(l)}>
                      {l[0].toUpperCase() + l.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div className="field">
                <label htmlFor="gen-topic">Topic</label>
                <select id="gen-topic" className="select" value={topic} onChange={(e) => setTopic(e.target.value)}>
                  <option value="">Any topic from the plan</option>
                  {topics.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              {aiMode && (
                <div className="field">
                  <label htmlFor="gen-focus">Extra focus (optional)</label>
                  <input
                    id="gen-focus"
                    className="input"
                    value={focus}
                    maxLength={300}
                    placeholder="e.g. more SQL window functions, questions about my RAG project"
                    onChange={(e) => setFocus(e.target.value)}
                  />
                </div>
              )}
            </>
          )}
          {error && <div className="banner error">{error}</div>}
          <div className="row" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? <LoaderCircle size={16} className="spin" /> : <WandSparkles size={16} />}
              {busy ? (aiMode ? 'Generating - up to a minute…' : 'Adding…') : 'Generate'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
