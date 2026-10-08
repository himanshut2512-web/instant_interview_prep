import { useState } from 'react'
import { CircleAlert, LoaderCircle, WandSparkles, X } from 'lucide-react'
import Dialog from './Dialog.jsx'
import { SegmentedTabs } from './Tabs.jsx'

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
  const isRevision = section === 'revision'
  const close = () => !busy && onClose()

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
    <Dialog open={open} onClose={close} labelledBy="gen-title" dismissable={!busy}>
      <form onSubmit={submit} data-section={section}>
        <div className="dialog-head">
          <h2 id="gen-title">
            <span className="title-icon" aria-hidden="true">
              <WandSparkles size={18} />
            </span>
            {isRevision ? 'Add a revision topic' : `Generate more ${SECTION_NOUN[section]}`}
          </h2>
          <button type="button" className="icon-btn sm" onClick={close} disabled={busy} aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <p className="muted" style={{ fontSize: 14 }}>
          {aiMode
            ? 'The agent writes fresh content tailored to your resume, JD and the company research, without repeating what you already have.'
            : 'Demo mode adds unused content from the built-in knowledge base. Add an API key for freshly generated questions.'}
        </p>
        <div className="stack" style={{ gap: 16, marginTop: 6 }}>
          {isRevision ? (
            <div className="field">
              <label className="label" htmlFor="gen-topic">
                Topic
              </label>
              <input
                id="gen-topic"
                className="input"
                list="gen-topic-list"
                value={topic}
                placeholder="e.g. Kafka, time-series forecasting, Power BI DAX"
                onChange={(e) => setTopic(e.target.value)}
                data-autofocus
              />
              <datalist id="gen-topic-list">
                {topics.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
              <span className="hint">Leave it empty to cover the next planned topic that has no notes yet.</span>
            </div>
          ) : (
            <>
              <div className="field">
                <span className="label">How many</span>
                <SegmentedTabs ariaLabel="How many" value={count} onChange={setCount} options={[3, 5, 10, 15].map((n) => ({ value: n, label: String(n) }))} />
              </div>
              <div className="field">
                <span className="label">Level</span>
                <SegmentedTabs
                  ariaLabel="Level"
                  value={level}
                  onChange={setLevel}
                  options={['mixed', 'beginner', 'intermediate', 'advanced'].map((l) => ({ value: l, label: l[0].toUpperCase() + l.slice(1) }))}
                />
              </div>
              <div className="field">
                <label className="label" htmlFor="gen-topic">
                  Topic
                </label>
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
                  <label className="label" htmlFor="gen-focus">
                    Extra focus <span className="opt">(optional)</span>
                  </label>
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
          {error && (
            <div className="banner-note error">
              <CircleAlert size={18} />
              <span>{error}</span>
            </div>
          )}
        </div>
        <div className="dialog-foot">
          <button type="button" className="btn" onClick={close} disabled={busy}>
            Cancel
          </button>
          <button type="submit" className="btn btn-sec" disabled={busy}>
            {busy ? <LoaderCircle size={16} className="spin" /> : <WandSparkles size={16} />}
            {busy ? (aiMode ? 'Generating, up to a minute…' : 'Adding…') : 'Generate'}
          </button>
        </div>
      </form>
    </Dialog>
  )
}
