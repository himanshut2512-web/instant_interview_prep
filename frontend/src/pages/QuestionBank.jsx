import { useMemo, useState } from 'react'
import { ChevronsDownUp, ChevronsUpDown, MessagesSquare, SearchX, WandSparkles } from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import QuestionCard from '../components/QuestionCard.jsx'
import FilterBar, { applyFilters, levelCounts } from '../components/FilterBar.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'

const META = {
  theory: {
    title: 'Theoretical questions',
    blurb: 'Concepts interviewers check, level by level - each with a model answer, the key points they listen for and how to deliver it.',
  },
  practical: {
    title: 'Practical questions',
    blurb: 'Hands-on coding, SQL and problem-solving exercises with complete solutions, complexity and how to talk through them live.',
  },
  scenario: {
    title: 'Scenario-based questions',
    blurb: 'Real on-the-job situations with a step-by-step approach to tackle them in the interview and a strong model answer.',
  },
}

const EMPTY_FILTERS = { level: 'all', hot: false, topic: '', status: '', q: '' }

export default function QuestionBank({ section }) {
  const { session, aiMode, setItemStatus, evaluate, generateMore } = useWorkspace()
  const { notify } = useApp()
  const items = useMemo(() => session.result?.[section] || [], [session.result, section])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [open, setOpen] = useState(() => new Set())
  const [practiceMode, setPracticeMode] = useState(false)
  const [dialog, setDialog] = useState(false)
  const meta = META[section]

  const userItems = session.user_state?.items || {}
  const evaluations = session.user_state?.evaluations || {}
  const topics = useMemo(() => [...new Set(items.map((i) => i.topic))].sort(), [items])
  const counts = useMemo(() => levelCounts(items), [items])
  const visible = useMemo(() => applyFilters(items, filters, userItems), [items, filters, userItems])
  const mastered = items.filter((i) => userItems[i.id] === 'mastered').length
  const planTopics = (session.result?.topics || []).map((t) => t.name)

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
      setOpen(new Set([res.added[0].id]))
      setTimeout(() => document.getElementById(res.added[0].id)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 150)
    } else {
      notify(res.message || 'No new questions found for those filters.', 'error')
    }
  }

  if (!items.length) {
    return (
      <div className="card empty">
        <MessagesSquare size={28} />
        <p>The agent is still writing these questions - they will appear here shortly.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="section-head">
        <div>
          <h1>{meta.title}</h1>
          <p>{meta.blurb}</p>
          <p className="subtle" style={{ marginTop: 6 }}>
            {items.length} questions · {counts.hot} hot · {mastered} mastered
          </p>
        </div>
        <div className="row wrap no-print">
          <button className="btn" onClick={() => setOpen(allOpen ? new Set() : new Set(visible.map((i) => i.id)))}>
            {allOpen ? <ChevronsDownUp size={16} /> : <ChevronsUpDown size={16} />}
            {allOpen ? 'Collapse all' : 'Expand all'}
          </button>
          <button className="btn btn-primary" onClick={() => setDialog(true)}>
            <WandSparkles size={16} /> Generate more
          </button>
        </div>
      </div>

      <FilterBar
        filters={filters}
        setFilters={setFilters}
        counts={counts}
        topics={topics}
        practiceMode={practiceMode}
        setPracticeMode={setPracticeMode}
      />

      {visible.length === 0 ? (
        <div className="card empty">
          <SearchX size={28} />
          <p>No questions match these filters.</p>
          <button className="btn" onClick={() => setFilters(EMPTY_FILTERS)}>
            Reset filters
          </button>
        </div>
      ) : (
        <div className="qlist">
          {visible.map((item, index) => (
            <QuestionCard
              key={item.id}
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
          ))}
        </div>
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
