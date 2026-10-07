import { useEffect, useRef } from 'react'
import {
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

function StepIcon({ status }) {
  if (status === 'done') return <Check size={14} />
  if (status === 'running') return <LoaderCircle size={14} className="spin" />
  if (status === 'failed') return <X size={14} />
  return <CircleDashed size={14} />
}

function host(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export function LogLines({ logs }) {
  return logs.map((entry, i) => {
    const Icon = LOG_ICONS[entry.kind] || Info
    return (
      <div key={i} className={`log-line ${entry.kind}`}>
        <Icon size={14} />
        <span>{entry.msg}</span>
      </div>
    )
  })
}

export default function AgentProgress({ session, onRetry, onDismiss }) {
  const progress = session.progress || {}
  const logRef = useRef(null)
  const logs = progress.logs || []
  const failed = session.status === 'failed'
  const active = session.status === 'queued' || session.status === 'running'

  useEffect(() => {
    const el = logRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs.length])

  return (
    <section className="agent-panel no-print" aria-label="Agent progress">
      <div className="card">
        <div className="progress-head">
          <div>
            <div className="card-title" style={{ marginBottom: 2 }}>
              {active ? <LoaderCircle size={18} className="spin" /> : failed ? <CircleAlert size={18} /> : <CircleCheck size={18} />}
              {active ? 'Your agent is building the prep kit' : failed ? 'Generation stopped' : 'Prep kit ready'}
            </div>
            <div className="subtle">
              {active
                ? 'Sections unlock as soon as they are ready - you can start reading now.'
                : failed
                  ? 'Content generated before the error is still available below.'
                  : `${session.summary?.questions ?? 0} questions across ${session.summary?.topics ?? 0} topics · finished ${progress.finished_at ? new Date(progress.finished_at).toLocaleTimeString() : ''}`}
            </div>
          </div>
          <div className="row">
            <div className="progress-pct">{progress.percent ?? 0}%</div>
            {!active && !failed && onDismiss && (
              <button className="icon-btn" onClick={onDismiss} aria-label="Hide progress panel">
                <X size={16} />
              </button>
            )}
          </div>
        </div>
        <div className="progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress.percent ?? 0}>
          <div style={{ width: `${progress.percent ?? 0}%` }} />
        </div>
        <ol className="timeline">
          {(progress.steps || []).map((step) => (
            <li key={step.key} className={step.status}>
              <span className="t-icon">
                <StepIcon status={step.status} />
              </span>
              <div>
                <div className="t-label">{step.label}</div>
                {step.detail && <div className="t-detail">{step.detail}</div>}
              </div>
            </li>
          ))}
        </ol>
        {failed && (
          <div className="stack" style={{ marginTop: 12, gap: 10 }}>
            <div className="banner error" role="alert">
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
      <div className="card">
        <div className="card-title">
          <MessagesSquare size={18} />
          Live agent log
        </div>
        <div className="log" ref={logRef} aria-live="polite">
          {logs.length === 0 && <div className="subtle">Waiting for the agent to start…</div>}
          <LogLines logs={logs} />
        </div>
        {(progress.sources || []).length > 0 && (
          <>
            <div className="card-title" style={{ marginTop: 16 }}>
              <Globe size={18} />
              Sources found ({progress.sources.length})
            </div>
            <div className="sources">
              {progress.sources.slice(0, 24).map((s) => (
                <a key={s.url} className="source-chip" href={s.url} target="_blank" rel="noreferrer noopener" title={s.title}>
                  <Globe size={12} />
                  <span>{s.title || host(s.url)}</span>
                </a>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  )
}
