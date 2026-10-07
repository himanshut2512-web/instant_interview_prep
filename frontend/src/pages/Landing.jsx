import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import {
  ArrowRight,
  BookOpen,
  Bot,
  Brain,
  Check,
  CircleCheck,
  Code2,
  Download,
  FileUp,
  Flame,
  Globe,
  Layers,
  ListChecks,
  Lock,
  MapPin,
  MessagesSquare,
  PenLine,
  Play,
  Plus,
  Puzzle,
  Search,
  Sparkles,
  Target,
  Trophy,
  UserRound,
  Zap,
} from 'lucide-react'
import { api } from '../api.js'
import { EASE, fadeUp, inView, stagger } from '../lib/motion.js'
import { avatarStyle, initials, timeAgo } from '../lib/format.js'
import { CountUp, Reveal } from '../components/Motion.jsx'
import { ProgressRing } from '../components/Viz.jsx'
import Footer from '../components/Footer.jsx'

const plusFormat = (v) => `${Math.round(v)}+`

const ROLES = ['Data Scientist', 'Software Engineer', 'Data Engineer', 'Product Analyst', 'ML Engineer', 'Business Analyst']

const DEMO_STEPS = [
  { icon: Search, text: 'Searching “Lumen Analytics data scientist interview questions”' },
  { icon: Globe, text: 'Reading glassdoor.com interview reviews' },
  { icon: Globe, text: 'Reading geeksforgeeks.org interview experiences' },
  { icon: CircleCheck, text: 'Found 14 reported questions across 4 rounds', ok: true },
  { icon: Brain, text: 'Matching your resume to the JD: 12 of 15 skills covered', note: true },
  { icon: BookOpen, text: 'Writing crash-revision notes for 10 topics' },
  { icon: Layers, text: '+24 theory · +15 practical · +15 scenario questions' },
  { icon: Trophy, text: 'Prep kit ready: 79 questions across 10 topics', ok: true },
]

const STEPS = [
  { icon: FileUp, title: 'Share your profile', text: 'Upload your resume, paste the job description and add your experience and the company.', section: 'overview' },
  { icon: Globe, title: 'The agent researches', text: 'It searches public interview experiences for that company and role, and keeps every source.', section: 'theory' },
  { icon: Layers, title: 'Get your prep kit', text: 'Crash notes plus level-wise theory, practical and scenario questions with model answers.', section: 'revision' },
  { icon: Target, title: 'Practise and track', text: 'Answer in practice mode for instant feedback, take scored quizzes and watch readiness grow.', section: 'quiz' },
]

const FEATURES = [
  { icon: Globe, title: 'Live company research', text: 'Searches interview experiences and reported questions on the web and lists every source it used.', section: 'overview' },
  { icon: UserRound, title: 'Tailored to your resume', text: 'Finds your strengths and gaps against the JD and writes your “tell me about yourself” pitch.', section: 'revision' },
  { icon: Flame, title: 'Level-wise & hot questions', text: 'Beginner to advanced, with the most-asked and company-reported questions flagged.', section: 'scenario' },
  { icon: PenLine, title: 'Practice with feedback', text: 'Type your answer and get a score out of 10, the points you missed and an improved version.', section: 'theory' },
  { icon: Trophy, title: 'Scored MCQ quizzes', text: 'Shuffled questions with an explanation for every option, accuracy by topic and attempt history.', section: 'quiz' },
  { icon: Download, title: 'Take it anywhere', text: 'Export the whole kit as Markdown or print a clean crash sheet to revise on the way.', section: 'practical' },
]

const TOPICS_A = ['Python', 'SQL', 'Statistics', 'A/B testing', 'Machine learning', 'Deep learning', 'GenAI & RAG', 'Spark']
const TOPICS_B = ['MLOps', 'Power BI & DAX', 'Data structures', 'System design', 'Case studies', 'Guesstimates', 'Behavioural', 'STAR stories']
const TOPIC_COLORS = ['var(--c-theory)', 'var(--c-practical)', 'var(--c-scenario)', 'var(--c-quiz)', 'var(--c-revision)']

const FAQS = [
  {
    q: 'Do I need an API key?',
    a: 'No key is needed to try it: without one the app runs in demo mode and builds kits from a built-in 13-topic knowledge base. Add an Anthropic API key on the server for live web research and freshly generated, fully personalised questions.',
  },
  {
    q: 'Which roles does it work for?',
    a: 'Any role with a job description. The agent plans topics from your JD and resume, so it adapts to data, analytics, software, AI, product and business roles. The built-in demo library is deepest for data and software roles.',
  },
  {
    q: 'Where does the company research come from?',
    a: 'In AI mode the agent searches public interview experiences (for example Glassdoor, AmbitionBox, GeeksforGeeks and Reddit) and company pages. Every source is listed in your kit, and it never attributes a question to a source that did not contain it.',
  },
  {
    q: 'How long does a kit take?',
    a: 'Demo kits are ready in seconds. In AI mode a standard kit takes a few minutes, and each dashboard unlocks as soon as its section is ready, so you can start reading straight away.',
  },
  {
    q: 'Can I get more questions or practise answers?',
    a: 'Yes. Every dashboard has “Generate more” for fresh questions by level and topic, practice mode hides the answers so you can try first, and you can get feedback on any typed answer.',
  },
  {
    q: 'Is my resume stored?',
    a: 'Kits are saved in a local SQLite database on the server you run. In AI mode, your resume, JD and notes are sent to the Anthropic API to generate the kit.',
  },
]

function RotatingWord() {
  const reduce = useReducedMotion()
  const [index, setIndex] = useState(0)
  useEffect(() => {
    if (reduce) return undefined
    const id = setInterval(() => setIndex((i) => (i + 1) % ROLES.length), 2600)
    return () => clearInterval(id)
  }, [reduce])
  return (
    <span className="rotator">
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={ROLES[index]}
          className="rotator-word gradient-text"
          initial={{ y: '70%', opacity: 0 }}
          animate={{ y: '0%', opacity: 1 }}
          exit={{ y: '-70%', opacity: 0 }}
          transition={{ duration: 0.45, ease: EASE }}
        >
          {ROLES[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

function AgentDemo() {
  const reduce = useReducedMotion()
  const [tick, setTick] = useState(reduce ? DEMO_STEPS.length : 1)

  useEffect(() => {
    if (reduce) return undefined
    const id = setInterval(() => setTick((t) => (t >= DEMO_STEPS.length + 3 ? 1 : t + 1)), 1150)
    return () => clearInterval(id)
  }, [reduce])

  const shown = Math.min(tick, DEMO_STEPS.length)
  const percent = Math.round((100 * shown) / DEMO_STEPS.length)
  const done = shown === DEMO_STEPS.length
  const visible = DEMO_STEPS.slice(0, shown).map((step, i) => ({ ...step, i })).slice(-5)

  return (
    <motion.div
      className="hero-visual"
      initial={{ opacity: 0, y: 30, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.25, ease: EASE }}
      aria-label="Animated preview of the agent researching a company and building a prep kit"
      role="img"
    >
      <div className="demo-window" aria-hidden="true">
        <div className="demo-bar">
          <span className="code-dots">
            <i />
            <i />
            <i />
          </span>
          <span className="demo-url">
            <Lock size={12} /> Prep agent · Lumen Analytics · Data Scientist
          </span>
        </div>
        <div className="demo-body">
          <div className="demo-head">
            <div className="demo-title">
              <strong>{done ? 'Prep kit ready' : 'Researching Lumen Analytics…'}</strong>
              <span>{done ? '5 dashboards unlocked' : 'Live web research · sources kept'}</span>
            </div>
            <ProgressRing value={percent} size={58} stroke={6} label="Agent progress">
              <span style={{ fontWeight: 750, fontSize: 13 }}>{percent}%</span>
            </ProgressRing>
          </div>
          <div className="demo-progress">
            <div style={{ width: `${percent}%` }} />
          </div>
          <ul className="demo-log">
            <AnimatePresence initial={false}>
              {visible.map((step) => {
                const Icon = step.icon
                return (
                  <motion.li
                    key={step.i}
                    layout
                    initial={{ opacity: 0, y: 12, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, transition: { duration: 0.2 } }}
                    transition={{ duration: 0.4, ease: EASE }}
                  >
                    <span className={`ico ${step.ok ? 'ok' : step.note ? 'note' : ''}`}>
                      <Icon size={15} />
                    </span>
                    <span>{step.text}</span>
                  </motion.li>
                )
              })}
            </AnimatePresence>
          </ul>
        </div>
      </div>

      <motion.div className="float-card fc-1" aria-hidden="true" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.9, duration: 0.6, ease: EASE }}>
        <span className="fc-icon" style={{ background: 'var(--hot-soft)', color: 'var(--hot-ink)' }}>
          <Flame size={17} />
        </span>
        <span>
          Explain the bias-variance trade-off
          <small>Hot · reported in technical round 1</small>
        </span>
      </motion.div>
      <motion.div className="float-card fc-2" aria-hidden="true" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 1.15, duration: 0.6, ease: EASE }} data-section="quiz">
        <ProgressRing value={92} size={46} stroke={5} label="Quiz score">
          <span style={{ fontWeight: 750, fontSize: 11.5 }}>92%</span>
        </ProgressRing>
        <span>
          Quiz score
          <small>23 of 25 correct</small>
        </span>
      </motion.div>
      <motion.div className="float-card fc-3" aria-hidden="true" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.4, duration: 0.6, ease: EASE }}>
        <span className="fc-icon" style={{ background: 'var(--c-theory-soft)', color: 'var(--c-theory-ink)' }}>
          <Bot size={17} />
        </span>
        <span>
          Practice feedback: 8/10
          <small>Add a metric from your project</small>
        </span>
      </motion.div>
    </motion.div>
  )
}

function SectionHeading({ icon: Icon, kicker, title, lead }) {
  return (
    <motion.div className="section-head" variants={stagger(0.08)} {...inView}>
      <motion.div className="kicker" variants={fadeUp}>
        <Icon size={15} /> {kicker}
      </motion.div>
      <motion.h2 className="section-title" variants={fadeUp}>
        {title}
      </motion.h2>
      {lead && (
        <motion.p className="section-lead" variants={fadeUp}>
          {lead}
        </motion.p>
      )}
    </motion.div>
  )
}

function FaqItem({ q, a, open, onToggle, id }) {
  return (
    <div className={`faq-item ${open ? 'open' : ''}`}>
      <button className="faq-q" onClick={onToggle} aria-expanded={open} aria-controls={`faq-${id}`}>
        {q}
        <span className="pm" aria-hidden="true">
          <Plus size={16} />
        </span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={`faq-${id}`}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: EASE }}
            style={{ overflow: 'hidden' }}
          >
            <div className="faq-a">{a}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function Marquee({ items, reverse = false }) {
  const doubled = [...items, ...items]
  return (
    <div className={`marquee ${reverse ? 'reverse' : ''}`}>
      <div className="marquee-track">
        {doubled.map((t, i) => (
          <span className="topic-pill" key={`${t}-${i}`} aria-hidden={i >= items.length ? 'true' : undefined}>
            <span className="td" style={{ background: TOPIC_COLORS[i % TOPIC_COLORS.length] }} />
            {t}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function Landing() {
  const [recent, setRecent] = useState([])
  const [openFaq, setOpenFaq] = useState(0)

  useEffect(() => {
    api
      .listSessions()
      .then((list) => setRecent(list.filter((s) => s.status === 'completed').slice(0, 3)))
      .catch(() => {})
  }, [])

  return (
    <>
      <main className="landing">
        {/* ------------------------------------------------------------ hero */}
        <section className="hero">
          <div className="hero-bg" aria-hidden="true">
            <span className="hero-blob blob-1" />
            <span className="hero-blob blob-2" />
            <span className="hero-blob blob-3" />
          </div>
          <div className="container hero-grid">
            <motion.div className="hero-copy" variants={stagger(0.1, 0.05)} initial="hidden" animate="show">
              <motion.div variants={fadeUp}>
                <a className="eyebrow" href="#how">
                  <span className="tag">
                    <span className="live-dot" /> AI agent
                  </span>
                  Researches the company for you
                  <ArrowRight size={14} />
                </a>
              </motion.div>
              <motion.h1 className="hero-title" variants={fadeUp}>
                <span className="sr-only">Ace your next job interview</span>
                <span aria-hidden="true">
                  Ace your next
                  <RotatingWord />
                  interview.
                </span>
              </motion.h1>
              <motion.p className="hero-lead" variants={fadeUp}>
                Upload your resume and the job description. An AI agent researches how the company interviews, then builds
                your personal prep kit: crash notes, 50+ level-wise questions with model answers, real scenarios and a scored
                quiz.
              </motion.p>
              <motion.div className="hero-cta" variants={fadeUp}>
                <Link to="/new" className="btn btn-primary btn-xl">
                  <Zap size={18} fill="currentColor" strokeWidth={1.6} /> Build my prep kit
                </Link>
                <Link to="/new?sample=1" className="btn btn-xl">
                  <Play size={17} /> Try a live sample
                </Link>
              </motion.div>
              <motion.ul className="hero-points" variants={fadeUp}>
                <li>
                  <Check size={15} /> No sign-up
                </li>
                <li>
                  <Check size={15} /> Ready in minutes
                </li>
                <li>
                  <Check size={15} /> Works offline in demo mode
                </li>
              </motion.ul>
            </motion.div>
            <AgentDemo />
          </div>
        </section>

        {/* ----------------------------------------------------------- stats */}
        <section className="stats-band">
          <Reveal className="container">
            <div className="stats-grid">
              <div className="stat-cell">
                <strong className="gradient-text">
                  <CountUp value={5} startOnView />
                </strong>
                <span>study dashboards</span>
              </div>
              <div className="stat-cell">
                <strong className="gradient-text">
                  <CountUp value={50} startOnView format={plusFormat} />
                </strong>
                <span>questions in every kit</span>
              </div>
              <div className="stat-cell">
                <strong className="gradient-text">
                  <CountUp value={3} startOnView />
                </strong>
                <span>difficulty levels</span>
              </div>
              <div className="stat-cell">
                <strong className="gradient-text">
                  <CountUp value={13} startOnView />
                </strong>
                <span>topic areas offline</span>
              </div>
            </div>
          </Reveal>
        </section>

        {recent.length > 0 && (
          <section className="continue">
            <Reveal className="container">
              <div className="continue-head">
                <h2>Continue preparing</h2>
                <Link to="/preps" className="subtle">
                  All prep kits
                </Link>
              </div>
              <div className="continue-grid">
                {recent.map((s) => (
                  <Link key={s.id} to={`/prep/${s.id}`} className="continue-card">
                    <span className="avatar sm" style={avatarStyle(s.company)}>
                      {initials(s.company)}
                    </span>
                    <span style={{ minWidth: 0 }}>
                      <strong className="ellipsis">{s.company}</strong>
                      <span className="subtle ellipsis" style={{ display: 'block' }}>
                        {s.role || 'Role from JD'} · {s.summary?.questions ?? 0} questions · {timeAgo(s.created_at)}
                      </span>
                    </span>
                    <ArrowRight size={17} className="arrow" />
                  </Link>
                ))}
              </div>
            </Reveal>
          </section>
        )}

        {/* ---------------------------------------------------- how it works */}
        <section className="section" id="how">
          <div className="container">
            <SectionHeading
              icon={Sparkles}
              kicker="How it works"
              title="From job description to interview-ready in four steps"
              lead="The agent does the research a careful candidate would do, then turns it into a plan you can actually practise."
            />
            <motion.div className="how-grid" role="list" variants={stagger(0.12)} {...inView}>
              <motion.span
                className="how-line"
                aria-hidden="true"
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 1.2, ease: EASE, delay: 0.3 }}
              />
              {STEPS.map(({ icon: Icon, title, text, section }, i) => (
                <motion.div key={title} className="how-card" role="listitem" variants={fadeUp} data-section={section}>
                  <div className="how-icon">
                    <Icon size={24} />
                    <span className="how-step">{i + 1}</span>
                  </div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ------------------------------------------------------ dashboards */}
        <section className="section section-tint" id="dashboards">
          <div className="container">
            <SectionHeading
              icon={Layers}
              kicker="Your prep kit"
              title="Five dashboards. One complete interview plan."
              lead="Each dashboard trains a different muscle, from last-minute revision to answering under pressure."
            />
            <motion.div className="bento" variants={stagger(0.08)} {...inView}>
              <motion.article className="bento-tile b-rev" variants={fadeUp} data-section="revision">
                <div className="bento-head">
                  <span className="bt-icon">
                    <BookOpen size={21} />
                  </span>
                  <div>
                    <h3>Crash revision</h3>
                    <p>Every likely topic as a one-page revision sheet: key concepts, examples, pitfalls and a cheat sheet.</p>
                  </div>
                </div>
                <div className="bento-preview mock-concepts" aria-hidden="true">
                  {['Bias-variance', 'Window functions', 'RAG pipelines'].map((t) => (
                    <div className="mock-concept" key={t}>
                      <strong>{t}</strong>
                      <div className="mock-line" />
                      <div className="mock-line w80" />
                      <div className="mock-line w60" />
                    </div>
                  ))}
                </div>
              </motion.article>

              <motion.article className="bento-tile b-quiz" variants={fadeUp} data-section="quiz">
                <div className="bento-head">
                  <span className="bt-icon">
                    <ListChecks size={21} />
                  </span>
                  <div>
                    <h3>MCQ quiz</h3>
                    <p>Shuffled questions, instant explanations and a score with accuracy by topic.</p>
                  </div>
                </div>
                <div className="bento-preview" aria-hidden="true">
                  <div className="mock-quiz-head">
                    <span>Question 3 of 10</span>
                    <span className="row" style={{ gap: 4, color: 'var(--hot-ink)' }}>
                      <Flame size={13} /> 3 in a row
                    </span>
                  </div>
                  <div className="meter thin" style={{ marginBottom: 14 }}>
                    <span style={{ width: '30%' }} />
                  </div>
                  <div className="mock-qtext">What does L1 regularisation do to model weights?</div>
                  <div className="mock-options">
                    {['L1 shrinks all weights equally', 'L1 drives some weights to exactly zero', 'L1 increases variance', 'L1 only works for trees'].map(
                      (t, i) => (
                        <div className={`mock-option ${i === 1 ? 'right' : ''}`} key={t}>
                          <b>{'ABCD'[i]}</b>
                          {t}
                          {i === 1 && <CircleCheck size={16} />}
                        </div>
                      ),
                    )}
                  </div>
                  <div className="mock-score" style={{ marginTop: 16 }}>
                    <ProgressRing value={92} size={64} stroke={7} label="Example quiz score">
                      <span style={{ fontWeight: 750, fontSize: 14 }}>92%</span>
                    </ProgressRing>
                    <div>
                      <strong style={{ display: 'block' }}>Interview-ready</strong>
                      <span className="subtle">23 of 25 correct · 6:41</span>
                    </div>
                  </div>
                </div>
              </motion.article>

              <motion.article className="bento-tile b-theory" variants={fadeUp} data-section="theory">
                <div className="bento-head">
                  <span className="bt-icon">
                    <MessagesSquare size={21} />
                  </span>
                  <div>
                    <h3>Theoretical</h3>
                    <p>Level-wise questions with model answers and the points interviewers listen for.</p>
                  </div>
                </div>
                <div className="bento-preview mock-card" aria-hidden="true">
                  <div className="row wrap">
                    <span className="chip chip-sec">Intermediate</span>
                    <span className="chip chip-hot">
                      <Flame size={12} /> Hot
                    </span>
                  </div>
                  <div className="q">Explain ROW_NUMBER vs RANK vs DENSE_RANK.</div>
                  <div className="mock-tick">
                    <Check size={14} /> Tie behaviour of each
                  </div>
                  <div className="mock-tick">
                    <Check size={14} /> N-th highest with DENSE_RANK
                  </div>
                </div>
              </motion.article>

              <motion.article className="bento-tile b-prac" variants={fadeUp} data-section="practical">
                <div className="bento-head">
                  <span className="bt-icon">
                    <Code2 size={21} />
                  </span>
                  <div>
                    <h3>Practical</h3>
                    <p>Hands-on coding and SQL problems with full solutions and complexity.</p>
                  </div>
                </div>
                <div className="bento-preview mock-code" aria-hidden="true">
                  <div>
                    <span className="k">def</span> <span className="f">top_k</span>(words, k):
                  </div>
                  <div>
                    {'    '}counts = <span className="f">Counter</span>(words)
                  </div>
                  <div>
                    {'    '}
                    <span className="k">return</span> heapq.<span className="f">nsmallest</span>(k, counts, ...)
                  </div>
                  <div className="c">{'    '}# O(n log k) time</div>
                </div>
              </motion.article>

              <motion.article className="bento-tile b-scen" variants={fadeUp} data-section="scenario">
                <div className="bento-head">
                  <span className="bt-icon">
                    <Puzzle size={21} />
                  </span>
                  <div>
                    <h3>Scenario-based</h3>
                    <p>Real on-the-job situations with a step-by-step game plan and a strong spoken answer.</p>
                  </div>
                </div>
                <div className="bento-preview" aria-hidden="true">
                  <div className="mock-brief">
                    <MapPin size={15} />
                    <span>Your demand forecast's error jumped from 12% to 30% after launch and planners stopped trusting it. What do you do?</span>
                  </div>
                  <div className="mock-steps">
                    {['Clarify', 'Diagnose', 'Decide', 'Communicate'].map((s, i) => (
                      <div className="mock-step" key={s}>
                        <i>{i + 1}</i>
                        {s}
                      </div>
                    ))}
                  </div>
                </div>
              </motion.article>

              <motion.article className="bento-tile b-feed" variants={fadeUp} data-section="overview">
                <div className="bento-head">
                  <span className="bt-icon">
                    <Bot size={21} />
                  </span>
                  <div>
                    <h3>Answer feedback</h3>
                    <p>Type an answer, get a score, missing points and a better version.</p>
                  </div>
                </div>
                <div className="bento-preview mock-card" aria-hidden="true">
                  <div className="spread">
                    <strong style={{ fontSize: 22 }}>8/10</strong>
                    <span className="chip chip-ok">Solid answer</span>
                  </div>
                  <div className="meter thin" style={{ margin: '10px 0' }}>
                    <span style={{ width: '80%' }} />
                  </div>
                  <div className="mock-tick">
                    <Check size={14} /> Clear definition and example
                  </div>
                  <div className="mock-tick">
                    <ArrowRight size={14} style={{ color: 'var(--brand-ink)' }} /> Add a metric from your project
                  </div>
                </div>
              </motion.article>
            </motion.div>
          </div>
        </section>

        {/* -------------------------------------------------------- features */}
        <section className="section">
          <div className="container">
            <SectionHeading
              icon={Zap}
              kicker="Why it works"
              title="Built around how real interviews are run"
              lead="Not a generic question bank: everything is planned from your resume, the JD and what the company actually asks."
            />
            <motion.div className="features" variants={stagger(0.07)} {...inView}>
              {FEATURES.map(({ icon: Icon, title, text, section }) => (
                <motion.div key={title} className="feature" variants={fadeUp} data-section={section}>
                  <div className="feature-icon">
                    <Icon size={21} />
                  </div>
                  <h3>{title}</h3>
                  <p>{text}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        <section className="topics" aria-label="Topics covered">
          <Marquee items={TOPICS_A} />
          <Marquee items={TOPICS_B} reverse />
        </section>

        {/* ------------------------------------------------------------- faq */}
        <section className="section" id="faq">
          <div className="container">
            <SectionHeading icon={MessagesSquare} kicker="FAQ" title="Questions, answered" />
            <Reveal className="faq">
              {FAQS.map((item, i) => (
                <FaqItem key={item.q} id={i} q={item.q} a={item.a} open={openFaq === i} onToggle={() => setOpenFaq(openFaq === i ? -1 : i)} />
              ))}
            </Reveal>
          </div>
        </section>

        {/* -------------------------------------------------------- final cta */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="container">
            <Reveal className="cta-band">
              <h2>Your next interview starts with the right questions.</h2>
              <p>Give the agent your resume and the job description. Your personalised prep kit will be ready in minutes.</p>
              <div className="hero-cta">
                <Link to="/new" className="btn btn-white btn-xl">
                  <Zap size={18} fill="currentColor" strokeWidth={1.6} /> Build my prep kit
                </Link>
                <Link to="/new?sample=1" className="btn btn-outline-white btn-xl">
                  <Play size={17} /> Try a live sample
                </Link>
              </div>
            </Reveal>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
