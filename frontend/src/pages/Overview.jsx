import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BadgeCheck,
  Bot,
  Building2,
  CalendarClock,
  CircleCheck,
  Copy,
  ExternalLink,
  Flame,
  Globe,
  Info,
  Layers,
  MessageCircleQuestion,
  Quote,
  RefreshCw,
  Route,
  ScrollText,
  Search,
  Target,
  TriangleAlert,
  UserRound,
} from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import Markdown from '../components/Markdown.jsx'
import { LogLines } from '../components/AgentProgress.jsx'
import { BarList, Meter, StatTile } from '../components/Viz.jsx'

const RESEARCH_LABEL = {
  live_web: 'Live web research',
  search_fallback: 'Backup web search',
  model_knowledge: "Claude's knowledge (no live web)",
  offline: 'Offline knowledge base',
}

function List({ items, icon: Icon, className }) {
  if (!items?.length) return <p className="subtle">Nothing here yet.</p>
  return (
    <ul className="list-clean">
      {items.map((text, i) => (
        <li key={i}>
          <Icon size={15} className={className} />
          <span>{text}</span>
        </li>
      ))}
    </ul>
  )
}

export default function Overview() {
  const { session, aiMode, retry } = useWorkspace()
  const { notify } = useApp()
  const navigate = useNavigate()
  const [showReport, setShowReport] = useState(false)
  const [showLog, setShowLog] = useState(false)
  const result = session.result || {}
  const profile = result.profile || {}
  const company = result.company || {}
  const topics = result.topics || []
  const items = session.user_state?.items || {}
  const revisedTopics = session.user_state?.topics || {}
  const attempts = session.quiz_attempts || []

  const stats = useMemo(() => {
    const interview = ['theory', 'practical', 'scenario'].flatMap((s) => result[s] || [])
    const mastered = interview.filter((q) => items[q.id] === 'mastered').length
    const bySection = Object.fromEntries(
      ['theory', 'practical', 'scenario'].map((s) => {
        const list = result[s] || []
        return [s, { total: list.length, mastered: list.filter((q) => items[q.id] === 'mastered').length }]
      }),
    )
    const revisionTotal = (result.revision || []).length
    const revised = (result.revision || []).filter((n) => revisedTopics[n.id]).length
    const best = attempts.length ? Math.max(...attempts.map((a) => a.score_pct)) : null
    return { interview: interview.length, mastered, bySection, revisionTotal, revised, best }
  }, [result, items, revisedTopics, attempts])

  if (!topics.length) {
    return (
      <div className="card empty">
        <Layers size={28} />
        <p>The overview appears as soon as the agent finishes analysing your profile and the company.</p>
      </div>
    )
  }

  const counts = session.summary || {}
  const warnings = [...new Set(session.warnings || [])]
  const copyPitch = async () => {
    try {
      await navigator.clipboard.writeText(profile.elevator_pitch)
      notify('Pitch copied to clipboard.')
    } catch {
      notify('Copy failed - select the text manually.', 'error')
    }
  }

  return (
    <div>
      <div className="section-head">
        <div>
          <h1>
            {session.role || profile.target_role || 'Your target role'} at {session.company}
          </h1>
          <p>
            {session.years_experience} years of experience · {profile.seniority || 'Experience-calibrated'} · created{' '}
            {new Date(session.created_at).toLocaleDateString()}
          </p>
          <div className="row wrap" style={{ marginTop: 8 }}>
            <span className={`chip ${company.research_mode === 'live_web' ? 'chip-good' : ''}`}>
              <Globe size={12} /> {RESEARCH_LABEL[company.research_mode] || 'Research'}
            </span>
            {(company.sources || []).length > 0 && <span className="chip">{company.sources.length} sources</span>}
          </div>
        </div>
        {session.status !== 'running' && session.status !== 'queued' && (
          <button
            className="btn btn-sm no-print"
            onClick={() => window.confirm('Regenerate the whole prep kit? Current content will be replaced.') && retry()}
          >
            <RefreshCw size={15} /> Regenerate
          </button>
        )}
      </div>

      {warnings.map((w) => (
        <div key={w} className="banner warn" style={{ marginBottom: 12 }}>
          <Info size={18} />
          <span>{w}</span>
        </div>
      ))}

      <div className="kpi-row">
        <StatTile label="Interview questions" value={counts.questions ?? 0} sub={`${counts.theory ?? 0} theory · ${counts.practical ?? 0} practical · ${counts.scenario ?? 0} scenario · ${counts.quiz ?? 0} MCQs`} icon={MessageCircleQuestion} />
        <StatTile label="Topics planned" value={topics.length} sub={`${counts.revision ?? 0} crash-revision notes`} icon={Layers} />
        <StatTile label="Hot questions" value={counts.hot ?? 0} sub={aiMode ? 'Reported or frequently asked' : 'Classic, frequently asked'} icon={Flame} />
        <StatTile label="Mastered" value={`${stats.mastered}/${stats.interview}`} sub={`${stats.interview ? Math.round((100 * stats.mastered) / stats.interview) : 0}% of interview questions`} icon={BadgeCheck}>
          <div style={{ marginTop: 8 }}>
            <Meter value={stats.mastered} max={Math.max(1, stats.interview)} label="Share of interview questions mastered" />
          </div>
        </StatTile>
      </div>

      <div className="ov-grid">
        <section className="card">
          <div className="card-title">
            <Target size={18} /> Readiness
          </div>
          <div className="stack" style={{ gap: 12 }}>
            {[
              ['Theory', stats.bySection.theory],
              ['Practical', stats.bySection.practical],
              ['Scenario', stats.bySection.scenario],
            ].map(([label, s]) => (
              <div className="meter-row" key={label}>
                <span>{label}</span>
                <Meter value={s.mastered} max={Math.max(1, s.total)} label={`${label} mastered`} />
                <span className="val">
                  {s.mastered}/{s.total} mastered
                </span>
              </div>
            ))}
            <div className="meter-row">
              <span>Revision</span>
              <Meter value={stats.revised} max={Math.max(1, stats.revisionTotal)} label="Topics revised" />
              <span className="val">
                {stats.revised}/{stats.revisionTotal} revised
              </span>
            </div>
            <div className="meter-row">
              <span>Quiz best</span>
              <Meter value={stats.best ?? 0} max={100} label="Best quiz score" />
              <span className="val">{stats.best === null ? 'not taken' : `${stats.best}%`}</span>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-title">
            <UserRound size={18} /> Your snapshot
          </div>
          {profile.summary && <p>{profile.summary}</p>}
          {(profile.matched_skills || []).length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div className="subtle" style={{ marginBottom: 4 }}>Skills you match</div>
              <div className="skill-chips">
                {profile.matched_skills.map((s) => (
                  <span key={s} className="chip chip-accent">
                    <CircleCheck size={12} /> {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          {(profile.missing_skills || []).length > 0 && (
            <div>
              <div className="subtle" style={{ marginBottom: 4 }}>Skills to brush up</div>
              <div className="skill-chips">
                {profile.missing_skills.map((s) => (
                  <span key={s} className="chip">
                    <TriangleAlert size={12} /> {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>

        <section className="card wide">
          <div className="spread" style={{ marginBottom: 10 }}>
            <div className="card-title" style={{ margin: 0 }}>
              <Quote size={18} /> "Tell me about yourself" - your pitch
            </div>
            {profile.elevator_pitch && (
              <button className="btn btn-sm no-print" onClick={copyPitch}>
                <Copy size={15} /> Copy
              </button>
            )}
          </div>
          <p className="pitch">{profile.elevator_pitch || 'Not available.'}</p>
          <div className="two-col">
            <div>
              <h3 className="label">Strengths to lean on</h3>
              <List items={profile.strengths} icon={CircleCheck} className="icon-good" />
            </div>
            <div>
              <h3 className="label">Gaps to prepare for</h3>
              <List items={profile.gaps} icon={TriangleAlert} className="icon-warn" />
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-title">
            <Route size={18} /> Interview process at {company.name || session.company}
          </div>
          {company.overview && <p className="muted">{company.overview}</p>}
          <ol className="rounds">
            {(company.interview_rounds || []).map((r, i) => (
              <li key={i}>
                <strong>{r.name}</strong>
                <span className="subtle">{r.format}</span>
                {r.what_they_test && <div style={{ fontSize: '0.9rem' }}>{r.what_they_test}</div>}
                {r.tips && <div className="subtle">Tip: {r.tips}</div>}
              </li>
            ))}
          </ol>
        </section>

        <section className="card">
          <div className="card-title">
            <Building2 size={18} /> What they look for
          </div>
          {company.hiring_focus && <p>{company.hiring_focus}</p>}
          {(company.focus_areas || []).length > 0 && (
            <div className="skill-chips" style={{ marginBottom: 12 }}>
              {company.focus_areas.map((f) => (
                <span key={f} className="chip">
                  {f}
                </span>
              ))}
            </div>
          )}
          {(company.culture_values || []).length > 0 && (
            <>
              <h3 className="label">Culture & values</h3>
              <List items={company.culture_values} icon={BadgeCheck} className="icon-accent" />
            </>
          )}
          {(company.insider_tips || []).length > 0 && (
            <>
              <h3 className="label" style={{ marginTop: 12 }}>Insider tips</h3>
              <List items={company.insider_tips} icon={Info} className="icon-accent" />
            </>
          )}
        </section>

        <section className="card wide">
          <div className="card-title">
            <Layers size={18} /> Topic priority
          </div>
          <p className="subtle" style={{ marginTop: -6 }}>
            Relative likelihood of each topic coming up. Select a topic to open its crash-revision notes.
          </p>
          <BarList
            ariaLabel="Topic priority weights"
            items={topics.map((t) => ({
              key: t.id,
              label: t.name,
              value: t.weight,
              max: 100,
              display: `${t.weight}`,
              tooltip: { title: `${t.name} · ${t.priority} priority`, lines: [t.why, (t.subtopics || []).slice(0, 5).join(', ')].filter(Boolean) },
            }))}
            onSelect={(item) => navigate(`/prep/${session.id}/revision?topic=${encodeURIComponent(item.label)}`)}
          />
        </section>

        {(company.reported_questions || []).length > 0 ? (
          <section className="card wide">
            <div className="card-title">
              <Flame size={18} /> Questions candidates reported
            </div>
            <ul className="list-clean">
              {company.reported_questions.map((q, i) => (
                <li key={i}>
                  <MessageCircleQuestion size={15} className="icon-hot" />
                  <span>
                    {q.question}{' '}
                    <span className="subtle">{[q.round, q.source].filter(Boolean).join(' · ')}</span>
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="card">
          <div className="card-title">
            <Search size={18} /> Resume deep-dive
          </div>
          <p className="subtle" style={{ marginTop: -6 }}>Interviewers will probe these - have numbers and trade-offs ready.</p>
          {(profile.resume_probes || []).length === 0 && <p className="subtle">No specific probes identified.</p>}
          {(profile.resume_probes || []).map((p, i) => (
            <div className="probe" key={i}>
              <strong>{p.item}</strong>
              <ul>
                {(p.likely_questions || []).map((q, j) => (
                  <li key={j}>{q}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>

        <section className="card">
          <div className="card-title">
            <MessageCircleQuestion size={18} /> Questions to ask them
          </div>
          <List items={company.questions_to_ask_them} icon={MessageCircleQuestion} className="icon-accent" />
        </section>

        {(result.study_plan || []).length > 0 && (
          <section className="card wide">
            <div className="card-title">
              <CalendarClock size={18} /> Study plan
            </div>
            <div className="study-blocks">
              {result.study_plan.map((b, i) => (
                <div className="study-block" key={i}>
                  <h4>{b.title}</h4>
                  <div style={{ fontSize: '0.88rem' }}>{b.focus}</div>
                  <ul>
                    {(b.tasks || []).map((t, j) => (
                      <li key={j}>{t}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        )}

        {(session.progress?.logs || []).length > 0 && (
          <section className="card wide no-print">
            <div className="spread">
              <div className="card-title" style={{ margin: 0 }}>
                <Bot size={18} /> How the agent built this kit
              </div>
              <button className="btn btn-sm" onClick={() => setShowLog((v) => !v)} aria-expanded={showLog}>
                {showLog ? 'Hide activity' : `Show activity (${session.progress.logs.length} steps)`}
              </button>
            </div>
            {showLog && (
              <div className="log" style={{ marginTop: 12, maxHeight: 420 }}>
                <LogLines logs={session.progress.logs} />
              </div>
            )}
          </section>
        )}

        <section className="card wide">
          <div className="spread">
            <div className="card-title" style={{ margin: 0 }}>
              <ScrollText size={18} /> Research report & sources
            </div>
            <button className="btn btn-sm no-print" onClick={() => setShowReport((v) => !v)} aria-expanded={showReport}>
              {showReport ? 'Hide report' : 'Show full report'}
            </button>
          </div>
          {showReport && <Markdown className="qsection">{company.research_md}</Markdown>}
          {(company.sources || []).length > 0 ? (
            <ul className="list-clean" style={{ marginTop: 12 }}>
              {company.sources.map((s) => (
                <li key={s.url}>
                  <ExternalLink size={15} className="icon-accent" />
                  <a href={s.url} target="_blank" rel="noreferrer noopener">
                    {s.title || s.url}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="subtle" style={{ marginTop: 10 }}>
              No web sources for this kit{aiMode ? '.' : ' - offline demo mode does not browse the web.'}
            </p>
          )}
        </section>
      </div>
    </div>
  )
}
