import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import {
  ArrowRight,
  BadgeCheck,
  Bot,
  Building2,
  CalendarClock,
  ChevronDown,
  CircleCheck,
  Copy,
  Download,
  ExternalLink,
  Flame,
  Globe,
  Grid3x3,
  Info,
  Layers,
  LayoutDashboard,
  Lightbulb,
  MessageCircleQuestion,
  Quote,
  RefreshCw,
  Route,
  ScrollText,
  Search,
  TriangleAlert,
  UserRound,
} from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { useWorkspace, SECTIONS } from './Workspace.jsx'
import { EASE, fadeUp, stagger } from '../lib/motion.js'
import { pct, seniority } from '../lib/format.js'
import Markdown from '../components/Markdown.jsx'
import { TerminalLog } from '../components/AgentProgress.jsx'
import { BarList, Heatmap, Meter, ProgressRing, StackedBar, StatTile } from '../components/Viz.jsx'
import { CardTitle, EmptyState, PageBanner } from '../components/UI.jsx'
import { LEVELS, LEVEL_LABEL } from '../components/Badges.jsx'

const reveal = { variants: fadeUp, initial: 'hidden', whileInView: 'show', viewport: { once: true, amount: 0.12 } }

const RESEARCH_LABEL = {
  live_web: 'Live web research',
  search_fallback: 'Backup web search',
  model_knowledge: "Claude's knowledge (no live web)",
  offline: 'Offline knowledge base',
}

// Validated adjacent order for the composition bar (palette validator, both themes).
const COMPOSITION = [
  { key: 'quiz', label: 'MCQs', color: 'var(--c-quiz)' },
  { key: 'theory', label: 'Theory', color: 'var(--c-theory)' },
  { key: 'practical', label: 'Practical', color: 'var(--c-practical)' },
  { key: 'scenario', label: 'Scenario', color: 'var(--c-scenario)' },
]

const READINESS_NOTE = 'Readiness averages revision, mastered questions and your best quiz score.'

const SECTION_NOUN = { theory: 'Theory', practical: 'Practical', scenario: 'Scenario', quiz: 'MCQ' }

function Bullets({ items, icon: Icon, className }) {
  if (!items?.length) return <p className="subtle" style={{ margin: 0 }}>Nothing here yet.</p>
  return (
    <ul className="list-clean">
      {items.map((text, i) => (
        <li key={i}>
          <Icon size={16} className={className} />
          <span>{text}</span>
        </li>
      ))}
    </ul>
  )
}

export default function Overview() {
  const { session, aiMode, retry, progressInfo: p } = useWorkspace()
  const { notify, confirm } = useApp()
  const navigate = useNavigate()
  const [showReport, setShowReport] = useState(false)
  const [showLog, setShowLog] = useState(false)
  const [openProbe, setOpenProbe] = useState(0)
  const result = session.result || {}
  const profile = result.profile || {}
  const company = result.company || {}
  const topics = result.topics || []
  const counts = session.summary || {}
  const base = `/prep/${session.id}`

  const coverage = useMemo(() => {
    const table = {}
    for (const section of ['theory', 'practical', 'scenario', 'quiz']) {
      for (const q of result[section] || []) {
        const key = `${q.topic}|${q.level}`
        table[key] = table[key] || { value: 0, bySection: {} }
        table[key].value += 1
        table[key].bySection[section] = (table[key].bySection[section] || 0) + 1
      }
    }
    return table
  }, [result])

  if (!topics.length) {
    return (
      <div data-section="overview">
        <EmptyState icon={LayoutDashboard} title="Analysing your profile…" text="The overview appears as soon as the agent has matched your resume to the JD and the company research." />
      </div>
    )
  }

  const warnings = [...new Set(session.warnings || [])]
  const active = session.status === 'running' || session.status === 'queued'
  const matched = profile.matched_skills || []
  const missing = profile.missing_skills || []
  const matchPct = pct(matched.length, matched.length + missing.length)
  const reported = company.reported_questions || []

  const copyPitch = async () => {
    try {
      await navigator.clipboard.writeText(profile.elevator_pitch)
      notify('Pitch copied to clipboard.')
    } catch {
      notify('Copy failed: select the text manually.', 'error')
    }
  }

  const regenerate = async () => {
    const ok = await confirm({
      title: 'Regenerate the whole prep kit?',
      message: 'The agent will run again from scratch. Current questions, notes and progress for this kit will be replaced.',
      confirmLabel: 'Regenerate',
    })
    if (ok) retry()
  }

  const dashTiles = [
    { key: 'revision', count: counts.revision ?? 0, label: 'Revision notes', progress: p.revised, total: p.revisionTotal, unit: 'revised' },
    { key: 'theory', count: counts.theory ?? 0, label: 'Theory questions', progress: p.sections.theory?.mastered || 0, total: p.sections.theory?.total || 0, unit: 'mastered' },
    { key: 'practical', count: counts.practical ?? 0, label: 'Practical problems', progress: p.sections.practical?.mastered || 0, total: p.sections.practical?.total || 0, unit: 'mastered' },
    { key: 'scenario', count: counts.scenario ?? 0, label: 'Scenarios', progress: p.sections.scenario?.mastered || 0, total: p.sections.scenario?.total || 0, unit: 'mastered' },
    { key: 'quiz', count: counts.quiz ?? 0, label: 'MCQs', progress: p.bestQuiz ?? 0, total: 100, unit: p.bestQuiz === null ? 'not taken' : '% best score' },
  ]

  const heatRows = topics.slice(0, 12).map((t) => ({ key: t.name, label: t.name }))
  const heatCols = LEVELS.map((l) => ({ key: l, label: LEVEL_LABEL[l] }))

  return (
    <div data-section="overview">
      <PageBanner
        icon={LayoutDashboard}
        kicker={`${RESEARCH_LABEL[company.research_mode] || 'Research'}${(company.sources || []).length ? ` · ${company.sources.length} sources` : ''}`}
        title={`${session.role || profile.target_role || 'Your target role'} at ${session.company}`}
        description={`${session.years_experience} years of experience · ${profile.seniority || seniority(session.years_experience)} · created ${new Date(session.created_at).toLocaleDateString()}`}
        actions={
          <div className="ov-banner-ring">
            <ProgressRing value={p.readiness} size={116} stroke={11} label="Interview readiness">
              <span className="ring-value">{p.readiness}%</span>
              <span className="ring-label">Readiness</span>
            </ProgressRing>
            <p className="ov-ring-note">{READINESS_NOTE}</p>
          </div>
        }
      >
        <div className="row wrap" style={{ marginTop: 16 }}>
          {!active && (
            <button className="btn btn-sm" onClick={regenerate}>
              <RefreshCw size={15} /> Regenerate
            </button>
          )}
          <a className="btn btn-sm" href={api.exportUrl(session.id)} download>
            <Download size={15} /> Export
          </a>
          <span className="subtle ov-note-inline">{READINESS_NOTE}</span>
        </div>
      </PageBanner>

      {warnings.map((w) => (
        <div key={w} className="banner-note warn" style={{ marginBottom: 12 }}>
          <Info size={18} />
          <span>{w}</span>
        </div>
      ))}

      <motion.div className="kpi-row" variants={stagger(0.07)} initial="hidden" animate="show">
        <motion.div variants={fadeUp}>
          <StatTile label="Interview questions" value={counts.questions ?? 0} icon={MessageCircleQuestion} tone="overview" sub={`${counts.theory ?? 0} theory · ${counts.practical ?? 0} practical · ${counts.scenario ?? 0} scenario · ${counts.quiz ?? 0} MCQs`} />
        </motion.div>
        <motion.div variants={fadeUp}>
          <StatTile label="Topics planned" value={topics.length} icon={Layers} tone="revision" sub={`${counts.revision ?? 0} crash-revision notes`} />
        </motion.div>
        <motion.div variants={fadeUp}>
          <StatTile label="Hot questions" value={counts.hot ?? 0} icon={Flame} tone="hot" sub={aiMode ? 'Reported or frequently asked' : 'Classic, frequently asked'} />
        </motion.div>
        <motion.div variants={fadeUp}>
          <StatTile label="Mastered" value={p.mastered} icon={BadgeCheck} tone="ok" sub={`of ${p.interviewTotal} interview questions`}>
            <div style={{ marginTop: 10 }}>
              <Meter value={p.mastered} max={Math.max(1, p.interviewTotal)} label="Share of interview questions mastered" />
            </div>
          </StatTile>
        </motion.div>
      </motion.div>

      <div className="ov-grid">
        <motion.section className="card pitch-card c8" {...reveal}>
          <CardTitle
            icon={Quote}
            title="“Tell me about yourself”"
            sub="Your 60-90 second opener, built from your resume and this JD."
            right={
              profile.elevator_pitch && (
                <button className="btn btn-sm no-print" onClick={copyPitch}>
                  <Copy size={15} /> Copy
                </button>
              )
            }
          />
          <p className="pitch">
            <Quote size={22} className="pitch-quote" aria-hidden="true" />
            {profile.elevator_pitch || 'Not available.'}
          </p>
          {profile.summary && <p className="muted" style={{ margin: '14px 0 0', fontSize: 14 }}>{profile.summary}</p>}
        </motion.section>

        <motion.section className="card c4" {...reveal}>
          <CardTitle icon={UserRound} title="Skills match" />
          <div className="match-top">
            <ProgressRing value={matchPct} size={74} stroke={8} label="Share of JD skills found on your resume">
              <span style={{ fontWeight: 750, fontSize: 17 }}>{matchPct}%</span>
            </ProgressRing>
            <div>
              <strong>
                {matched.length} of {matched.length + missing.length} JD skills
              </strong>
              <span className="subtle">appear on your resume</span>
            </div>
          </div>
          {matched.length > 0 && (
            <>
              <span className="sub-label">You match</span>
              <div className="chips">
                {matched.map((s) => (
                  <span key={s} className="chip chip-ok">
                    <CircleCheck size={12} /> {s}
                  </span>
                ))}
              </div>
            </>
          )}
          {missing.length > 0 && (
            <>
              <span className="sub-label">Brush up on</span>
              <div className="chips">
                {missing.map((s) => (
                  <span key={s} className="chip chip-warn">
                    <TriangleAlert size={12} /> {s}
                  </span>
                ))}
              </div>
            </>
          )}
        </motion.section>

        <motion.section className="card c12" {...reveal}>
          <CardTitle icon={Layers} title="Your prep kit" sub={`${counts.questions ?? 0} practice questions, shared across four question dashboards.`} />
          <StackedBar ariaLabel="Kit composition" segments={COMPOSITION.map((c) => ({ ...c, value: counts[c.key] ?? 0 }))} unit=" questions" />
          <div className="dash-tiles">
            {dashTiles.map((t) => {
              const meta = SECTIONS.find((s) => s.key === t.key)
              const Icon = meta.icon
              return (
                <Link key={t.key} to={`${base}/${meta.path}`} className="dash-tile" data-section={t.key}>
                  <span className="dt-top">
                    <span className="dt-icon">
                      <Icon size={18} />
                    </span>
                    <ArrowRight size={17} className="dt-arrow" />
                  </span>
                  <span>
                    <strong>{t.count}</strong> <span className="dt-label">{t.label}</span>
                  </span>
                  <Meter className="thin" value={t.progress} max={Math.max(1, t.total)} label={`${meta.label} progress`} />
                  <span className="subtle" style={{ fontSize: 12 }}>
                    {t.key === 'quiz' ? (p.bestQuiz === null ? 'Quiz not taken yet' : `${p.bestQuiz}% best score`) : `${t.progress}/${t.total} ${t.unit}`}
                  </span>
                </Link>
              )
            })}
          </div>
        </motion.section>

        <motion.section className="card sw-card c6" {...reveal}>
          <div className="sw-head good">
            <CircleCheck size={18} /> Strengths to lean on
          </div>
          <div className="sw-body">
            <Bullets items={profile.strengths} icon={CircleCheck} className="icon-ok" />
          </div>
        </motion.section>
        <motion.section className="card sw-card c6" {...reveal}>
          <div className="sw-head gap">
            <TriangleAlert size={18} /> Gaps to prepare for
          </div>
          <div className="sw-body">
            <Bullets items={profile.gaps} icon={TriangleAlert} className="icon-warn" />
          </div>
        </motion.section>

        <motion.section className="card c12" {...reveal}>
          <CardTitle icon={Route} title={`Interview journey at ${company.name || session.company}`} sub={company.overview} />
          <div className="journey">
            {(company.interview_rounds || []).map((r, i, all) => (
              <div className="j-step" key={i}>
                <div className="j-node">
                  <span className="j-dot">{i + 1}</span>
                  {i < all.length - 1 && <span className="j-line" />}
                </div>
                <div className="j-card">
                  <strong>{r.name}</strong>
                  {r.format && <span className="fmt">{r.format}</span>}
                  {r.what_they_test && <p>{r.what_they_test}</p>}
                  {r.tips && (
                    <div className="j-tip">
                      <Lightbulb size={14} />
                      <span>{r.tips}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        <motion.section className="card c7" {...reveal}>
          <CardTitle icon={Layers} title="Topic priority" sub="Relative likelihood of each topic coming up. Select one to open its revision notes." />
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
            onSelect={(item) => navigate(`${base}/revision?topic=${encodeURIComponent(item.label)}`)}
          />
        </motion.section>

        <motion.section className="card c5" {...reveal}>
          <CardTitle icon={Grid3x3} title="Question coverage" sub="Questions per topic and level, across all four banks. Select a cell to practise it." />
          <Heatmap
            caption="Number of questions per topic and level"
            rows={heatRows}
            cols={heatCols}
            cell={(row, col) => {
              const data = coverage[`${row}|${col}`] || { value: 0, bySection: {} }
              return {
                value: data.value,
                lines: [Object.entries(data.bySection).map(([s, n]) => `${SECTION_NOUN[s]} ${n}`).join(' · ')],
              }
            }}
            onSelect={(row, col) => navigate(`${base}/theory?topic=${encodeURIComponent(row.key)}&level=${col.key}`)}
          />
        </motion.section>

        <motion.section className="card c6" {...reveal}>
          <CardTitle icon={Building2} title="What they look for" />
          {company.hiring_focus && <p style={{ fontSize: 14, marginTop: -4 }}>{company.hiring_focus}</p>}
          {(company.focus_areas || []).length > 0 && (
            <div className="chips" style={{ marginBottom: 14 }}>
              {company.focus_areas.map((f) => (
                <span key={f} className="chip chip-brand">
                  {f}
                </span>
              ))}
            </div>
          )}
          {(company.culture_values || []).length > 0 && (
            <>
              <span className="sub-label">Culture & values</span>
              <Bullets items={company.culture_values} icon={BadgeCheck} className="icon-brand" />
            </>
          )}
          {(company.insider_tips || []).length > 0 && (
            <>
              <span className="sub-label" style={{ marginTop: 14 }}>
                Insider tips
              </span>
              <Bullets items={company.insider_tips} icon={Lightbulb} className="icon-brand" />
            </>
          )}
        </motion.section>

        <motion.section className="card c6" {...reveal}>
          <CardTitle icon={Search} title="Resume deep-dive" sub="Interviewers will probe these. Have numbers and trade-offs ready." />
          {(profile.resume_probes || []).length === 0 && <p className="subtle">No specific probes identified.</p>}
          {(profile.resume_probes || []).map((probe, i) => (
            <div key={i} className={`probe ${openProbe === i ? 'open' : ''}`}>
              <button className="probe-q" onClick={() => setOpenProbe(openProbe === i ? -1 : i)} aria-expanded={openProbe === i}>
                <span className="title-icon brand" style={{ width: 26, height: 26, borderRadius: 8 }}>
                  <Search size={14} />
                </span>
                <span>{probe.item}</span>
                <ChevronDown size={17} className="chev" />
              </button>
              <AnimatePresence initial={false}>
                {openProbe === i && (
                  <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.28, ease: EASE }} style={{ overflow: 'hidden' }}>
                    <div className="probe-a">
                      <ul>
                        {(probe.likely_questions || []).map((q, j) => (
                          <li key={j}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </motion.section>

        {reported.length > 0 && (
          <motion.section className="card c6" {...reveal}>
            <CardTitle icon={Flame} tone="hot" title="Questions candidates reported" sub="From the research. Practise these first." />
            <ol className="rq-list">
              {reported.map((q, i) => (
                <li key={i}>
                  <span>
                    {q.question}
                    {(q.round || q.source) && (
                      <span className="subtle" style={{ display: 'block' }}>
                        {[q.round, q.source].filter(Boolean).join(' · ')}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ol>
          </motion.section>
        )}

        <motion.section className={`card ${reported.length ? 'c6' : 'c12'}`} {...reveal}>
          <CardTitle icon={MessageCircleQuestion} title="Questions to ask them" sub="End every round with one of these." />
          <div className="ask-grid">
            {(company.questions_to_ask_them || []).map((q, i) => (
              <div className="ask-card" key={i}>
                <MessageCircleQuestion size={16} />
                <span>{q}</span>
              </div>
            ))}
          </div>
        </motion.section>

        {(result.study_plan || []).length > 0 && (
          <motion.section className="card c12" {...reveal}>
            <CardTitle icon={CalendarClock} title="Your study plan" sub="A suggested order to work through the kit." />
            <ol className="plan-timeline">
              {result.study_plan.map((block, i) => (
                <li className="plan-step" key={i}>
                  <span className="plan-dot" aria-hidden="true">
                    {i + 1}
                  </span>
                  <div className="plan-main">
                    <h4>{block.title}</h4>
                    {block.focus && <p className="focus">{block.focus}</p>}
                  </div>
                  {(block.tasks || []).length > 0 && (
                    <ul className="plan-tasks">
                      {block.tasks.map((t, j) => (
                        <li key={j}>
                          <CircleCheck size={15} aria-hidden="true" />
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ol>
          </motion.section>
        )}

        <motion.section className="card c12" {...reveal}>
          <div className="collapse-head">
            <h3 className="card-title">
              <span className="title-icon" aria-hidden="true">
                <ScrollText size={17} />
              </span>
              Research report & sources
            </h3>
            <button className="btn btn-sm no-print" onClick={() => setShowReport((v) => !v)} aria-expanded={showReport}>
              {showReport ? 'Hide report' : 'Show full report'}
              <ChevronDown size={15} style={{ transform: showReport ? 'rotate(180deg)' : 'none', transition: 'transform .3s' }} />
            </button>
          </div>
          <AnimatePresence initial={false}>
            {showReport && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.35, ease: EASE }} style={{ overflow: 'hidden' }}>
                <div style={{ paddingTop: 16 }}>
                  <Markdown>{company.research_md}</Markdown>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          {(company.sources || []).length > 0 ? (
            <ul className="list-clean" style={{ marginTop: 14 }}>
              {company.sources.map((s) => (
                <li key={s.url}>
                  <ExternalLink size={15} className="icon-brand" />
                  <a href={s.url} target="_blank" rel="noreferrer noopener">
                    {s.title || s.url}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="subtle" style={{ margin: '12px 0 0' }}>
              <Globe size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 6 }} />
              No web sources for this kit{aiMode ? '.' : ': demo mode does not browse the web.'}
            </p>
          )}
        </motion.section>

        {(session.progress?.logs || []).length > 0 && (
          <motion.section className="card c12 no-print" {...reveal}>
            <div className="collapse-head">
              <h3 className="card-title">
                <span className="title-icon" aria-hidden="true">
                  <Bot size={17} />
                </span>
                How the agent built this kit
              </h3>
              <button className="btn btn-sm" onClick={() => setShowLog((v) => !v)} aria-expanded={showLog}>
                {showLog ? 'Hide activity' : `Show activity (${session.progress.logs.length} steps)`}
                <ChevronDown size={15} style={{ transform: showLog ? 'rotate(180deg)' : 'none', transition: 'transform .3s' }} />
              </button>
            </div>
            <AnimatePresence initial={false}>
              {showLog && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.35, ease: EASE }} style={{ overflow: 'hidden' }}>
                  <div style={{ paddingTop: 16 }}>
                    <TerminalLog logs={session.progress.logs} sources={session.progress.sources || []} title="Agent activity" maxHeight={420} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        )}
      </div>
    </div>
  )
}
