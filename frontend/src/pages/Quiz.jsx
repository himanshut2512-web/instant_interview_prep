import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import {
  ArrowRight,
  BookOpen,
  CircleCheck,
  CircleX,
  Flame,
  Gauge,
  History,
  Infinity as InfinityIcon,
  Lightbulb,
  ListChecks,
  Play,
  RotateCcw,
  Shuffle,
  Target,
  Timer,
  Trophy,
  WandSparkles,
  Zap,
} from 'lucide-react'
import { useApp } from '../context.jsx'
import { useWorkspace } from './Workspace.jsx'
import { EASE, fadeUp, stagger } from '../lib/motion.js'
import Markdown from '../components/Markdown.jsx'
import { HotBadge, LevelBadge, LEVEL_LABEL, OrdinalGlyph } from '../components/Badges.jsx'
import { BarList, Meter, ProgressRing, Sparkline } from '../components/Viz.jsx'
import { CountUp } from '../components/Motion.jsx'
import { SegmentedTabs } from '../components/Tabs.jsx'
import { CardTitle, EmptyState, PageBanner } from '../components/UI.jsx'
import Confetti from '../components/Confetti.jsx'
import GenerateMoreDialog from '../components/GenerateMoreDialog.jsx'

const KEYS = ['A', 'B', 'C', 'D', 'E', 'F']
const MODES = [
  { count: 5, label: 'Quick fire', blurb: '5 questions', icon: Zap },
  { count: 10, label: 'Standard', blurb: '10 questions', icon: Target },
  { count: 20, label: 'Marathon', blurb: '20 questions', icon: Gauge },
  { count: 'all', label: 'Everything', blurb: 'All matching', icon: InfinityIcon },
]

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

function streaks(answers) {
  let current = 0
  let best = 0
  for (const a of answers) {
    if (a?.correct) {
      current += 1
      best = Math.max(best, current)
    } else if (a) current = 0
  }
  return { current, best }
}

export default function Quiz() {
  const { session, aiMode, addQuizAttempt, generateMore } = useWorkspace()
  const { notify, confirm } = useApp()
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
  const [reviewFilter, setReviewFilter] = useState('all')

  const pool = useMemo(
    () => all.filter((q) => (config.level === 'all' || q.level === config.level) && (!config.topic || q.topic === config.topic) && (!config.hot || q.hot)),
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
    setReviewFilter('all')
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
      const duration = Math.round((Date.now() - startedAt) / 1000)
      setElapsed(duration)
      setPhase('done')
      window.scrollTo({ top: 0, behavior: 'smooth' })
      try {
        await addQuizAttempt({
          total: questions.length,
          correct: finalAnswers.filter((a) => a?.correct).length,
          duration_sec: duration,
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
      if (e.key === 'Enter' && e.target.closest('button')) return
      const pos = KEYS.indexOf(e.key.toUpperCase())
      const num = Number(e.key) - 1
      if (pos >= 0 && pos < (current?.options.length || 0)) choose(pos)
      else if (num >= 0 && num < (current?.options.length || 0)) choose(num)
      else if (e.key === 'Enter') next()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, current, choose, next])

  const quit = async () => {
    const ok = await confirm({ title: 'Quit this quiz?', message: 'Your answers so far will not be saved.', confirmLabel: 'Quit quiz', tone: 'danger' })
    if (ok) setPhase('setup')
  }

  const onGenerate = async (body) => {
    const res = await generateMore(body)
    if (res.added.length) notify(`Added ${res.added.length} fresh MCQs to the pool.`)
    else notify(res.message || 'No new MCQs found.', 'error')
  }

  if (!all.length) {
    const active = session.status === 'running' || session.status === 'queued'
    return (
      <div data-section="quiz">
        <EmptyState
          icon={ListChecks}
          title={active ? 'Building your quiz…' : 'No MCQs yet'}
          text={active ? 'The MCQ quiz is being generated. It will appear here shortly.' : 'This kit has no quiz questions. Regenerate the kit from the overview.'}
        />
      </div>
    )
  }

  const dialogEl = <GenerateMoreDialog open={dialog} onClose={() => setDialog(false)} section="quiz" topics={topics} aiMode={aiMode} onSubmit={onGenerate} />
  const scores = attempts.map((a) => a.score_pct)
  const best = scores.length ? Math.max(...scores) : null
  const last = scores.length ? scores[scores.length - 1] : null

  // ------------------------------------------------------------------ setup
  if (phase === 'setup') {
    const willGet = config.count === 'all' ? pool.length : Math.min(config.count, pool.length)
    return (
      <div data-section="quiz">
        <PageBanner
          icon={ListChecks}
          kicker="Dashboard 5 · MCQ quiz"
          title="MCQ quiz arena"
          description="Rapid self-test with instant explanations for every option. Questions and options are shuffled on every attempt."
          stats={[
            { label: 'MCQs', value: all.length },
            { label: 'attempts', value: attempts.length },
            { label: 'best score', value: best === null ? '-' : `${best}%` },
          ]}
          actions={
            <button className="btn" onClick={() => setDialog(true)}>
              <WandSparkles size={16} /> Fresh MCQs
            </button>
          }
        />

        <div className="quiz-setup">
          <motion.section className="card card-pad-lg" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }}>
            <CardTitle icon={Play} title="Choose your challenge" sub="Pick a format, then narrow it down by level, topic or hot questions." />
            <motion.div className="quiz-modes" variants={stagger(0.06)} initial="hidden" animate="show">
              {MODES.map(({ count, label, blurb, icon: Icon }) => (
                <motion.button
                  variants={fadeUp}
                  key={String(count)}
                  className={`mode-card ${config.count === count ? 'on' : ''}`}
                  aria-pressed={config.count === count}
                  onClick={() => setConfig((c) => ({ ...c, count }))}
                >
                  <span className="mc-icon">
                    <Icon size={19} />
                  </span>
                  <strong>{label}</strong>
                  <span className="mc-blurb">{blurb}</span>
                </motion.button>
              ))}
            </motion.div>
            <div className="stack" style={{ gap: 14, marginTop: 20 }}>
              <div className="field">
                <span className="label">Level</span>
                <SegmentedTabs
                  ariaLabel="Level"
                  value={config.level}
                  onChange={(level) => setConfig((c) => ({ ...c, level }))}
                  options={['all', 'beginner', 'intermediate', 'advanced'].map((l, i) => ({
                    value: l,
                    label: l === 'all' ? 'All levels' : LEVEL_LABEL[l],
                    icon: i ? <OrdinalGlyph value={i} /> : null,
                  }))}
                />
              </div>
              <div className="row wrap">
                <select className="select sm" style={{ minWidth: 220 }} aria-label="Topic" value={config.topic} onChange={(e) => setConfig((c) => ({ ...c, topic: e.target.value }))}>
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
              <div className="spread" style={{ marginTop: 6 }}>
                <span className="subtle">
                  {pool.length} questions match · you'll get {willGet}
                </span>
                <button className="btn btn-sec btn-lg" onClick={() => start()} disabled={!pool.length}>
                  <Shuffle size={17} /> Start quiz
                </button>
              </div>
            </div>
          </motion.section>

          <motion.section className="card card-pad-lg" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.08, ease: EASE }}>
            <CardTitle icon={Trophy} title="Your record" />
            <div className="match-top">
              <ProgressRing value={best ?? 0} size={92} stroke={9} label="Best quiz score">
                <span className="ring-value" style={{ fontSize: 20 }}>
                  {best === null ? '-' : `${best}%`}
                </span>
                <span className="ring-label">best</span>
              </ProgressRing>
              <div>
                <strong>{last === null ? 'No attempts yet' : `Last score ${last}%`}</strong>
                <span className="subtle">{attempts.length ? `${attempts.length} attempt${attempts.length === 1 ? '' : 's'} so far` : 'Take a quiz to start your trend'}</span>
                <Sparkline values={scores.slice(-12)} />
              </div>
            </div>
            {attempts.length > 0 ? (
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>When</th>
                      <th>Score</th>
                      <th className="num">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...attempts]
                      .reverse()
                      .slice(0, 8)
                      .map((a) => (
                        <tr key={a.id}>
                          <td>{new Date(a.at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                          <td>
                            <div className="score-cell">
                              <Meter className="thin" value={a.score_pct} max={100} label={`${a.score_pct}%`} />
                              <span className="tabular">
                                {a.correct}/{a.total} · {a.score_pct}%
                              </span>
                            </div>
                          </td>
                          <td className="num">{formatTime(a.duration_sec || 0)}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="subtle" style={{ margin: 0 }}>
                <History size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 6 }} />
                Your attempts will appear here with time and score.
              </p>
            )}
          </motion.section>
        </div>
        {dialogEl}
      </div>
    )
  }

  // ---------------------------------------------------------------- running
  if (phase === 'running' && current) {
    const correctSoFar = answers.filter((a) => a?.correct).length
    const { current: streak } = streaks(answers)
    return (
      <div data-section="quiz" className="quiz-run">
        <div className="quiz-hud">
          <span className="hud-item">
            Question {index + 1}/{questions.length}
          </span>
          <Meter value={index + (answered ? 1 : 0)} max={questions.length} label="Quiz progress" />
          <span className="hud-item">
            <Timer size={15} /> {formatTime(elapsed)}
          </span>
          <span className="hud-item">
            <CircleCheck size={15} className="icon-ok" /> {correctSoFar}
          </span>
          <AnimatePresence>
            {streak >= 2 && (
              <motion.span className="hud-item hud-streak" initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.6, opacity: 0 }}>
                <Flame size={15} /> {streak} streak
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={index}
            className="quiz-card"
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.3, ease: EASE }}
          >
            <div className="row wrap">
              <LevelBadge level={current.level} />
              <span className="chip">{current.topic}</span>
              {current.hot && <HotBadge reason={current.hot_reason} />}
            </div>
            <div className="quiz-q">
              <Markdown>{current.question}</Markdown>
            </div>
            <div className="options" role="group" aria-label="Answer options">
              {current.options.map((opt, i) => {
                let state = ''
                if (answered) {
                  if (i === current.correct_index) state = 'correct'
                  else if (i === answered.selected) state = 'wrong'
                  else state = 'dim'
                }
                return (
                  <button key={i} className={`option ${state}`} disabled={Boolean(answered)} onClick={() => choose(i)} aria-pressed={answered?.selected === i}>
                    <span className="key">{KEYS[i]}</span>
                    <span>{opt}</span>
                    {state === 'correct' && (
                      <span className="verdict">
                        <CircleCheck size={15} /> Correct
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
            <AnimatePresence>
              {answered && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3, ease: EASE }}>
                  <div className={`explain ${answered.correct ? 'good' : 'bad'}`}>
                    {answered.correct ? <CircleCheck size={19} /> : <CircleX size={19} />}
                    <div>
                      <strong>{answered.correct ? 'Correct! ' : 'Not quite. '}</strong>
                      {current.explanation}
                    </div>
                  </div>
                  {current.interview_tip && (
                    <div className="tip-box" style={{ marginTop: 10 }}>
                      <Lightbulb size={18} />
                      <div>
                        <strong>In the interview: </strong>
                        {current.interview_tip}
                      </div>
                    </div>
                  )}
                  <div className="row" style={{ justifyContent: 'flex-end', marginTop: 14 }}>
                    <button className="btn btn-sec btn-lg" onClick={next} autoFocus>
                      {index + 1 < questions.length ? 'Next question' : 'See my results'} <ArrowRight size={17} />
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            {!answered && (
              <p className="subtle" style={{ marginTop: 14 }}>
                Press <kbd className="kbd">A</kbd>-<kbd className="kbd">D</kbd> to answer and <kbd className="kbd">Enter</kbd> for the next question.
              </p>
            )}
          </motion.div>
        </AnimatePresence>
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-ghost btn-sm" onClick={quit}>
            Quit quiz
          </button>
        </div>
      </div>
    )
  }

  // ---------------------------------------------------------------- results
  const total = questions.length
  const correct = answers.filter((a) => a?.correct).length
  const scorePct = total ? Math.round((100 * correct) / total) : 0
  const { best: bestStreak } = streaks(answers)
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
  const grade = scorePct >= 80 ? 'Interview-ready!' : scorePct >= 60 ? 'Almost there' : 'Keep practising'
  const verdict =
    scorePct >= 80
      ? 'Strong result on these topics. Push yourself with advanced questions next.'
      : scorePct >= 60
        ? 'A solid base. Review the misses below and retry.'
        : 'Revise the weak topics below, then retry this quiz.'
  const review = questions.map((q, i) => ({ q, a: answers[i] })).filter(({ a }) => reviewFilter === 'all' || (reviewFilter === 'wrong' ? !a?.correct : a?.correct))

  return (
    <div data-section="quiz">
      <Confetti fire={scorePct >= 80} />
      <motion.section className="page-banner result-hero" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, ease: EASE }}>
        <ProgressRing value={scorePct} size={150} stroke={13} label="Quiz score">
          <span className="ring-value">
            <CountUp value={scorePct} format={(v) => `${Math.round(v)}%`} />
          </span>
          <span className="ring-label">
            {correct} of {total} correct
          </span>
        </ProgressRing>
        <div>
          <div className="banner-kicker">Quiz results</div>
          <h1 className="grade">{grade}</h1>
          <p>{verdict}</p>
          <div className="result-stats">
            <span className="chip chip-lg">
              <Timer size={14} /> {formatTime(elapsed)}
            </span>
            <span className="chip chip-lg chip-hot">
              <Flame size={14} /> Best streak {bestStreak}
            </span>
            {best !== null && (
              <span className="chip chip-lg chip-sec">
                <Trophy size={14} /> All-time best {Math.max(best, scorePct)}%
              </span>
            )}
          </div>
        </div>
        <div className="banner-actions">
          <button className="btn" onClick={() => start(questions)}>
            <RotateCcw size={16} /> Retry these
          </button>
          <button className="btn btn-sec" onClick={() => setPhase('setup')}>
            <Play size={16} /> New quiz
          </button>
        </div>
      </motion.section>

      <div className="ov-grid" style={{ marginTop: 0 }}>
        <section className="card c7">
          <CardTitle icon={ListChecks} title="Accuracy by topic" sub="Weakest topics first." />
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
        </section>
        <section className="card c5">
          <CardTitle icon={BookOpen} title="Revise next" sub={weak.length ? 'Topics under 70% in this attempt.' : 'Nothing under 70%. Nicely done!'} />
          {weak.length > 0 ? (
            <ul className="lq-list">
              {weak.map((t) => (
                <li key={t.topic}>
                  <BookOpen size={16} />
                  <Link to={`/prep/${session.id}/revision?topic=${encodeURIComponent(t.topic)}`}>
                    {t.topic} ({t.correct}/{t.total})
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <div className="banner-note ok">
              <Trophy size={18} />
              <span>Every topic in this quiz scored 70% or more. Try the advanced level next.</span>
            </div>
          )}
        </section>
      </div>

      <div className="spread" style={{ margin: '26px 0 12px' }}>
        <h2 style={{ margin: 0 }}>Review your answers</h2>
        <SegmentedTabs
          ariaLabel="Show"
          value={reviewFilter}
          onChange={setReviewFilter}
          options={[
            { value: 'all', label: 'All', count: total },
            { value: 'wrong', label: 'Incorrect', count: total - correct },
            { value: 'right', label: 'Correct', count: correct },
          ]}
        />
      </div>
      <motion.div className="qlist" variants={stagger(0.04)} initial="hidden" animate="show" key={reviewFilter}>
        {review.map(({ q, a }, i) => (
          <motion.div key={`${q.id}-${i}`} className="review-item" variants={fadeUp}>
            <div className="row wrap" style={{ marginBottom: 8 }}>
              {a?.correct ? (
                <span className="chip chip-ok">
                  <CircleCheck size={12} /> Correct
                </span>
              ) : (
                <span className="chip chip-bad">
                  <CircleX size={12} /> Incorrect
                </span>
              )}
              <LevelBadge level={q.level} />
              <span className="chip">{q.topic}</span>
            </div>
            <Markdown>{q.question}</Markdown>
            {!a?.correct && a && (
              <div className="ans">
                <CircleX size={16} className="icon-bad" />
                <span>
                  <strong>Your answer:</strong> {KEYS[a.selected]}. {q.options[a.selected]}
                </span>
              </div>
            )}
            <div className="ans">
              <CircleCheck size={16} className="icon-ok" />
              <span>
                <strong>Correct answer:</strong> {KEYS[q.correct_index]}. {q.options[q.correct_index]}
              </span>
            </div>
            <p className="muted" style={{ margin: '8px 0 0', fontSize: 14 }}>
              {q.explanation}
            </p>
          </motion.div>
        ))}
      </motion.div>
      {dialogEl}
    </div>
  )
}
