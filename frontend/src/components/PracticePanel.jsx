import { useId, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowRight, Bot, CircleAlert, CircleCheck, LoaderCircle, PenLine, Sparkles } from 'lucide-react'
import { EASE } from '../lib/motion.js'
import Markdown from './Markdown.jsx'
import { ProgressRing } from './Viz.jsx'

export function Feedback({ result }) {
  const [showImproved, setShowImproved] = useState(false)
  return (
    <motion.div className="feedback" aria-live="polite" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }}>
      <div className="fb-top">
        <ProgressRing value={result.score} max={10} size={66} stroke={7} label="Answer score out of 10">
          <span style={{ fontWeight: 750, fontSize: 15 }}>{result.score}/10</span>
        </ProgressRing>
        <div style={{ minWidth: 0 }}>
          <div className="verdict">{result.verdict}</div>
          <span className={`chip ${result.engine === 'ai' ? 'chip-brand' : ''}`} style={{ marginTop: 6 }}>
            <Bot size={12} /> {result.engine === 'ai' ? 'AI feedback' : 'Offline feedback'}
          </span>
        </div>
      </div>
      <div className="duo">
        {result.strengths?.length > 0 && (
          <div>
            <span className="sub-label" style={{ marginTop: 0 }}>
              What worked
            </span>
            <ul className="list-clean">
              {result.strengths.map((s, i) => (
                <li key={i}>
                  <CircleCheck size={15} className="icon-ok" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {result.improvements?.length > 0 && (
          <div>
            <span className="sub-label" style={{ marginTop: 0 }}>
              Improve
            </span>
            <ul className="list-clean">
              {result.improvements.map((s, i) => (
                <li key={i}>
                  <ArrowRight size={15} className="icon-sec" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      {result.missing_points?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <span className="sub-label">Missing key points</span>
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
        <div style={{ marginTop: 14 }}>
          <button className="btn btn-sm" onClick={() => setShowImproved((v) => !v)} aria-expanded={showImproved}>
            <Sparkles size={15} /> {showImproved ? 'Hide' : 'Show'} improved answer
          </button>
          <AnimatePresence initial={false}>
            {showImproved && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: EASE }} style={{ overflow: 'hidden' }}>
                <div className="answer-box" style={{ marginTop: 12 }}>
                  <Markdown>{result.improved_answer_md}</Markdown>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  )
}

export default function PracticePanel({ onEvaluate, aiMode }) {
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const inputId = useId()
  const words = answer.trim() ? answer.trim().split(/\s+/).length : 0
  const target = Math.min(1, words / 150)

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
    <motion.div className="practice" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: EASE }}>
      <label className="label" htmlFor={inputId} style={{ marginBottom: 8 }}>
        <PenLine size={15} /> Answer it the way you would say it in the interview
      </label>
      <textarea
        id={inputId}
        className="textarea"
        rows={6}
        value={answer}
        placeholder="Structure it: definition → how it works → an example from your experience → a trade-off…"
        onChange={(e) => setAnswer(e.target.value)}
      />
      <div className="spread" style={{ marginTop: 10 }}>
        <div className="row" style={{ minWidth: 180, flex: 1 }}>
          <div className="meter thin" style={{ flex: 1, maxWidth: 160 }} aria-hidden="true">
            <span style={{ width: `${target * 100}%` }} />
          </div>
          <span className="subtle">{words} words · aim for 120-250</span>
        </div>
        <button className="btn btn-sec btn-sm" disabled={busy || answer.trim().length < 15} onClick={submit}>
          {busy ? <LoaderCircle size={15} className="spin" /> : <Bot size={15} />}
          {busy ? (aiMode ? 'Claude is reviewing…' : 'Scoring…') : 'Get feedback'}
        </button>
      </div>
      {error && (
        <div className="field-error" style={{ marginTop: 8 }}>
          <CircleAlert size={14} /> {error}
        </div>
      )}
      {result && <Feedback result={result} />}
    </motion.div>
  )
}
