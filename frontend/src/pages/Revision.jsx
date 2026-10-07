import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, useScroll, useSpring } from 'motion/react'
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CircleCheck,
  CircleX,
  Code2,
  FlipHorizontal2,
  Layers,
  Lightbulb,
  ListChecks,
  MessageCircleQuestion,
  Plus,
  Search,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import { useScrollSpy } from '../hooks/useScrollSpy.js'
import { useOverflowFade } from '../hooks/useOverflowFade.js'
import { EASE, fadeUp, stagger } from '../lib/motion.js'
import Markdown, { codeFence } from '../components/Markdown.jsx'
import { PriorityTag } from '../components/Badges.jsx'
import { ProgressRing } from '../components/Viz.jsx'
import { SegmentedTabs } from '../components/Tabs.jsx'
import { EmptyState, PageBanner } from '../components/UI.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'

function Flashcard({ term, explanation, flipped, onFlip }) {
  return (
    <button type="button" className={`flash ${flipped ? 'flipped' : ''}`} onClick={onFlip} aria-pressed={flipped} aria-label={`${term}. ${flipped ? explanation : 'Select to reveal the explanation.'}`}>
      <span className="flash-inner">
        <span className="flash-face flash-front">
          {term}
          <span className="flash-hint">Tap to flip</span>
        </span>
        <span className="flash-face flash-back">
          <strong>{term}</strong>
          {explanation}
        </span>
      </span>
    </button>
  )
}

export default function Revision() {
  const { session, aiMode, setTopicRevised, generateMore } = useWorkspace()
  const { notify } = useApp()
  const [params, setParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [dialog, setDialog] = useState(false)
  const [conceptView, setConceptView] = useState('cards')
  const [flipped, setFlipped] = useState(() => new Set())
  const articleRef = useRef(null)
  const railRef = useRef(null)
  useOverflowFade(railRef)
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

  const index = selected ? notes.indexOf(selected) : -1
  const previous = index > 0 ? notes[index - 1] : null
  const next = index >= 0 && index < notes.length - 1 ? notes[index + 1] : null
  const doneCount = notes.filter((n) => revised[n.id]).length
  const visible = notes.filter((n) => n.topic.toLowerCase().includes(query.trim().toLowerCase()))

  const { scrollYProgress } = useScroll({ target: articleRef, offset: ['start start', 'end end'] })
  const progressX = useSpring(scrollYProgress, { stiffness: 140, damping: 28, restDelta: 0.001 })

  const sections = selected
    ? [
        { id: 'rv-concepts', label: 'Key concepts', show: (selected.key_concepts || []).length > 0 },
        { id: 'rv-explain', label: 'Explanation', show: Boolean(selected.explanation_md) },
        { id: 'rv-example', label: 'Example', show: Boolean(selected.code_example?.code) },
        { id: 'rv-traps', label: 'Pitfalls & tips', show: (selected.pitfalls || []).length + (selected.interview_tips || []).length > 0 },
        { id: 'rv-cheats', label: 'Cheat sheet', show: (selected.cheat_sheet || []).length > 0 },
        { id: 'rv-questions', label: 'Likely questions', show: (selected.likely_questions || []).length > 0 },
      ].filter((s) => s.show)
    : []
  const activeSection = useScrollSpy(
    sections.map((s) => s.id),
    selected?.id,
  )

  useEffect(() => {
    setFlipped(new Set())
  }, [selected?.id])

  // Keep the open topic visible in the rail (a sideways strip on small screens):
  // scroll the rail itself, never the page, and only as far as needed.
  useEffect(() => {
    const rail = railRef.current
    const item = rail?.querySelector('.rev-topic.on')
    if (!item) return
    const box = rail.getBoundingClientRect()
    const at = item.getBoundingClientRect()
    const gap = 12
    const left = at.left < box.left ? at.left - box.left - gap : at.right > box.right ? at.right - box.right + gap : 0
    const top = at.top < box.top ? at.top - box.top - gap : at.bottom > box.bottom ? at.bottom - box.bottom + gap : 0
    if (left || top) rail.scrollBy({ left, top, behavior: 'smooth' })
  }, [selected?.id])

  const open = (note) => {
    setParams({ note: note.id })
    articleRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const markAndNext = () => {
    if (!selected) return
    if (!revised[selected.id]) setTopicRevised(selected.id, true)
    if (next) open(next)
    else notify('That was the last topic. Great revision session!')
  }

  const add = async (body) => {
    const res = await generateMore(body)
    if (res.added.length) {
      notify(`Added notes for ${res.added.map((n) => n.topic).join(', ')}.`)
      setParams({ note: res.added[0].id })
    } else {
      notify(res.message || 'Nothing new to add.', 'error')
    }
  }

  const toggleFlip = (i) =>
    setFlipped((prev) => {
      const nextSet = new Set(prev)
      if (nextSet.has(i)) nextSet.delete(i)
      else nextSet.add(i)
      return nextSet
    })

  if (!notes.length) {
    return (
      <div data-section="revision">
        <EmptyState icon={BookOpen} title="Writing your revision notes…" text="Crash-revision notes are being written. They will appear here in a moment." />
      </div>
    )
  }

  const concepts = selected?.key_concepts || []
  const allFlipped = concepts.length > 0 && flipped.size === concepts.length

  return (
    <div data-section="revision">
      <PageBanner
        icon={BookOpen}
        kicker="Dashboard 1 · Crash revision"
        title="Crash revision"
        description="Every topic likely to come up, explained for last-minute revision: concepts, examples, pitfalls and a cheat sheet."
        stats={[
          { label: 'topics', value: notes.length },
          { label: 'revised', value: doneCount },
          { label: 'key concepts', value: notes.reduce((sum, n) => sum + (n.key_concepts || []).length, 0) },
        ]}
        actions={
          <button className="btn btn-sec" onClick={() => setDialog(true)}>
            <Plus size={16} /> Add a topic
          </button>
        }
      />

      <div className="rev-layout">
        <aside ref={railRef} className="rev-rail" aria-label="Revision topics">
          <div className="rev-progress">
            <div className="row" style={{ marginBottom: 0 }}>
              <ProgressRing value={doneCount} max={notes.length} size={54} stroke={6} label="Topics revised">
                <span style={{ fontWeight: 750, fontSize: 12.5 }}>{Math.round((100 * doneCount) / notes.length)}%</span>
              </ProgressRing>
              <span style={{ textAlign: 'right' }}>
                <strong style={{ display: 'block', fontSize: 15 }}>
                  {doneCount}/{notes.length}
                </strong>
                <span className="subtle">topics revised</span>
              </span>
            </div>
          </div>
          <div className="input-wrap sm">
            <Search size={15} />
            <input className="input" placeholder="Filter topics…" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Filter topics" />
          </div>
          {visible.map((n) => {
            const isOn = selected?.id === n.id
            const isDone = Boolean(revised[n.id])
            return (
              <button key={n.id} className={`rev-topic ${isOn ? 'on' : ''} ${isDone ? 'revised' : ''}`} onClick={() => open(n)} aria-current={isOn}>
                <span className="rt-num">{isDone ? <CircleCheck size={15} /> : notes.indexOf(n) + 1}</span>
                <span style={{ minWidth: 0 }}>
                  <strong>{n.topic}</strong>
                  <PriorityTag priority={n.priority} />
                </span>
              </button>
            )
          })}
        </aside>

        {selected && (
          <article ref={articleRef} className="card rev-article">
            <div className="read-progress" aria-hidden="true">
              <motion.span style={{ scaleX: progressX }} />
            </div>
            <motion.div key={selected.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, ease: EASE }}>
            <header className="rev-hero">
              <div className="spread">
                <div className="row wrap">
                  <span className="chip chip-sec">
                    Topic {index + 1} of {notes.length}
                  </span>
                  <PriorityTag priority={selected.priority} />
                </div>
                <button
                  className={`btn btn-sm ${revised[selected.id] ? 'is-on' : ''}`}
                  aria-pressed={Boolean(revised[selected.id])}
                  onClick={() => setTopicRevised(selected.id, !revised[selected.id])}
                >
                  <CircleCheck size={15} /> {revised[selected.id] ? 'Revised' : 'Mark as revised'}
                </button>
              </div>
              <h2 style={{ marginTop: 14 }}>{selected.topic}</h2>
              {selected.summary && <p className="summary">{selected.summary}</p>}
              {selected.why_it_matters && (
                <div className="callout" style={{ marginTop: 16 }}>
                  <Target size={18} />
                  <div>
                    <strong>Why it matters here: </strong>
                    {selected.why_it_matters}
                  </div>
                </div>
              )}
            </header>

            <div className="rev-body">
              {concepts.length > 0 && (
                <section className="rev-section" id="rv-concepts">
                  <div className="spread" style={{ marginBottom: 12 }}>
                    <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 10 }}>
                      <Zap size={18} className="icon-sec" /> Key concepts
                    </h3>
                    <div className="row wrap">
                      {conceptView === 'flash' && (
                        <button className="btn btn-sm btn-ghost" onClick={() => setFlipped(allFlipped ? new Set() : new Set(concepts.map((_, i) => i)))}>
                          <FlipHorizontal2 size={15} /> {allFlipped ? 'Hide all' : 'Flip all'}
                        </button>
                      )}
                      <SegmentedTabs
                        ariaLabel="Concept view"
                        value={conceptView}
                        onChange={setConceptView}
                        options={[
                          { value: 'cards', label: 'Cards', icon: <Layers size={14} /> },
                          { value: 'flash', label: 'Flashcards', icon: <Sparkles size={14} /> },
                        ]}
                      />
                    </div>
                  </div>
                  {conceptView === 'cards' ? (
                    <motion.dl className="concepts" variants={stagger(0.04)} initial="hidden" animate="show">
                      {concepts.map((c, i) => (
                        <motion.div className="concept" key={i} variants={fadeUp}>
                          <dt>{c.term}</dt>
                          <dd>{c.explanation}</dd>
                        </motion.div>
                      ))}
                    </motion.dl>
                  ) : (
                    <motion.div className="concepts" variants={stagger(0.04)} initial="hidden" animate="show">
                      {concepts.map((c, i) => (
                        <motion.div key={i} variants={fadeUp}>
                          <Flashcard term={c.term} explanation={c.explanation} flipped={flipped.has(i)} onFlip={() => toggleFlip(i)} />
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                  {conceptView === 'flash' && (
                    <p className="subtle" style={{ margin: '10px 0 0' }}>
                      {flipped.size} of {concepts.length} flipped. Say the explanation out loud before you flip.
                    </p>
                  )}
                </section>
              )}

              {selected.explanation_md && (
                <section className="rev-section" id="rv-explain">
                  <h3>
                    <BookOpen size={18} className="icon-sec" /> Explanation
                  </h3>
                  <Markdown>{selected.explanation_md}</Markdown>
                </section>
              )}

              {selected.code_example?.code && (
                <section className="rev-section" id="rv-example">
                  <h3>
                    <Code2 size={18} className="icon-sec" /> Example
                  </h3>
                  <Markdown>{codeFence(selected.code_example)}</Markdown>
                </section>
              )}

              {(selected.pitfalls || []).length + (selected.interview_tips || []).length > 0 && (
                <section className="rev-section" id="rv-traps">
                  <div className="duo">
                    {(selected.pitfalls || []).length > 0 && (
                      <div className="duo-card pit">
                        <h4>
                          <CircleX size={17} className="icon-bad" /> Common pitfalls
                        </h4>
                        <ul className="list-clean">
                          {selected.pitfalls.map((t, i) => (
                            <li key={i}>
                              <CircleX size={15} className="icon-bad" />
                              <span>{t}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {(selected.interview_tips || []).length > 0 && (
                      <div className="duo-card tip">
                        <h4>
                          <Lightbulb size={17} className="icon-sec" /> How it's tested
                        </h4>
                        <ul className="list-clean">
                          {selected.interview_tips.map((t, i) => (
                            <li key={i}>
                              <Lightbulb size={15} className="icon-sec" />
                              <span>{t}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {(selected.cheat_sheet || []).length > 0 && (
                <section className="rev-section" id="rv-cheats">
                  <h3>
                    <ListChecks size={18} className="icon-sec" /> Cheat sheet: memorise these
                  </h3>
                  <ul className="cheats">
                    {selected.cheat_sheet.map((c, i) => (
                      <li key={i}>
                        <Zap size={15} />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {(selected.likely_questions || []).length > 0 && (
                <section className="rev-section" id="rv-questions">
                  <h3>
                    <MessageCircleQuestion size={18} className="icon-sec" /> Likely questions on this topic
                  </h3>
                  <ul className="lq-list">
                    {selected.likely_questions.map((q, i) => (
                      <li key={i}>
                        <MessageCircleQuestion size={16} />
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
            </motion.div>

            <nav className="rev-nav no-print" aria-label="Topic navigation">
              <button className="rev-nav-btn" disabled={!previous} onClick={() => previous && open(previous)}>
                <span>
                  <ArrowLeft size={13} /> Previous topic
                </span>
                <strong>{previous ? previous.topic : 'This is the first topic'}</strong>
              </button>
              <button className="rev-nav-btn next" onClick={markAndNext}>
                <span>
                  {revised[selected.id] ? 'Next topic' : 'Mark revised & continue'} <ArrowRight size={13} />
                </span>
                <strong>{next ? next.topic : 'Finish revision'}</strong>
              </button>
            </nav>
          </article>
        )}

        {sections.length > 1 && (
          <nav className="rev-toc no-print" aria-label="On this page">
            <span className="toc-title">On this page</span>
            {sections.map((s) => (
              <a key={s.id} href={`#${s.id}`} className={`toc-link ${activeSection === s.id ? 'on' : ''}`}>
                {s.label}
              </a>
            ))}
          </nav>
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
