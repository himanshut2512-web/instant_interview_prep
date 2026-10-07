import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import {
  BookOpen,
  Code2,
  Download,
  EllipsisVertical,
  LayoutDashboard,
  ListChecks,
  LoaderCircle,
  MessagesSquare,
  Printer,
  Puzzle,
  Trash2,
  Zap,
} from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { useSession } from '../hooks/useSession.js'
import { computeProgress } from '../lib/progress.js'
import { avatarStyle, initials, timeAgo } from '../lib/format.js'
import { EASE } from '../lib/motion.js'
import AgentProgress, { AgentStrip } from '../components/AgentProgress.jsx'
import { ModeBadge } from '../components/Badges.jsx'
import { Meter } from '../components/Viz.jsx'
import { EmptyState } from '../components/UI.jsx'
import Overview from './Overview.jsx'
import Revision from './Revision.jsx'
import QuestionBank from './QuestionBank.jsx'
import Quiz from './Quiz.jsx'

const SessionContext = createContext(null)
export const useWorkspace = () => useContext(SessionContext)

export const SECTIONS = [
  { key: 'overview', path: '', label: 'Overview', short: 'Overview', icon: LayoutDashboard },
  { key: 'revision', path: 'revision', label: 'Crash revision', short: 'Revise', icon: BookOpen },
  { key: 'theory', path: 'theory', label: 'Theoretical', short: 'Theory', icon: MessagesSquare },
  { key: 'practical', path: 'practical', label: 'Practical', short: 'Practical', icon: Code2 },
  { key: 'scenario', path: 'scenario', label: 'Scenario-based', short: 'Scenario', icon: Puzzle },
  { key: 'quiz', path: 'quiz', label: 'MCQ quiz', short: 'Quiz', icon: ListChecks },
]

function KitMenu({ id, onDelete }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    if (!open) return undefined
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false)
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])
  return (
    <div className="menu-wrap" ref={ref} style={{ marginLeft: 'auto' }}>
      <button className="icon-btn" aria-label="Kit actions" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <EllipsisVertical size={18} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div className="menu" role="menu" initial={{ opacity: 0, y: -6, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: 0.97 }} transition={{ duration: 0.16 }}>
            <a className="menu-item" role="menuitem" href={api.exportUrl(id)} download>
              <Download size={16} /> Export Markdown
            </a>
            <a className="menu-item" role="menuitem" href={`/prep/${id}/print`} target="_blank" rel="noreferrer">
              <Printer size={16} /> Print / save PDF
            </a>
            <div className="menu-sep" />
            <button
              className="menu-item danger"
              role="menuitem"
              onClick={() => {
                setOpen(false)
                onDelete()
              }}
            >
              <Trash2 size={16} /> Delete kit
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function Workspace() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { notify, confirm } = useApp()
  const ws = useSession(id)
  const { session, error } = ws
  const [justFinished, setJustFinished] = useState(false)
  const wasActive = useRef(false)
  const seenReady = useRef(false)
  const liveStatus = session?.status
  const overviewTo = `/prep/${id}`
  const onOverview = location.pathname.replace(/\/+$/, '') === overviewTo

  // When a run completes, the "Prep kit ready" summary is shown once, on the
  // Overview. Finishing elsewhere gets a toast instead, and the summary waits
  // for the next Overview visit.
  useEffect(() => {
    const isActive = liveStatus === 'queued' || liveStatus === 'running'
    if (wasActive.current && liveStatus === 'completed') {
      setJustFinished(true)
      if (!onOverview) {
        const summary = session?.summary || {}
        notify(`Your prep kit is ready: ${summary.questions ?? 0} questions across ${summary.topics ?? 0} topics.`)
      }
    }
    if (isActive) setJustFinished(false)
    wasActive.current = isActive
    // eslint-disable-next-line react-hooks/exhaustive-deps -- react to status changes only
  }, [liveStatus])

  // Once seen on the Overview, the summary goes away when you leave it.
  useEffect(() => {
    if (!justFinished) {
      seenReady.current = false
      return
    }
    if (onOverview) seenReady.current = true
    else if (seenReady.current) setJustFinished(false)
  }, [justFinished, onOverview])

  useEffect(() => {
    window.scrollTo({ top: 0 })
  }, [location.pathname])

  const progressInfo = useMemo(() => (session ? computeProgress(session) : null), [session])

  if (error) {
    return (
      <main className="page">
        <EmptyState icon={LayoutDashboard} title="We couldn't open this prep kit" text={error} action={<a className="btn btn-primary" href="/preps">Back to my prep kits</a>} />
      </main>
    )
  }
  if (!session) {
    return (
      <div className="center-loader" role="status">
        <span className="loader-orb">
          <Zap size={22} fill="currentColor" strokeWidth={1.6} />
        </span>
        <span>Loading your prep kit…</span>
      </div>
    )
  }

  const result = session.result || {}
  const ready = new Set(session.progress?.sections_ready || [])
  const active = session.status === 'queued' || session.status === 'running'
  const failed = session.status === 'failed'
  const showPanel = onOverview && (active || failed || justFinished)
  const showStrip = !onOverview && (active || failed)
  const hasContent = (key) => (key === 'overview' ? (result.topics || []).length > 0 : (result[key] || []).length > 0)
  const count = (key) => (key === 'overview' ? null : (result[key] || []).length)

  const remove = async () => {
    const ok = await confirm({
      title: 'Delete this prep kit?',
      message: `The kit for ${session.company} and all your progress will be removed permanently.`,
      confirmLabel: 'Delete kit',
      tone: 'danger',
    })
    if (!ok) return
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

  const navItems = SECTIONS.map((s) => ({
    ...s,
    enabled: hasContent(s.key) || (!active && s.key === 'overview'),
    loading: active && !ready.has(s.key),
    to: s.path ? `/prep/${id}/${s.path}` : `/prep/${id}`,
  }))

  return (
    <SessionContext.Provider value={{ ...ws, session, aiMode: session.mode === 'ai', retry, progressInfo, remove }}>
      <div className="ws">
        <aside className="ws-side no-print" aria-label="Prep kit navigation">
          <motion.div className="kit-card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }}>
            <div className="kit-id">
              <span className="avatar" style={avatarStyle(session.company)}>
                {initials(session.company)}
              </span>
              <div style={{ minWidth: 0 }}>
                <strong className="kit-name" title={session.company}>
                  {session.company}
                </strong>
                <span className="kit-sub">
                  {session.role || 'Role from JD'} · {session.years_experience} yrs
                </span>
              </div>
            </div>
            <div className="kit-meta">
              <ModeBadge mode={session.mode} />
              <span className="subtle">{timeAgo(session.created_at)}</span>
            </div>
            <div className="kit-ready">
              <div className="row">
                <span>Interview readiness</span>
                <strong>{progressInfo.readiness}%</strong>
              </div>
              <Meter value={progressInfo.readiness} max={100} label="Interview readiness" />
            </div>
          </motion.div>

          <nav className="side-nav">
            {navItems.map(({ key, label, icon: Icon, enabled, loading, to }) => (
              <NavLink key={key} to={to} end={key === 'overview'} data-section={key} className={({ isActive }) => `side-link ${isActive ? 'active' : ''} ${enabled ? '' : 'disabled'}`}>
                {({ isActive }) => (
                  <>
                    {isActive && <motion.span layoutId="side-active" className="side-active" transition={{ type: 'spring', stiffness: 460, damping: 38 }} />}
                    <span className="side-ico">
                      <Icon size={17} />
                    </span>
                    {label}
                    {loading && !enabled ? (
                      <LoaderCircle size={15} className="spin" style={{ marginLeft: 'auto', color: 'var(--ink-3)' }} />
                    ) : (
                      count(key) !== null && <span className="side-count">{count(key)}</span>
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="side-actions">
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
        </aside>

        <main className="ws-main">
          <div className="ws-mobile-head no-print">
            <span className="avatar sm" style={avatarStyle(session.company)}>
              {initials(session.company)}
            </span>
            <div style={{ minWidth: 0 }}>
              <strong className="ellipsis" style={{ display: 'block', fontFamily: 'var(--font-display)' }}>
                {session.company}
              </strong>
              <span className="subtle ellipsis" style={{ display: 'block' }}>
                {session.role || 'Role from JD'} · readiness {progressInfo.readiness}%
              </span>
            </div>
            <KitMenu id={id} onDelete={remove} />
          </div>

          {showPanel && <AgentProgress session={session} onRetry={retry} onDismiss={() => setJustFinished(false)} />}
          <AnimatePresence>{showStrip && <AgentStrip key="strip" session={session} overviewTo={overviewTo} />}</AnimatePresence>

          <motion.div key={location.pathname} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: EASE }}>
            <Routes>
              <Route index element={<Overview />} />
              <Route path="revision" element={<Revision />} />
              <Route path="theory" element={<QuestionBank section="theory" />} />
              <Route path="practical" element={<QuestionBank section="practical" />} />
              <Route path="scenario" element={<QuestionBank section="scenario" />} />
              <Route path="quiz" element={<Quiz />} />
            </Routes>
          </motion.div>
        </main>

        <nav className="ws-tabbar no-print" aria-label="Prep kit sections">
          {navItems.map(({ key, short, icon: Icon, enabled, loading, to }) => (
            <NavLink key={key} to={to} end={key === 'overview'} data-section={key} className={({ isActive }) => `tab-link ${isActive ? 'active' : ''} ${enabled ? '' : 'disabled'}`}>
              {({ isActive }) => (
                <>
                  {isActive && <motion.span layoutId="tab-active" className="tab-active" transition={{ type: 'spring', stiffness: 460, damping: 38 }} />}
                  {loading && !enabled ? <LoaderCircle size={20} className="spin" /> : <Icon size={20} />}
                  <span>{short}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
    </SessionContext.Provider>
  )
}
