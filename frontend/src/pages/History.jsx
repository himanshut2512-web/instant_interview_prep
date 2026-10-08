import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { CircleAlert, CircleCheck, FolderOpen, History as HistoryIcon, LoaderCircle, Plus, Search, Trash2 } from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { EASE } from '../lib/motion.js'
import { avatarStyle, initials, timeAgo } from '../lib/format.js'
import { ModeBadge } from '../components/Badges.jsx'
import { SegmentedTabs } from '../components/Tabs.jsx'
import { EmptyState, PageBanner } from '../components/UI.jsx'
import Footer from '../components/Footer.jsx'

function StatusChip({ status }) {
  if (status === 'completed')
    return (
      <span className="chip chip-ok">
        <CircleCheck size={12} /> Ready
      </span>
    )
  if (status === 'failed')
    return (
      <span className="chip chip-bad">
        <CircleAlert size={12} /> Failed
      </span>
    )
  return (
    <span className="chip chip-brand">
      <LoaderCircle size={12} className="spin" /> Generating
    </span>
  )
}

export default function History() {
  const { notify, confirm } = useApp()
  const [sessions, setSessions] = useState(null)
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')

  useEffect(() => {
    api
      .listSessions()
      .then(setSessions)
      .catch((e) => {
        notify(e.message, 'error')
        setSessions([])
      })
  }, [notify])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return (sessions || []).filter((s) => {
      if (status === 'ready' && s.status !== 'completed') return false
      if (status === 'other' && s.status === 'completed') return false
      return !q || `${s.company} ${s.role || ''}`.toLowerCase().includes(q)
    })
  }, [sessions, query, status])

  const remove = async (event, s) => {
    event.preventDefault()
    event.stopPropagation()
    const ok = await confirm({
      title: `Delete the ${s.company} prep kit?`,
      message: 'All questions, notes and your progress for this kit will be removed permanently.',
      confirmLabel: 'Delete kit',
      tone: 'danger',
    })
    if (!ok) return
    try {
      await api.deleteSession(s.id)
      setSessions((list) => list.filter((x) => x.id !== s.id))
      notify('Prep kit deleted.')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const ready = (sessions || []).filter((s) => s.status === 'completed').length
  const totalQuestions = (sessions || []).reduce((sum, s) => sum + (s.summary?.questions || 0), 0)

  return (
    <>
      <main className="page" data-section="overview">
        <PageBanner
          icon={HistoryIcon}
          kicker="Your library"
          title="My prep kits"
          description="Every kit is saved on this server. Come back any time to revise, practise or take the quiz again."
          stats={sessions ? [{ label: 'kits', value: sessions.length }, { label: 'ready', value: ready }, { label: 'questions', value: totalQuestions }] : undefined}
          actions={
            <Link to="/new" className="btn btn-primary">
              <Plus size={16} /> New prep kit
            </Link>
          }
        />

        {sessions === null && (
          <div className="center-loader" style={{ minHeight: '30vh' }}>
            <LoaderCircle size={26} className="spin" />
          </div>
        )}

        {sessions && sessions.length === 0 && (
          <EmptyState
            icon={FolderOpen}
            title="No prep kits yet"
            text="Create your first one in under a minute: upload a resume, paste the JD, and let the agent do the research."
            action={
              <Link to="/new" className="btn btn-primary">
                <Plus size={16} /> Create a prep kit
              </Link>
            }
          />
        )}

        {sessions && sessions.length > 0 && (
          <>
            <div className="hist-toolbar">
              <div className="input-wrap sm search">
                <Search size={15} />
                <input className="input" type="search" placeholder="Search by company or role…" aria-label="Search prep kits" value={query} onChange={(e) => setQuery(e.target.value)} />
              </div>
              <SegmentedTabs
                ariaLabel="Status"
                value={status}
                onChange={setStatus}
                options={[
                  { value: 'all', label: 'All', count: sessions.length },
                  { value: 'ready', label: 'Ready', count: ready },
                  { value: 'other', label: 'In progress / failed', count: sessions.length - ready },
                ]}
              />
            </div>
            <motion.div className="hist-grid" layout>
              <AnimatePresence initial={true}>
                {filtered.map((s, i) => (
                  <motion.div
                    key={s.id}
                    layout
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0, transition: { duration: 0.4, delay: Math.min(i, 8) * 0.05, ease: EASE } }}
                    exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
                  >
                    <Link to={`/prep/${s.id}`} className="hist-card" style={{ height: '100%' }}>
                      <div className="spread">
                        <StatusChip status={s.status} />
                        <ModeBadge mode={s.mode} />
                      </div>
                      <div className="hist-top">
                        <span className="avatar" style={avatarStyle(s.company)}>
                          {initials(s.company)}
                        </span>
                        <div style={{ minWidth: 0 }}>
                          <h3>{s.company}</h3>
                          <span className="subtle">
                            {s.role || 'Role from JD'} · {s.years_experience} yrs · {s.depth}
                          </span>
                        </div>
                      </div>
                      <div className="hist-stats">
                        <div className="hs">
                          <strong>{s.summary?.questions ?? 0}</strong>
                          <span>questions</span>
                        </div>
                        <div className="hs">
                          <strong>{s.summary?.topics ?? 0}</strong>
                          <span>topics</span>
                        </div>
                        <div className="hs">
                          <strong>{s.summary?.hot ?? 0}</strong>
                          <span>hot</span>
                        </div>
                      </div>
                      <div className="hist-foot">
                        <span>Created {timeAgo(s.created_at)}</span>
                        <button className="icon-btn sm ghost btn-danger" onClick={(e) => remove(e, s)} aria-label={`Delete prep kit for ${s.company}`}>
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </AnimatePresence>
              <motion.div layout>
                <Link to="/new" className="new-tile" style={{ height: '100%' }}>
                  <span className="nt-icon">
                    <Plus size={22} />
                  </span>
                  Create a new prep kit
                  <span className="subtle" style={{ fontWeight: 500 }}>
                    Another company or role? Start fresh.
                  </span>
                </Link>
              </motion.div>
            </motion.div>
            {filtered.length === 0 && <p className="subtle" style={{ marginTop: 14 }}>No kits match your search.</p>}
          </>
        )}
      </main>
      <Footer />
    </>
  )
}
