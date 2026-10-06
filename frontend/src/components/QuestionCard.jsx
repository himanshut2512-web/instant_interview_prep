import { useState } from 'react'
import {
  BookOpen,
  ChevronRight,
  CircleCheck,
  CircleX,
  Eye,
  Lightbulb,
  ListChecks,
  MessagesSquare,
  PenLine,
  RotateCcw,
  Route,
  Target,
} from 'lucide-react'
import Markdown, { codeFence } from './Markdown.jsx'
import { HotBadge, LevelBadge, NewBadge } from './Badges.jsx'
import PracticePanel from './PracticePanel.jsx'

function Section({ title, icon: Icon, children }) {
  return (
    <div className="qsection">
      <h4>
        {Icon && <Icon size={14} />}
        {title}
      </h4>
      {children}
    </div>
  )
}

function Bullets({ items, icon: Icon = CircleCheck, className = 'icon-good' }) {
  if (!items?.length) return null
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

function Tip({ text }) {
  if (!text) return null
  return (
    <div className="qsection tip-box">
      <Lightbulb size={17} />
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
    <Section title="Likely follow-up questions" icon={MessagesSquare}>
      <Bullets items={items} icon={ChevronRight} className="icon-accent" />
    </Section>
  )
}

function TheoryBody({ item }) {
  return (
    <>
      <Section title="Model answer" icon={BookOpen}>
        <Markdown>{item.answer_md}</Markdown>
      </Section>
      {item.key_points?.length > 0 && (
        <Section title="Key points the interviewer listens for" icon={ListChecks}>
          <Bullets items={item.key_points} />
        </Section>
      )}
      <Tip text={item.interview_tip} />
      <FollowUps items={item.follow_ups} />
    </>
  )
}

function PracticalBody({ item }) {
  return (
    <>
      {item.context && (
        <Section title="Problem details" icon={BookOpen}>
          <Markdown>{item.context}</Markdown>
        </Section>
      )}
      {item.approach?.length > 0 && (
        <Section title="How to approach it (think aloud)" icon={Route}>
          <ol className="steps">
            {item.approach.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </Section>
      )}
      <Section title="Solution" icon={CircleCheck}>
        <Markdown>{item.solution_md}</Markdown>
        <Markdown>{codeFence(item.code)}</Markdown>
      </Section>
      {(item.complexity || item.edge_cases?.length > 0) && (
        <div className="two-col">
          {item.complexity && (
            <Section title="Complexity" icon={Target}>
              <div className="md">{item.complexity}</div>
            </Section>
          )}
          {item.edge_cases?.length > 0 && (
            <Section title="Edge cases to mention" icon={ListChecks}>
              <Bullets items={item.edge_cases} icon={ChevronRight} className="icon-accent" />
            </Section>
          )}
        </div>
      )}
      <Tip text={item.interview_tip} />
      <FollowUps items={item.follow_ups} />
    </>
  )
}

function ScenarioBody({ item }) {
  return (
    <>
      {item.scenario && (
        <div className="qsection scenario-box">
          <Markdown>{item.scenario}</Markdown>
        </div>
      )}
      {item.approach_steps?.length > 0 && (
        <Section title="How to tackle it in the interview" icon={Route}>
          <ol className="steps">
            {item.approach_steps.map((s, i) => (
              <li key={i}>
                <strong>{s.step}</strong>
                {s.detail ? ` - ${s.detail}` : ''}
              </li>
            ))}
          </ol>
        </Section>
      )}
      <Section title="Model answer" icon={BookOpen}>
        <Markdown>{item.model_answer_md}</Markdown>
      </Section>
      <div className="two-col">
        {item.what_interviewer_looks_for?.length > 0 && (
          <Section title="What the interviewer looks for" icon={Target}>
            <Bullets items={item.what_interviewer_looks_for} />
          </Section>
        )}
        {item.mistakes_to_avoid?.length > 0 && (
          <Section title="Mistakes to avoid" icon={CircleX}>
            <Bullets items={item.mistakes_to_avoid} icon={CircleX} className="icon-warn" />
          </Section>
        )}
      </div>
      <FollowUps items={item.follow_ups} />
    </>
  )
}

const BODIES = { theory: TheoryBody, practical: PracticalBody, scenario: ScenarioBody }

export default function QuestionCard({
  item,
  index,
  section,
  status,
  evaluation,
  open,
  onToggle,
  practiceMode,
  aiMode,
  onSetStatus,
  onEvaluate,
}) {
  const [revealed, setRevealed] = useState(false)
  const [practising, setPractising] = useState(false)
  const Body = BODIES[section]
  const hidden = practiceMode && !revealed

  return (
    <article className={`qcard ${open ? 'open' : ''} ${status || ''}`} id={item.id}>
      <button className="qhead" onClick={onToggle} aria-expanded={open}>
        <span className="qnum">{index + 1}</span>
        <span>
          <span className="qtext">{item.question}</span>
          {section === 'scenario' && item.scenario && !open && (
            <span className="subtle" style={{ display: 'block', marginTop: 4 }}>
              {item.scenario.length > 160 ? `${item.scenario.slice(0, 160)}…` : item.scenario}
            </span>
          )}
          <span className="qmeta">
            <LevelBadge level={item.level} />
            <span className="chip">{item.topic}</span>
            {item.hot && <HotBadge reason={item.hot_reason} />}
            {item.origin === 'more' && <NewBadge />}
            {status === 'mastered' && (
              <span className="chip chip-good">
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
                <PenLine size={12} /> Last practice {evaluation.score}/10
              </span>
            )}
          </span>
        </span>
        <ChevronRight size={18} className="qchevron" aria-hidden="true" />
      </button>

      {open && (
        <div className="qbody">
          {item.hot && item.hot_reason && (
            <div className="qsection subtle">🔥 {item.hot_reason}</div>
          )}
          {hidden ? (
            <>
              {section === 'scenario' && item.scenario && (
                <div className="qsection scenario-box">
                  <Markdown>{item.scenario}</Markdown>
                </div>
              )}
              {section === 'practical' && item.context && (
                <Section title="Problem details" icon={BookOpen}>
                  <Markdown>{item.context}</Markdown>
                </Section>
              )}
              <div className="qsection banner">
                <Eye size={18} />
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
            <Body item={item} />
          )}

          <div className="qactions">
            <button
              className={`btn btn-sm ${status === 'mastered' ? 'is-on' : ''}`}
              aria-pressed={status === 'mastered'}
              onClick={() => onSetStatus(status === 'mastered' ? null : 'mastered')}
            >
              <CircleCheck size={15} /> {status === 'mastered' ? 'Mastered' : 'Mark mastered'}
            </button>
            <button
              className={`btn btn-sm ${status === 'review' ? 'is-on' : ''}`}
              aria-pressed={status === 'review'}
              onClick={() => onSetStatus(status === 'review' ? null : 'review')}
            >
              <RotateCcw size={15} /> Review later
            </button>
            {!hidden && (
              <button className={`btn btn-sm ${practising ? 'is-on' : ''}`} onClick={() => setPractising((v) => !v)}>
                <PenLine size={15} /> {practising ? 'Close practice' : 'Practise this answer'}
              </button>
            )}
          </div>
          {!hidden && practising && <PracticePanel onEvaluate={onEvaluate} aiMode={aiMode} />}
        </div>
      )}
    </article>
  )
}
