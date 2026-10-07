import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import {
  BookOpen,
  ChevronDown,
  CircleCheck,
  CircleX,
  Code2,
  CornerDownRight,
  Eye,
  EyeOff,
  FileText,
  Flame,
  Gauge,
  Lightbulb,
  ListChecks,
  MapPin,
  MessagesSquare,
  Mic,
  PenLine,
  Quote,
  RotateCcw,
  Route,
  ShieldCheck,
  Target,
} from 'lucide-react'
import { collapse, EASE } from '../lib/motion.js'
import Markdown, { codeFence } from './Markdown.jsx'
import { HotBadge, LevelBadge, NewBadge } from './Badges.jsx'
import { UnderlineTabs } from './Tabs.jsx'
import PracticePanel from './PracticePanel.jsx'

function Block({ title, icon: Icon, children, className = '' }) {
  return (
    <div className={`qblock ${className}`}>
      {title && (
        <h4 className="qblock-title">
          {Icon && <Icon size={14} />}
          {title}
        </h4>
      )}
      {children}
    </div>
  )
}

function Tip({ text }) {
  if (!text) return null
  return (
    <div className="qblock tip-box">
      <Lightbulb size={18} />
      <div>
        <strong>In the interview: </strong>
        {text}
      </div>
    </div>
  )
}

function FollowUps({ items }) {
  if (!items?.length) return null
  return (
    <Block title="Likely follow-up questions" icon={MessagesSquare}>
      <div className="followups">
        {items.map((f, i) => (
          <span className="followup" key={i}>
            <CornerDownRight size={14} />
            {f}
          </span>
        ))}
      </div>
    </Block>
  )
}

function TheoryBody({ item }) {
  return (
    <>
      <Block title="Model answer" icon={BookOpen}>
        <div className="answer-box">
          <Markdown>{item.answer_md}</Markdown>
        </div>
      </Block>
      {item.key_points?.length > 0 && (
        <Block title="What the interviewer listens for" icon={ListChecks}>
          <ul className="keypoints">
            {item.key_points.map((p, i) => (
              <li key={i}>
                <CircleCheck size={15} />
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </Block>
      )}
      <Tip text={item.interview_tip} />
      <FollowUps items={item.follow_ups} />
    </>
  )
}

function PracticalBody({ item }) {
  const [tab, setTab] = useState('solution')
  const tabs = [
    { value: 'problem', label: 'Problem', icon: <FileText size={14} /> },
    { value: 'approach', label: 'Approach', icon: <Route size={14} /> },
    { value: 'solution', label: 'Solution', icon: <Code2 size={14} /> },
    { value: 'checks', label: 'Edge cases', icon: <ShieldCheck size={14} /> },
  ]
  return (
    <>
      <div className="qblock">
        <UnderlineTabs value={tab} onChange={setTab} options={tabs} ariaLabel="Practical question sections" idPrefix={item.id} />
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={tab}
            id={`${item.id}-panel`}
            role="tabpanel"
            aria-labelledby={`${item.id}-tab-${tab}`}
            className="tab-panel"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.2, ease: EASE }}
          >
            {tab === 'problem' && (item.context ? <Markdown>{item.context}</Markdown> : <p className="subtle">The question above is the full problem statement.</p>)}
            {tab === 'approach' &&
              (item.approach?.length ? (
                <ol className="gameplan">
                  {item.approach.map((step, i) => (
                    <li className="gp-step" key={i}>
                      <span className="gp-node">{i + 1}</span>
                      <p style={{ margin: 0, paddingTop: 7, fontSize: 14 }}>{step}</p>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="subtle">Think out loud: clarify inputs, outline the idea, then code it.</p>
              ))}
            {tab === 'solution' && (
              <>
                <Markdown>{item.solution_md}</Markdown>
                <div style={{ marginTop: 12 }}>
                  <Markdown>{codeFence(item.code)}</Markdown>
                </div>
                {item.complexity && (
                  <div className="complexity">
                    <span className="cx-chip">
                      <Gauge size={15} /> {item.complexity}
                    </span>
                  </div>
                )}
              </>
            )}
            {tab === 'checks' && (
              <>
                {item.edge_cases?.length ? (
                  <ul className="list-clean">
                    {item.edge_cases.map((c, i) => (
                      <li key={i}>
                        <ShieldCheck size={16} className="icon-sec" />
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="subtle">No specific edge cases listed. Mention empty input, duplicates and very large data.</p>
                )}
                {item.complexity && (
                  <div className="complexity" style={{ marginTop: 12 }}>
                    <span className="cx-chip">
                      <Gauge size={15} /> {item.complexity}
                    </span>
                  </div>
                )}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
      <Tip text={item.interview_tip} />
      <FollowUps items={item.follow_ups} />
    </>
  )
}

function ScenarioBrief({ text }) {
  if (!text) return null
  return (
    <div className="qblock brief">
      <span className="brief-label">
        <MapPin size={14} /> The situation
      </span>
      <Markdown>{text}</Markdown>
    </div>
  )
}

function ScenarioBody({ item }) {
  return (
    <>
      <ScenarioBrief text={item.scenario} />
      {item.approach_steps?.length > 0 && (
        <Block title="Your game plan for the interview" icon={Route}>
          <ol className="gameplan">
            {item.approach_steps.map((s, i) => (
              <motion.li className="gp-step" key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.05 * i, duration: 0.35, ease: EASE }}>
                <span className="gp-node">{i + 1}</span>
                <div>
                  <strong>{s.step}</strong>
                  {s.detail && <p>{s.detail}</p>}
                </div>
              </motion.li>
            ))}
          </ol>
        </Block>
      )}
      <Block title="Say it like this" icon={Mic}>
        <div className="transcript">
          <Quote size={20} />
          <Markdown>{item.model_answer_md}</Markdown>
        </div>
      </Block>
      {(item.what_interviewer_looks_for?.length > 0 || item.mistakes_to_avoid?.length > 0) && (
        <div className="qblock lf-grid">
          {item.what_interviewer_looks_for?.length > 0 && (
            <div className="lf-card good">
              <h4>
                <Target size={16} /> What the interviewer looks for
              </h4>
              <ul className="list-clean">
                {item.what_interviewer_looks_for.map((t, i) => (
                  <li key={i}>
                    <CircleCheck size={15} className="icon-ok" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {item.mistakes_to_avoid?.length > 0 && (
            <div className="lf-card bad">
              <h4>
                <CircleX size={16} /> Mistakes to avoid
              </h4>
              <ul className="list-clean">
                {item.mistakes_to_avoid.map((t, i) => (
                  <li key={i}>
                    <CircleX size={15} className="icon-bad" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      <FollowUps items={item.follow_ups} />
    </>
  )
}

/** The part of a question shown before its answer is revealed. */
export function QuestionLead({ section, item }) {
  if (section === 'scenario') return <ScenarioBrief text={item.scenario} />
  if (section === 'practical' && item.context)
    return (
      <Block title="Problem details" icon={FileText}>
        <Markdown>{item.context}</Markdown>
      </Block>
    )
  return null
}

export function QuestionBody({ section, item }) {
  if (section === 'practical') return <PracticalBody item={item} />
  if (section === 'scenario') return <ScenarioBody item={item} />
  return <TheoryBody item={item} />
}

export function StatusChips({ item, status, evaluation }) {
  return (
    <>
      <LevelBadge level={item.level} />
      <span className="chip">{item.topic}</span>
      {item.hot && <HotBadge reason={item.hot_reason} />}
      {item.origin === 'more' && <NewBadge />}
      {status === 'mastered' && (
        <span className="chip chip-ok">
          <CircleCheck size={12} /> Mastered
        </span>
      )}
      {status === 'review' && (
        <span className="chip chip-warn">
          <RotateCcw size={12} /> Review later
        </span>
      )}
      {evaluation && (
        <span className="chip" title={`Best ${evaluation.best}/10 over ${evaluation.attempts} attempt(s)`}>
          <PenLine size={12} /> Practice {evaluation.score}/10
        </span>
      )}
    </>
  )
}

export default function QuestionCard({ item, index, section, status, evaluation, open, onToggle, practiceMode, aiMode, onSetStatus, onEvaluate }) {
  const [revealed, setRevealed] = useState(false)
  const [practising, setPractising] = useState(false)
  const hidden = practiceMode && !revealed
  const preview = section === 'scenario' && item.scenario && !open ? (item.scenario.length > 170 ? `${item.scenario.slice(0, 170)}…` : item.scenario) : ''

  return (
    <article className={`qcard ${open ? 'open' : ''} ${status || ''}`} id={item.id}>
      <button className="qhead" onClick={onToggle} aria-expanded={open} aria-controls={`${item.id}-body`}>
        <span className="qnum">{index + 1}</span>
        <span style={{ minWidth: 0 }}>
          <span className="qtext">{item.question}</span>
          {preview && <span className="qpreview">{preview}</span>}
          <span className="qmeta">
            <StatusChips item={item} status={status} evaluation={evaluation} />
          </span>
        </span>
        <span className="qchev" aria-hidden="true">
          <ChevronDown size={17} />
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div id={`${item.id}-body`} {...collapse} style={{ overflow: 'hidden' }}>
            <div className="qbody">
              {item.hot && item.hot_reason && (
                <div className="qblock row" style={{ color: 'var(--hot-ink)', fontSize: 13, fontWeight: 600 }}>
                  <Flame size={15} /> {item.hot_reason}
                </div>
              )}
              {hidden ? (
                <>
                  <QuestionLead section={section} item={item} />
                  <div className="qblock banner-note">
                    <EyeOff size={18} />
                    <span>Practice mode: the model answer is hidden. Answer first, then reveal it and compare.</span>
                  </div>
                  <PracticePanel onEvaluate={onEvaluate} aiMode={aiMode} />
                  <div style={{ marginTop: 12 }}>
                    <button className="btn btn-sm" onClick={() => setRevealed(true)}>
                      <Eye size={15} /> Reveal model answer
                    </button>
                  </div>
                </>
              ) : (
                <QuestionBody section={section} item={item} />
              )}

              <div className="qactions">
                <button className={`btn btn-sm ${status === 'mastered' ? 'is-on' : ''}`} aria-pressed={status === 'mastered'} onClick={() => onSetStatus(status === 'mastered' ? null : 'mastered')}>
                  <CircleCheck size={15} /> {status === 'mastered' ? 'Mastered' : 'Mark mastered'}
                </button>
                <button className={`btn btn-sm ${status === 'review' ? 'is-on' : ''}`} aria-pressed={status === 'review'} onClick={() => onSetStatus(status === 'review' ? null : 'review')}>
                  <RotateCcw size={15} /> Review later
                </button>
                {!hidden && (
                  <button className={`btn btn-sm ${practising ? 'is-on' : ''}`} onClick={() => setPractising((v) => !v)} aria-expanded={practising}>
                    <PenLine size={15} /> {practising ? 'Close practice' : 'Practise this answer'}
                  </button>
                )}
              </div>
              <AnimatePresence initial={false}>{!hidden && practising && <PracticePanel key="practice" onEvaluate={onEvaluate} aiMode={aiMode} />}</AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </article>
  )
}
