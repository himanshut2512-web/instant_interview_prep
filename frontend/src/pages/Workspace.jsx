import { createContext, useContext, useEffect, useRef, useState } from 'react'
import { NavLink, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import {
  BookOpen,
  Code2,
  Download,
  LayoutDashboard,
  ListChecks,
  LoaderCircle,
  MessagesSquare,
  Printer,
  Puzzle,
  Trash2,
} from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { useSession } from '../hooks/useSession.js'
import AgentProgress from '../components/AgentProgress.jsx'
import { ModeBadge } from '../components/Badges.jsx'
import Overview from './Overview.jsx'
import Revision from './Revision.jsx'
import QuestionBank from './QuestionBank.jsx'
import Quiz from './Quiz.jsx'

const SessionContext = createContext(null)
export const useWorkspace = () => useContext(SessionContext)

export const SECTIONS = [
  { key: 'overview', path: '', label: 'Overview', icon: LayoutDashboard },
  { key: 'revision', path: 'revision', label: 'Crash revision', icon: BookOpen },
  { key: 'theory', path: 'theory', label: 'Theoretical', icon: MessagesSquare },
  { key: 'practical', path: 'practical', label: 'Practical', icon: Code2 },
  { key: 'scenario', path: 'scenario', label: 'Scenario-based', icon: Puzzle },
  { key: 'quiz', path: 'quiz', label: 'MCQ quiz', icon: ListChecks },
]

export default function Workspace() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { notify } = useApp()
  const ws = useSession(id)
  const { session, error } = ws
  const [justFinished, setJustFinished] = useState(false)
  const wasActive = useRef(false)
  const liveStatus = session?.status

  useEffect(() => {
    const isActive = liveStatus === 'queued' || liveStatus === 'running'
    if (wasActive.current && liveStatus === 'completed') setJustFinished(true)
    if (isActive) setJustFinished(false)
    wasActive.current = isActive
  }, [liveStatus])

  if (error) {
    return (
      <main className="page">
        <div className="banner error">{error}</div>
      </main>
    )
  }
  if (!session) {
    return (
      <div className="center-loader">
        <LoaderCircle size={28} className="spin" />
        <span>Loading your prep kit…</span>
      </div>
    )
  }

  const result = session.result || {}
  const ready = new Set(session.progress?.sections_ready || [])
  const active = session.status === 'queued' || session.status === 'running'
  const showProgress = active || session.status === 'failed' || justFinished
  const hasContent = (key) => (key === 'overview' ? (result.topics || []).length > 0 : (result[key] || []).length > 0)
  const count = (key) => (key === 'overview' ? null : (result[key] || []).length)

  const remove = async () => {
    if (!window.confirm('Delete this prep kit permanently?')) return
    try {
      await api.deleteSession(id)
      notify('Prep kit deleted.')
      navigate('/preps')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const retry = async () => {
    try {
      await ws.retry()
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const navItems = SECTIONS.map((s) => {
    const enabled = hasContent(s.key) || (!active && s.key === 'overview')
    return { ...s, enabled, loading: active && !ready.has(s.key) }
  })

  return (
    <SessionContext.Provider value={{ ...ws, session, aiMode: session.mode === 'ai', retry }}>
      <div className="workspace">
        <nav className="sidenav" aria-label="Prep kit sections">
          <div className="sidenav-head">
            <strong title={session.company}>{session.company}</strong>
            <span className="subtle">
              {session.role || 'Role from JD'} · {session.years_experience} yrs
            </span>
            <div style={{ marginTop: 8 }}>
              <ModeBadge mode={session.mode} />
            </div>
          </div>
          {navItems.map(({ key, path, label, icon: Icon, enabled, loading }) => (
            <NavLink key={key} to={path ? `/prep/${id}/${path}` : `/prep/${id}`} end={!path} className={({ isActive }) => `${isActive ? 'active' : ''} ${enabled ? '' : 'disabled'}`}>
              <Icon size={17} />
              {label}
              {loading && !enabled ? (
                <LoaderCircle size={14} className="spin" style={{ marginLeft: 'auto' }} />
              ) : (
                count(key) !== null && <span className="nav-count">{count(key)}</span>
              )}
            </NavLink>
          ))}
          <div className="sidenav-foot">
            <a className="btn btn-sm" href={api.exportUrl(id)} download>
              <Download size={15} /> Export Markdown
            </a>
            <a className="btn btn-sm" href={`/prep/${id}/print`} target="_blank" rel="noreferrer">
              <Printer size={15} /> Print / save PDF
            </a>
            <button className="btn btn-sm btn-ghost btn-danger" onClick={remove}>
              <Trash2 size={15} /> Delete kit
            </button>
          </div>
        </nav>

        <main style={{ minWidth: 0 }}>
          <div className="mobile-tabs" aria-label="Prep kit sections">
            {navItems.map(({ key, path, label, enabled }) => (
              <NavLink key={key} to={path ? `/prep/${id}/${path}` : `/prep/${id}`} end={!path} style={enabled ? undefined : { opacity: 0.5, pointerEvents: 'none' }}>
                {label} {count(key) !== null ? `(${count(key)})` : ''}
              </NavLink>
            ))}
          </div>
          {showProgress && <AgentProgress session={session} onRetry={retry} onDismiss={() => setJustFinished(false)} />}
          <Routes>
            <Route index element={<Overview />} />
            <Route path="revision" element={<Revision />} />
            <Route path="theory" element={<QuestionBank section="theory" />} />
            <Route path="practical" element={<QuestionBank section="practical" />} />
            <Route path="scenario" element={<QuestionBank section="scenario" />} />
            <Route path="quiz" element={<Quiz />} />
          </Routes>
        </main>
      </div>
    </SessionContext.Provider>
  )
}
