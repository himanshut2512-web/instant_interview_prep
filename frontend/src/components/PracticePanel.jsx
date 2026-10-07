import { useId, useState } from 'react'
import { ArrowRight, Bot, CircleAlert, CircleCheck, LoaderCircle, PenLine } from 'lucide-react'
import Markdown from './Markdown.jsx'
import { Meter } from './Viz.jsx'

export function Feedback({ result }) {
  const [showImproved, setShowImproved] = useState(false)
  return (
    <div className="feedback" aria-live="polite">
      <div className="spread">
        <div className="score-line">
          <span className="score-big">{result.score}/10</span>
          <span className="muted">{result.verdict}</span>
        </div>
        <span className={`chip ${result.engine === 'ai' ? 'chip-accent' : ''}`}>
          <Bot size={12} /> {result.engine === 'ai' ? 'AI feedback' : 'Offline feedback'}
        </span>
      </div>
      <Meter value={result.score} max={10} label="Answer score out of 10" />
      <div className="two-col" style={{ marginTop: 12 }}>
        {result.strengths?.length > 0 && (
          <div>
            <h4 className="label" style={{ margin: '0 0 6px' }}>What worked</h4>
            <ul className="list-clean">
              {result.strengths.map((s, i) => (
                <li key={i}>
                  <CircleCheck size={15} className="icon-good" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {result.improvements?.length > 0 && (
          <div>
            <h4 className="label" style={{ margin: '0 0 6px' }}>Improve</h4>
            <ul className="list-clean">
              {result.improvements.map((s, i) => (
                <li key={i}>
                  <ArrowRight size={15} className="icon-accent" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      {result.missing_points?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 className="label" style={{ margin: '0 0 6px' }}>Missing key points</h4>
          <ul className="list-clean">
            {result.missing_points.map((s, i) => (
              <li key={i}>
                <CircleAlert size={15} className="icon-warn" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {result.improved_answer_md && (
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-sm" onClick={() => setShowImproved((v) => !v)}>
            {showImproved ? 'Hide' : 'Show'} improved answer
          </button>
          {showImproved && <Markdown className="feedback-md" children={result.improved_answer_md} />}
        </div>
      )}
    </div>
  )
}

export default function PracticePanel({ onEvaluate, aiMode }) {
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const inputId = useId()
  const words = answer.trim() ? answer.trim().split(/\s+/).length : 0

  const submit = async () => {
    setBusy(true)
    setError('')
    try {
      setResult(await onEvaluate(answer))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="practice">
      <label className="label row" htmlFor={inputId} style={{ marginBottom: 6 }}>
        <PenLine size={15} /> Type your answer the way you would say it in the interview
      </label>
      <textarea
        id={inputId}
        className="textarea"
        rows={6}
        value={answer}
        placeholder="Structure it: definition → how it works → example from your experience → trade-off…"
        onChange={(e) => setAnswer(e.target.value)}
      />
      <div className="spread" style={{ marginTop: 8 }}>
        <span className="subtle">
          {words} words · aim for 120-250 for a 1-2 minute answer
        </span>
        <button className="btn btn-primary btn-sm" disabled={busy || answer.trim().length < 15} onClick={submit}>
          {busy ? <LoaderCircle size={15} className="spin" /> : <Bot size={15} />}
          {busy ? (aiMode ? 'Claude is reviewing…' : 'Scoring…') : 'Get feedback'}
        </button>
      </div>
      {error && <div className="field-error" style={{ marginTop: 8 }}>{error}</div>}
      {result && <Feedback result={result} />}
    </div>
  )
}
