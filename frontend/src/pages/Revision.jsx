import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  BookOpen,
  CircleCheck,
  CircleDashed,
  CircleX,
  Code2,
  Lightbulb,
  ListChecks,
  MessageCircleQuestion,
  Plus,
  Search,
  Target,
  Zap,
} from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import Markdown, { codeFence } from '../components/Markdown.jsx'
import { PriorityTag } from '../components/Badges.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'

function Block({ title, icon: Icon, children }) {
  return (
    <section className="qsection" style={{ marginTop: 22 }}>
      <h3 className="row" style={{ fontSize: '1rem' }}>
        <Icon size={17} className="icon-accent" />
        {title}
      </h3>
      {children}
    </section>
  )
}

export default function Revision() {
  const { session, aiMode, setTopicRevised, generateMore } = useWorkspace()
  const { notify } = useApp()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [dialog, setDialog] = useState(false)
  const notes = session.result?.revision || []
  const revised = session.user_state?.topics || {}
  const topicNames = (session.result?.topics || []).map((t) => t.name)

  const wanted = (params.get('topic') || '').toLowerCase()
  const selected = useMemo(() => {
    if (!notes.length) return null
    return (
      notes.find((n) => n.id === params.get('note')) ||
      notes.find((n) => wanted && (n.topic.toLowerCase() === wanted || n.topic.toLowerCase().includes(wanted) || wanted.includes(n.topic.toLowerCase()))) ||
      notes[0]
    )
  }, [notes, params, wanted])

  const visible = notes.filter((n) => n.topic.toLowerCase().includes(query.trim().toLowerCase()))
  const doneCount = notes.filter((n) => revised[n.id]).length

  const add = async (body) => {
    const res = await generateMore(body)
    if (res.added.length) {
      notify(`Added notes for ${res.added.map((n) => n.topic).join(', ')}.`)
      setParams({ note: res.added[0].id })
    } else {
      notify(res.message || 'Nothing new to add.', 'error')
    }
  }

  if (!notes.length) {
    return (
      <div className="card empty">
        <BookOpen size={28} />
        <p>Crash-revision notes are being written - they will appear here in a moment.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="section-head">
        <div>
          <h1>Crash revision</h1>
          <p>
            Every topic likely to come up, explained for last-minute revision. {doneCount}/{notes.length} topics revised.
          </p>
        </div>
        <button className="btn btn-primary no-print" onClick={() => setDialog(true)}>
          <Plus size={16} /> Add a topic
        </button>
      </div>

      <div className="rev-layout">
        <aside className="rev-topics" aria-label="Revision topics">
          <div className="search-box" style={{ flex: 'none' }}>
            <Search size={15} />
            <input className="input" placeholder="Filter topics…" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Filter topics" />
          </div>
          {visible.map((n) => (
            <button key={n.id} className={`rev-topic ${selected?.id === n.id ? 'on' : ''}`} onClick={() => setParams({ note: n.id })} aria-current={selected?.id === n.id}>
              <span>
                <strong>{n.topic}</strong>
                <PriorityTag priority={n.priority} />
              </span>
              {revised[n.id] ? <CircleCheck size={18} className="icon-good" aria-label="Revised" /> : <CircleDashed size={18} className="subtle" aria-label="Not revised yet" />}
            </button>
          ))}
        </aside>

        {selected && (
          <article className="card" style={{ padding: 24 }}>
            <div className="spread">
              <div>
                <h2 style={{ marginBottom: 4 }}>{selected.topic}</h2>
                <PriorityTag priority={selected.priority} />
              </div>
              <button
                className={`btn ${revised[selected.id] ? 'is-on' : ''}`}
                aria-pressed={Boolean(revised[selected.id])}
                onClick={() => setTopicRevised(selected.id, !revised[selected.id])}
              >
                <CircleCheck size={16} /> {revised[selected.id] ? 'Revised' : 'Mark as revised'}
              </button>
            </div>

            {selected.summary && <p style={{ fontSize: '1.02rem', marginTop: 14 }}>{selected.summary}</p>}
            {selected.why_it_matters && (
              <div className="tip-box">
                <Target size={17} />
                <div>
                  <strong>Why it matters here: </strong>
                  {selected.why_it_matters}
                </div>
              </div>
            )}

            {(selected.key_concepts || []).length > 0 && (
              <Block title="Key concepts" icon={Zap}>
                <dl className="concepts">
                  {selected.key_concepts.map((c, i) => (
                    <div className="concept" key={i}>
                      <dt>{c.term}</dt>
                      <dd>{c.explanation}</dd>
                    </div>
                  ))}
                </dl>
              </Block>
            )}

            {selected.explanation_md && (
              <Block title="Explanation" icon={BookOpen}>
                <Markdown>{selected.explanation_md}</Markdown>
              </Block>
            )}

            {selected.code_example?.code && (
              <Block title="Example" icon={Code2}>
                <Markdown>{codeFence(selected.code_example)}</Markdown>
              </Block>
            )}

            <div className="two-col">
              {(selected.pitfalls || []).length > 0 && (
                <Block title="Common pitfalls" icon={CircleX}>
                  <ul className="list-clean">
                    {selected.pitfalls.map((p, i) => (
                      <li key={i}>
                        <CircleX size={15} className="icon-warn" />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </Block>
              )}
              {(selected.interview_tips || []).length > 0 && (
                <Block title="How it's tested" icon={Lightbulb}>
                  <ul className="list-clean">
                    {selected.interview_tips.map((p, i) => (
                      <li key={i}>
                        <Lightbulb size={15} className="icon-accent" />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </Block>
              )}
            </div>

            {(selected.cheat_sheet || []).length > 0 && (
              <Block title="Cheat sheet - memorise these" icon={ListChecks}>
                <ul className="cheats">
                  {selected.cheat_sheet.map((c, i) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </Block>
            )}

            {(selected.likely_questions || []).length > 0 && (
              <Block title="Likely questions on this topic" icon={MessageCircleQuestion}>
                <ul className="list-clean">
                  {selected.likely_questions.map((q, i) => (
                    <li key={i}>
                      <MessageCircleQuestion size={15} className="icon-accent" />
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </Block>
            )}
          </article>
        )}
      </div>

      <GenerateMoreDialog
        open={dialog}
        onClose={() => setDialog(false)}
        section="revision"
        topics={topicNames.filter((t) => !notes.some((n) => n.topic.toLowerCase() === t.toLowerCase()))}
        aiMode={aiMode}
        onSubmit={add}
      />
    </div>
  )
}
