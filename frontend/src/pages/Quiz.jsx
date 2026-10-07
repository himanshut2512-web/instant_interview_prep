import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BookOpen,
  CircleCheck,
  CircleX,
  Flame,
  History,
  Lightbulb,
  ListChecks,
  Play,
  RotateCcw,
  Shuffle,
  Timer,
  Trophy,
  WandSparkles,
} from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import Markdown from '../components/Markdown.jsx'
import { HotBadge, LevelBadge, LEVEL_LABEL } from '../components/Badges.jsx'
import { BarList, Meter, Sparkline, StatTile } from '../components/Viz.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'

const KEYS = ['A', 'B', 'C', 'D', 'E', 'F']

function shuffle(list) {
  const out = [...list]
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

/** Shuffle question order and option order (remapping the correct answer). */
function prepare(pool, count) {
  return shuffle(pool)
    .slice(0, count)
    .map((q) => {
      const perm = shuffle(q.options.map((_, i) => i))
      return {
        ...q,
        options: perm.map((i) => q.options[i]),
        option_explanations: perm.map((i) => (q.option_explanations || [])[i] || ''),
        correct_index: perm.indexOf(q.correct_index),
      }
    })
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function Quiz() {
  const { session, aiMode, addQuizAttempt, generateMore } = useWorkspace()
  const { notify } = useApp()
  const all = useMemo(() => session.result?.quiz || [], [session.result])
  const attempts = session.quiz_attempts || []
  const topics = useMemo(() => [...new Set(all.map((q) => q.topic))].sort(), [all])

  const [config, setConfig] = useState({ count: 10, level: 'all', topic: '', hot: false })
  const [phase, setPhase] = useState('setup')
  const [questions, setQuestions] = useState([])
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState([])
  const [startedAt, setStartedAt] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [dialog, setDialog] = useState(false)

  const pool = useMemo(
    () =>
      all.filter(
        (q) =>
          (config.level === 'all' || q.level === config.level) &&
          (!config.topic || q.topic === config.topic) &&
          (!config.hot || q.hot),
      ),
    [all, config],
  )

  useEffect(() => {
    if (phase !== 'running') return undefined
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - startedAt) / 1000)), 1000)
    return () => clearInterval(timer)
  }, [phase, startedAt])

  const start = (set) => {
    const prepared = set ? prepare(set, set.length) : prepare(pool, config.count === 'all' ? pool.length : config.count)
    if (!prepared.length) return notify('No questions match these settings.', 'error')
    setQuestions(prepared)
    setAnswers([])
    setIndex(0)
    setStartedAt(Date.now())
    setElapsed(0)
    setPhase('running')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const current = questions[index]
  const answered = answers[index]

  const choose = useCallback(
    (optionIndex) => {
      if (!current || answers[index]) return
      const next = [...answers]
      next[index] = { id: current.id, selected: optionIndex, correct: optionIndex === current.correct_index }
      setAnswers(next)
    },
    [current, answers, index],
  )

  const finish = useCallback(
    async (finalAnswers) => {
      setElapsed(Math.round((Date.now() - startedAt) / 1000))
      setPhase('done')
      const correct = finalAnswers.filter((a) => a?.correct).length
      try {
        await addQuizAttempt({
          total: questions.length,
          correct,
          duration_sec: Math.round((Date.now() - startedAt) / 1000),
          filters: { level: config.level, topic: config.topic, hot: config.hot },
          answers: finalAnswers.map((a) => ({ id: a.id, selected: a.selected, correct: a.correct })),
        })
      } catch (e) {
        notify(`Score not saved: ${e.message}`, 'error')
      }
    },
    [addQuizAttempt, questions.length, startedAt, config, notify],
  )

  const next = useCallback(() => {
    if (!answers[index]) return
    if (index + 1 < questions.length) setIndex(index + 1)
    else finish(answers)
  }, [answers, index, questions.length, finish])

  useEffect(() => {
    if (phase !== 'running') return undefined
    const onKey = (e) => {
      if (e.target.closest('input, textarea, select')) return
      if (e.key === 'Enter' && e.target.closest('button')) return // the focused button handles Enter itself
      const key = e.key.toUpperCase()
      const pos = KEYS.indexOf(key)
      const num = Number(e.key) - 1
      if (pos >= 0 && pos < (current?.options.length || 0)) choose(pos)
      else if (num >= 0 && num < (current?.options.length || 0)) choose(num)
      else if (e.key === 'Enter') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, current, choose, next])

  const onGenerate = async (body) => {
    const res = await generateMore(body)
    if (res.added.length) notify(`Added ${res.added.length} fresh MCQs to the pool.`)
    else notify(res.message || 'No new MCQs found.', 'error')
  }

  if (!all.length) {
    return (
      <div className="card empty">
        <ListChecks size={28} />
        <p>The MCQ quiz is being generated - it will appear here shortly.</p>
      </div>
    )
  }

  const dialogEl = (
    <GenerateMoreDialog open={dialog} onClose={() => setDialog(false)} section="quiz" topics={topics} aiMode={aiMode} onSubmit={onGenerate} />
  )

  // ------------------------------------------------------------------ setup
  if (phase === 'setup') {
    const scores = attempts.map((a) => a.score_pct)
    const best = scores.length ? Math.max(...scores) : null
    const last = scores.length ? scores[scores.length - 1] : null
    return (
      <div>
        <div className="section-head">
          <div>
            <h1>MCQ quiz</h1>
            <p>Rapid self-test with instant explanations. Questions and options are shuffled every attempt.</p>
          </div>
          <button className="btn no-print" onClick={() => setDialog(true)}>
            <WandSparkles size={16} /> Generate fresh MCQs
          </button>
        </div>

        <div className="kpi-row" style={{ marginBottom: 18 }}>
          <StatTile label="MCQs available" value={all.length} sub={`${all.filter((q) => q.hot).length} hot`} icon={ListChecks} />
          <StatTile label="Attempts" value={attempts.length} sub={attempts.length ? `Last on ${new Date(attempts[attempts.length - 1].at).toLocaleDateString()}` : 'No attempts yet'} icon={History} />
          <StatTile label="Best score" value={best === null ? '-' : `${best}%`} sub="Across all attempts" icon={Trophy} />
          <StatTile label="Last score" value={last === null ? '-' : `${last}%`} sub={scores.length > 1 ? 'Score history' : 'Take a quiz to start a trend'} icon={RotateCcw}>
            <Sparkline values={scores.slice(-12)} />
          </StatTile>
        </div>

        <div className="card quiz-wrap" style={{ marginBottom: 18 }}>
          <div className="card-title">
            <Play size={18} /> Start a quiz
          </div>
          <div className="stack" style={{ gap: 14 }}>
            <div className="field">
              <span className="label">Number of questions</span>
              <div className="segmented" role="radiogroup" aria-label="Number of questions">
                {[5, 10, 20, 'all'].map((n) => (
                  <button key={n} className={config.count === n ? 'on' : ''} aria-pressed={config.count === n} onClick={() => setConfig((c) => ({ ...c, count: n }))}>
                    {n === 'all' ? 'All' : n}
                  </button>
                ))}
              </div>
            </div>
            <div className="field">
              <span className="label">Level</span>
              <div className="segmented" role="radiogroup" aria-label="Level">
                {['all', 'beginner', 'intermediate', 'advanced'].map((l) => (
                  <button key={l} className={config.level === l ? 'on' : ''} aria-pressed={config.level === l} onClick={() => setConfig((c) => ({ ...c, level: l }))}>
                    {l === 'all' ? 'All levels' : LEVEL_LABEL[l]}
                  </button>
                ))}
              </div>
            </div>
            <div className="row wrap">
              <select className="select" style={{ width: 'auto', minWidth: 220 }} aria-label="Topic" value={config.topic} onChange={(e) => setConfig((c) => ({ ...c, topic: e.target.value }))}>
                <option value="">All topics</option>
                {topics.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
              <button className={`btn btn-sm btn-hot ${config.hot ? 'is-on' : ''}`} aria-pressed={config.hot} onClick={() => setConfig((c) => ({ ...c, hot: !c.hot }))}>
                <Flame size={15} /> Hot only
              </button>
            </div>
            <div className="spread">
              <span className="subtle">
                {pool.length} questions match · you'll get {config.count === 'all' ? pool.length : Math.min(config.count, pool.length)}
              </span>
              <button className="btn btn-primary btn-lg" onClick={() => start()} disabled={!pool.length}>
                <Shuffle size={17} /> Start quiz
              </button>
            </div>
          </div>
        </div>

        {attempts.length > 0 && (
          <div className="card">
            <div className="card-title">
              <History size={18} /> Attempt history
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th className="num">Score</th>
                    <th className="num">Correct</th>
                    <th className="num">Time</th>
                    <th>Filters</th>
                  </tr>
                </thead>
                <tbody>
                  {[...attempts].reverse().map((a) => (
                    <tr key={a.id}>
                      <td>{new Date(a.at).toLocaleString()}</td>
                      <td className="num">{a.score_pct}%</td>
                      <td className="num">
                        {a.correct}/{a.total}
                      </td>
                      <td className="num">{formatTime(a.duration_sec || 0)}</td>
                      <td className="subtle">
                        {[a.filters?.level && a.filters.level !== 'all' ? LEVEL_LABEL[a.filters.level] : 'All levels', a.filters?.topic, a.filters?.hot ? 'Hot only' : null]
                          .filter(Boolean)
                          .join(' · ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {dialogEl}
      </div>
    )
  }

  // ---------------------------------------------------------------- running
  if (phase === 'running' && current) {
    const correctSoFar = answers.filter((a) => a?.correct).length
    return (
      <div className="quiz-wrap">
        <div className="quiz-progress" style={{ marginBottom: 14 }}>
          <span>
            Question {index + 1} of {questions.length}
          </span>
          <Meter value={index + (answered ? 1 : 0)} max={questions.length} label="Quiz progress" />
          <span className="row">
            <Timer size={15} /> {formatTime(elapsed)}
          </span>
          <span>
            {correctSoFar}/{answers.filter(Boolean).length} correct
          </span>
        </div>
        <div className="card" style={{ padding: 24 }}>
          <div className="row wrap">
            <LevelBadge level={current.level} />
            <span className="chip">{current.topic}</span>
            {current.hot && <HotBadge reason={current.hot_reason} />}
          </div>
          <div className="quiz-q">
            <Markdown>{current.question}</Markdown>
          </div>
          <div className="options" role="radiogroup" aria-label="Answer options">
            {current.options.map((opt, i) => {
              let state = ''
              if (answered) {
                if (i === current.correct_index) state = 'correct'
                else if (i === answered.selected) state = 'wrong'
              }
              return (
                <button key={i} className={`option ${state}`} disabled={Boolean(answered)} onClick={() => choose(i)} aria-pressed={answered?.selected === i}>
                  <span className="key">{KEYS[i]}</span>
                  <span>{opt}</span>
                  {state === 'correct' && (
                    <span className="verdict">
                      <CircleCheck size={15} /> Correct answer
                    </span>
                  )}
                  {state === 'wrong' && (
                    <span className="verdict">
                      <CircleX size={15} /> Your answer
                    </span>
                  )}
                  {answered && current.option_explanations[i] && <span className="option-why">{current.option_explanations[i]}</span>}
                </button>
              )
            })}
          </div>
          {answered && (
            <div className="stack" style={{ marginTop: 16, gap: 12 }}>
              <div className={`banner ${answered.correct ? '' : 'error'}`}>
                {answered.correct ? <CircleCheck size={18} /> : <CircleX size={18} />}
                <div>
                  <strong>{answered.correct ? 'Correct! ' : 'Not quite. '}</strong>
                  {current.explanation}
                </div>
              </div>
              {current.interview_tip && (
                <div className="tip-box">
                  <Lightbulb size={17} />
                  <div>
                    <strong>In the interview: </strong>
                    {current.interview_tip}
                  </div>
                </div>
              )}
              <div className="row" style={{ justifyContent: 'flex-end' }}>
                <button className="btn btn-primary" onClick={next} autoFocus>
                  {index + 1 < questions.length ? 'Next question' : 'See my results'} <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}
          {!answered && <p className="subtle" style={{ marginTop: 12 }}>Tip: press A-D (or 1-4) to answer and Enter for the next question.</p>}
        </div>
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => window.confirm('Quit this quiz? Progress will not be saved.') && setPhase('setup')}>
            Quit quiz
          </button>
        </div>
      </div>
    )
  }

  // ---------------------------------------------------------------- results
  const total = questions.length
  const correct = answers.filter((a) => a?.correct).length
  const pct = total ? Math.round((100 * correct) / total) : 0
  const byTopic = {}
  questions.forEach((q, i) => {
    const t = (byTopic[q.topic] = byTopic[q.topic] || { total: 0, correct: 0 })
    t.total += 1
    if (answers[i]?.correct) t.correct += 1
  })
  const topicRows = Object.entries(byTopic)
    .map(([topic, t]) => ({ topic, ...t, pct: Math.round((100 * t.correct) / t.total) }))
    .sort((a, b) => a.pct - b.pct)
  const weak = topicRows.filter((t) => t.pct < 70)
  const verdict =
    pct >= 80 ? 'Interview-ready on these topics. Push yourself with advanced questions next.' : pct >= 60 ? 'Solid base - review the misses below and retry.' : 'Revise the weak topics below, then retry this quiz.'
  const review = questions.map((q, i) => ({ q, a: answers[i] })).sort((x, y) => Number(x.a?.correct) - Number(y.a?.correct))

  return (
    <div>
      <div className="section-head">
        <div>
          <h1>Quiz results</h1>
          <p>{verdict}</p>
        </div>
        <div className="row wrap no-print">
          <button className="btn" onClick={() => start(questions)}>
            <RotateCcw size={16} /> Retry these questions
          </button>
          <button className="btn btn-primary" onClick={() => setPhase('setup')}>
            <Play size={16} /> New quiz
          </button>
        </div>
      </div>

      <div className="result-grid">
        <div className="card">
          <div className="stat-label">
            <Trophy size={15} /> Your score
          </div>
          <div className="hero-figure" style={{ margin: '10px 0 6px' }}>
            {pct}%
          </div>
          <div className="muted">
            {correct} of {total} correct · {formatTime(elapsed)}
          </div>
          <div style={{ marginTop: 14 }}>
            <Meter value={correct} max={total} label="Correct answers" />
          </div>
          {weak.length > 0 && (
            <div style={{ marginTop: 18 }}>
              <h3 className="label">Revise next</h3>
              <ul className="list-clean">
                {weak.map((t) => (
                  <li key={t.topic}>
                    <BookOpen size={15} className="icon-accent" />
                    <Link to={`/prep/${session.id}/revision?topic=${encodeURIComponent(t.topic)}`}>
                      {t.topic} ({t.correct}/{t.total})
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <div className="card">
          <div className="card-title">
            <ListChecks size={18} /> Accuracy by topic
          </div>
          <BarList
            ariaLabel="Accuracy by topic"
            items={topicRows.map((t) => ({
              key: t.topic,
              label: t.topic,
              value: t.pct,
              max: 100,
              display: `${t.correct}/${t.total} · ${t.pct}%`,
              tooltip: { title: t.topic, lines: [`${t.correct} of ${t.total} correct (${t.pct}%)`, t.pct < 70 ? 'Worth revising before the interview' : 'Looking good'] },
            }))}
          />
        </div>
      </div>

      <h2 style={{ margin: '26px 0 12px' }}>Review your answers</h2>
      <div className="qlist">
        {review.map(({ q, a }, i) => (
          <div key={`${q.id}-${i}`} className="card card-flat">
            <div className="row wrap" style={{ marginBottom: 6 }}>
              {a?.correct ? (
                <span className="chip chip-good">
                  <CircleCheck size={12} /> Correct
                </span>
              ) : (
                <span className="chip chip-critical">
                  <CircleX size={12} /> Incorrect
                </span>
              )}
              <LevelBadge level={q.level} />
              <span className="chip">{q.topic}</span>
            </div>
            <Markdown>{q.question}</Markdown>
            <div className="stack" style={{ gap: 4, marginTop: 8, fontSize: '0.92rem' }}>
              {!a?.correct && a && (
                <div>
                  <strong>Your answer:</strong> {KEYS[a.selected]}. {q.options[a.selected]}
                </div>
              )}
              <div>
                <strong>Correct answer:</strong> {KEYS[q.correct_index]}. {q.options[q.correct_index]}
              </div>
              <div className="muted">{q.explanation}</div>
            </div>
          </div>
        ))}
      </div>
      {dialogEl}
    </div>
  )
}
