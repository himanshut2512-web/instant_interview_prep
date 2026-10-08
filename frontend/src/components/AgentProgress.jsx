import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ArrowRight,
  Check,
  CircleAlert,
  CircleCheck,
  CircleDashed,
  Globe,
  Info,
  LoaderCircle,
  MessagesSquare,
  RefreshCw,
  Search,
  TriangleAlert,
  Trophy,
  X,
} from 'lucide-react'
import { EASE } from '../lib/motion.js'
import { Meter, ProgressRing } from './Viz.jsx'

const LOG_ICONS = {
  search: Search,
  fetch: Globe,
  result: CircleCheck,
  note: MessagesSquare,
  warn: TriangleAlert,
  error: CircleAlert,
  success: Trophy,
  info: Info,
}

function host(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function StepIcon({ status }) {
  if (status === 'done') return <Check size={14} strokeWidth={3} />
  if (status === 'running') return <LoaderCircle size={14} className="spin" />
  if (status === 'failed') return <X size={14} strokeWidth={3} />
  return <CircleDashed size={14} />
}

/** Terminal-style log (also used for the overview's "how the agent built this kit"). */
export function TerminalLog({ logs, sources = [], live = false, title = 'Live agent log', maxHeight }) {
  const bodyRef = useRef(null)

  useEffect(() => {
    const el = bodyRef.current
    if (el && live) el.scrollTop = el.scrollHeight
  }, [logs.length, live])

  return (
    <div className="term">
      <div className="term-head">
        <span className="code-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        {title}
        <span className={`term-live ${live ? '' : 'idle'}`}>
          <i />
          {live ? 'LIVE' : 'DONE'}
        </span>
      </div>
      <div className="term-body" ref={bodyRef} aria-live={live ? 'polite' : undefined} style={maxHeight ? { maxHeight } : undefined}>
        {logs.length === 0 && (
          <div className="term-line">
            <Info size={14} />
            <span>Waiting for the agent to start…</span>
          </div>
        )}
        {logs.map((entry, i) => {
          const Icon = LOG_ICONS[entry.kind] || Info
          return (
            <motion.div
              key={`${entry.t}-${i}`}
              className={`term-line ${entry.kind}`}
              initial={live ? { opacity: 0, x: -8 } : false}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, ease: EASE }}
            >
              <Icon size={14} />
              <span>{entry.msg}</span>
            </motion.div>
          )
        })}
        {live && <span className="term-cursor" aria-hidden="true" />}
      </div>
      {sources.length > 0 && (
        <div className="term-sources">
          {sources.slice(0, 24).map((s) => (
            <a key={s.url} className="term-source" href={s.url} target="_blank" rel="noreferrer noopener" title={s.title || s.url}>
              <Globe size={12} />
              <span>{host(s.url)}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

export default function AgentProgress({ session, onRetry, onDismiss }) {
  const progress = session.progress || {}
  const steps = progress.steps || []
  const failed = session.status === 'failed'
  const active = session.status === 'queued' || session.status === 'running'
  const percent = progress.percent ?? 0
  const summary = session.summary || {}

  const title = active ? 'Your agent is building the prep kit' : failed ? 'Generation stopped' : 'Prep kit ready'
  const subtitle = active
    ? 'Dashboards unlock as soon as their section is ready, so you can start reading now.'
    : failed
      ? 'Anything generated before the error is still available below.'
      : `${summary.questions ?? 0} questions across ${summary.topics ?? 0} topics · finished ${
          progress.finished_at ? new Date(progress.finished_at).toLocaleTimeString() : ''
        }`

  return (
    <motion.section className="agent no-print" aria-label="Agent progress" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, ease: EASE }}>
      <div className={`agent-card ${active ? 'running' : failed ? '' : 'success'}`}>
        <div className="agent-head">
          <ProgressRing value={percent} size={76} stroke={8} label="Generation progress">
            <span className="ring-value" style={{ fontSize: 19 }}>
              {percent}%
            </span>
          </ProgressRing>
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>
          {!active && !failed && onDismiss && (
            <button className="icon-btn" onClick={onDismiss} aria-label="Hide progress panel">
              <X size={16} />
            </button>
          )}
        </div>
        <ol className="agent-steps">
          {steps.map((step) => (
            <li key={step.key} className={`agent-step ${step.status}`}>
              <span className="as-icon">
                <StepIcon status={step.status} />
              </span>
              <div>
                <div className="as-label">{step.label}</div>
                {step.detail && <div className="as-detail">{step.detail}</div>}
                {step.status === 'running' && step.fraction > 0 && step.fraction < 1 && (
                  <div className="as-bar">
                    <span style={{ width: `${Math.round(step.fraction * 100)}%` }} />
                  </div>
                )}
              </div>
            </li>
          ))}
        </ol>
        {failed && (
          <div className="stack" style={{ marginTop: 14, gap: 12 }}>
            <div className="banner-note error" role="alert">
              <CircleAlert size={18} />
              <span>{session.error || 'Something went wrong while generating this prep kit.'}</span>
            </div>
            <div>
              <button className="btn btn-primary" onClick={onRetry}>
                <RefreshCw size={16} /> Retry generation
              </button>
            </div>
          </div>
        )}
      </div>
      <TerminalLog logs={progress.logs || []} sources={progress.sources || []} live={active} />
    </motion.section>
  )
}

/**
 * One-line status shown on the other dashboards while the agent is still
 * working (or after it failed); the full panel and log live on the Overview.
 */
export function AgentStrip({ session, overviewTo }) {
  const progress = session.progress || {}
  const steps = progress.steps || []
  const failed = session.status === 'failed'
  const done = steps.filter((s) => s.status === 'done').length
  const current = steps.find((s) => s.status === 'running')

  return (
    <motion.div
      className={`agent-strip no-print ${failed ? 'failed' : ''}`}
      role={failed ? 'alert' : 'status'}
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.3, ease: EASE }}
    >
      <span className="strip-icon" aria-hidden="true">
        {failed ? <CircleAlert size={16} /> : <LoaderCircle size={16} className="spin" />}
      </span>
      <div className="strip-text" title={failed ? undefined : current?.label}>
        <strong>{failed ? 'Generation stopped' : 'Agent working'}</strong>
        {failed ? (
          <span>{session.error || 'Something went wrong. Anything already generated is still available.'}</span>
        ) : (
          <span>
            {current
              ? `Step ${Math.min(done + 1, steps.length)} of ${steps.length} · ${current.label}`
              : steps.length > 0
                ? `${done} of ${steps.length} steps done`
                : 'Starting up…'}
          </span>
        )}
      </div>
      {!failed && (
        <div className="strip-meter">
          <Meter value={progress.percent ?? 0} max={100} label="Generation progress" />
          <span>{progress.percent ?? 0}%</span>
        </div>
      )}
      <Link className="btn btn-sm strip-link" to={overviewTo}>
        {failed ? 'Details & retry' : 'Watch live'} <ArrowRight size={14} />
      </Link>
    </motion.div>
  )
}
