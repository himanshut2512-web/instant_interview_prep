import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CircleAlert, CircleCheck, FolderOpen, LoaderCircle, Plus, Trash2 } from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { ModeBadge } from '../components/Badges.jsx'

function StatusChip({ status }) {
  if (status === 'completed')
    return (
      <span className="chip chip-good">
        <CircleCheck size={12} /> Ready
      </span>
    )
  if (status === 'failed')
    return (
      <span className="chip chip-critical">
        <CircleAlert size={12} /> Failed
      </span>
    )
  return (
    <span className="chip chip-accent">
      <LoaderCircle size={12} className="spin" /> Generating
    </span>
  )
}

export default function History() {
  const { notify } = useApp()
  const [sessions, setSessions] = useState(null)

  const load = () =>
    api
      .listSessions()
      .then(setSessions)
      .catch((e) => {
        notify(e.message, 'error')
        setSessions([])
      })

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const remove = async (event, id) => {
    event.preventDefault()
    if (!window.confirm('Delete this prep kit permanently?')) return
    try {
      await api.deleteSession(id)
      setSessions((list) => list.filter((s) => s.id !== id))
      notify('Prep kit deleted.')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  return (
    <main className="page">
      <div className="section-head">
        <div>
          <h1>My prep kits</h1>
          <p>Every kit is saved on this server - come back any time to revise, practise or take the quiz again.</p>
        </div>
        <Link to="/" className="btn btn-primary">
          <Plus size={16} /> New prep kit
        </Link>
      </div>
      {sessions === null && (
        <div className="center-loader">
          <LoaderCircle size={26} className="spin" />
        </div>
      )}
      {sessions && sessions.length === 0 && (
        <div className="card empty">
          <FolderOpen size={28} />
          <p>No prep kits yet. Create your first one in under a minute.</p>
          <Link to="/" className="btn btn-primary">
            Create a prep kit
          </Link>
        </div>
      )}
      {sessions && sessions.length > 0 && (
        <div className="history-grid">
          {sessions.map((s) => (
            <Link key={s.id} to={`/prep/${s.id}`} className="card history-card">
              <div className="spread">
                <StatusChip status={s.status} />
                <ModeBadge mode={s.mode} />
              </div>
              <h3 style={{ margin: 0 }}>{s.company}</h3>
              <div className="muted">
                {s.role || 'Role from JD'} · {s.years_experience} yrs · {s.depth}
              </div>
              <div className="subtle">
                {s.summary?.questions ?? 0} questions · {s.summary?.topics ?? 0} topics · {s.summary?.hot ?? 0} hot
              </div>
              <div className="spread" style={{ marginTop: 'auto' }}>
                <span className="subtle">{new Date(s.created_at).toLocaleString()}</span>
                <button className="btn btn-ghost btn-sm btn-danger" onClick={(e) => remove(e, s.id)} aria-label={`Delete prep kit for ${s.company}`}>
                  <Trash2 size={15} />
                </button>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}
