import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'motion/react'
import { ChevronsDownUp, ChevronsUpDown, Code2, Layers, List, MessagesSquare, Puzzle, SearchX, WandSparkles } from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import { fadeUp, stagger } from '../lib/motion.js'
import { pct } from '../lib/format.js'
import QuestionCard from '../components/QuestionCard.jsx'
import DrillView from '../components/DrillView.jsx'
import FilterBar, { applyFilters, levelCounts } from '../components/FilterBar.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'
import { SegmentedTabs } from '../components/Tabs.jsx'
import { EmptyState, PageBanner } from '../components/UI.jsx'

const META = {
  theory: {
    icon: MessagesSquare,
    kicker: 'Dashboard 2 · Theoretical',
    title: 'Theoretical questions',
    blurb: 'Concepts interviewers check, level by level. Each has a model answer, the points they listen for and how to deliver it.',
  },
  practical: {
    icon: Code2,
    kicker: 'Dashboard 3 · Practical',
    title: 'Practical questions',
    blurb: 'Hands-on coding, SQL and problem-solving exercises with complete solutions, complexity and how to talk them through live.',
  },
  scenario: {
    icon: Puzzle,
    kicker: 'Dashboard 4 · Scenario-based',
    title: 'Scenario-based questions',
    blurb: 'Real on-the-job situations with a step-by-step game plan for the interview and a strong spoken answer.',
  },
}

const EMPTY_FILTERS = { level: 'all', hot: false, topic: '', status: '', q: '' }

function SkeletonList() {
  return (
    <div className="qlist" aria-busy="true" aria-label="Loading questions">
      {[0, 1, 2, 3].map((i) => (
        <div className="skel-card" key={i}>
          <div className="skeleton" style={{ width: 36, height: 36, borderRadius: 11 }} />
          <div>
            <div className="skeleton skel-line" style={{ width: `${70 - i * 8}%`, height: 14 }} />
            <div className="row" style={{ marginTop: 12 }}>
              <div className="skeleton" style={{ width: 90, height: 22 }} />
              <div className="skeleton" style={{ width: 70, height: 22 }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function QuestionBank({ section }) {
  const { session, aiMode, setItemStatus, evaluate, generateMore } = useWorkspace()
  const { notify } = useApp()
  const [params] = useSearchParams()
  const items = useMemo(() => session.result?.[section] || [], [session.result, section])
  const [filters, setFilters] = useState(() => ({
    ...EMPTY_FILTERS,
    level: ['beginner', 'intermediate', 'advanced'].includes(params.get('level')) ? params.get('level') : 'all',
    topic: params.get('topic') || '',
    hot: params.get('hot') === '1',
  }))
  const [open, setOpen] = useState(() => new Set())
  const [practiceMode, setPracticeMode] = useState(false)
  const [view, setView] = useState('list')
  const [dialog, setDialog] = useState(false)
  const meta = META[section]

  const userItems = session.user_state?.items || {}
  const evaluations = session.user_state?.evaluations || {}
  const topics = useMemo(() => [...new Set(items.map((i) => i.topic))].sort(), [items])
  const counts = useMemo(() => levelCounts(items), [items])
  const visible = useMemo(() => applyFilters(items, filters, userItems), [items, filters, userItems])
  const mastered = items.filter((i) => userItems[i.id] === 'mastered').length
  const planTopics = (session.result?.topics || []).map((t) => t.name)
  const active = session.status === 'running' || session.status === 'queued'
  const drillKey = `${section}|${filters.level}|${filters.hot}|${filters.topic}|${filters.status}|${filters.q}|${items.length}`

  const toggle = (id) =>
    setOpen((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  const allOpen = visible.length > 0 && visible.every((i) => open.has(i.id))

  const onGenerate = async (body) => {
    const res = await generateMore(body)
    if (res.added.length) {
      notify(`Added ${res.added.length} new ${meta.title.toLowerCase()}.`)
      setFilters(EMPTY_FILTERS)
      setView('list')
      setOpen(new Set([res.added[0].id]))
      setTimeout(() => document.getElementById(res.added[0].id)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 250)
    } else {
      notify(res.message || 'No new questions found for those settings.', 'error')
    }
  }

  return (
    <div data-section={section}>
      <PageBanner
        icon={meta.icon}
        kicker={meta.kicker}
        title={meta.title}
        description={meta.blurb}
        stats={[
          { label: 'questions', value: items.length },
          { label: 'hot', value: counts.hot },
          { label: 'mastered', value: `${pct(mastered, items.length)}%` },
        ]}
        actions={
          <>
            <SegmentedTabs
              ariaLabel="View"
              value={view}
              onChange={setView}
              options={[
                { value: 'list', label: 'List', icon: <List size={15} /> },
                { value: 'drill', label: 'Drill', icon: <Layers size={15} /> },
              ]}
            />
            <button className="btn btn-sec" onClick={() => setDialog(true)} disabled={!items.length}>
              <WandSparkles size={16} /> Generate more
            </button>
          </>
        }
      />

      {items.length === 0 ? (
        active ? (
          <>
            <div className="banner-note" style={{ marginBottom: 14 }}>
              <meta.icon size={18} />
              <span>The agent is writing these questions. They will appear here as soon as the first batch is ready.</span>
            </div>
            <SkeletonList />
          </>
        ) : (
          <EmptyState icon={meta.icon} title="No questions yet" text="This section has no questions. Use Regenerate on the overview to run the agent again." />
        )
      ) : (
        <>
          <FilterBar
            filters={filters}
            setFilters={setFilters}
            counts={counts}
            topics={topics}
            practiceMode={view === 'list' ? practiceMode : undefined}
            setPracticeMode={view === 'list' ? setPracticeMode : undefined}
          />

          {visible.length === 0 ? (
            <EmptyState
              icon={SearchX}
              title="No questions match these filters"
              text="Try another level or topic, or clear the search."
              action={
                <button className="btn" onClick={() => setFilters(EMPTY_FILTERS)}>
                  Reset filters
                </button>
              }
            />
          ) : view === 'drill' ? (
            <DrillView
              items={visible}
              allItems={items}
              resetKey={drillKey}
              section={section}
              userItems={userItems}
              evaluations={evaluations}
              onSetStatus={(id, value) => setItemStatus(id, value)}
            />
          ) : (
            <>
              <div className="spread" style={{ margin: '-4px 0 12px' }}>
                <span className="subtle">
                  Showing {visible.length} of {items.length}
                </span>
                <button className="btn btn-sm btn-ghost" onClick={() => setOpen(allOpen ? new Set() : new Set(visible.map((i) => i.id)))}>
                  {allOpen ? <ChevronsDownUp size={15} /> : <ChevronsUpDown size={15} />}
                  {allOpen ? 'Collapse all' : 'Expand all'}
                </button>
              </div>
              <motion.div className="qlist" variants={stagger(0.035)} initial="hidden" animate="show">
                {visible.map((item, index) => (
                  <motion.div key={item.id} variants={fadeUp}>
                    <QuestionCard
                      item={item}
                      index={index}
                      section={section}
                      status={userItems[item.id]}
                      evaluation={evaluations[item.id]}
                      open={open.has(item.id)}
                      onToggle={() => toggle(item.id)}
                      practiceMode={practiceMode}
                      aiMode={aiMode}
                      onSetStatus={(value) => setItemStatus(item.id, value)}
                      onEvaluate={(answer) => evaluate({ section, item_id: item.id, answer })}
                    />
                  </motion.div>
                ))}
              </motion.div>
            </>
          )}
        </>
      )}

      <GenerateMoreDialog
        key={section}
        open={dialog}
        onClose={() => setDialog(false)}
        section={section}
        topics={planTopics.length ? planTopics : topics}
        aiMode={aiMode}
        onSubmit={onGenerate}
      />
    </div>
  )
}
