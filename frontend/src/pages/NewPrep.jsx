import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'motion/react'
import {
  ArrowLeft,
  Briefcase,
  Building2,
  Check,
  CircleAlert,
  ClipboardList,
  Code2,
  FileText,
  Info,
  Layers,
  ListChecks,
  LoaderCircle,
  MessagesSquare,
  Mountain,
  Puzzle,
  Rabbit,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import { fadeUp, stagger } from '../lib/motion.js'
import { avatarStyle, initials, seniority } from '../lib/format.js'
import FileDrop from '../components/FileDrop.jsx'
import { ModeBadge } from '../components/Badges.jsx'
import { SegmentedTabs } from '../components/Tabs.jsx'
import Footer from '../components/Footer.jsx'

const MIN_CHARS = 80
const DEPTHS = [
  { key: 'quick', label: 'Quick', blurb: 'Night-before crash prep', icon: Rabbit },
  { key: 'standard', label: 'Standard', blurb: 'Balanced and thorough', icon: Layers, badge: 'Recommended' },
  { key: 'deep', label: 'Deep', blurb: 'A full week of practice', icon: Mountain },
]
const FALLBACK_DEPTHS = {
  quick: { topics: 8, theory: 15, practical: 10, scenario: 10, quiz: 15 },
  standard: { topics: 10, theory: 24, practical: 15, scenario: 15, quiz: 25 },
  deep: { topics: 14, theory: 36, practical: 21, scenario: 21, quiz: 36 },
}

function total(plan) {
  return plan ? plan.theory + plan.practical + plan.scenario + plan.quiz : 0
}

function FormSection({ index, title, desc, done, optional, children }) {
  return (
    <motion.section className={`card form-section ${done ? 'done' : ''}`} variants={fadeUp}>
      <div className="fs-head">
        <span className="fs-index" aria-hidden="true">
          {done ? <Check size={17} strokeWidth={3} /> : index}
        </span>
        <div>
          <h2>
            {title}
            {optional && <span className="opt">Optional</span>}
          </h2>
          <p>{desc}</p>
        </div>
      </div>
      {children}
    </motion.section>
  )
}

function FieldError({ children }) {
  if (!children) return null
  return (
    <span className="field-error" role="alert">
      <CircleAlert size={14} /> {children}
    </span>
  )
}

export default function NewPrep() {
  const { health, healthError, notify } = useApp()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [form, setForm] = useState({ company: '', role: '', years: '', resumeText: '', jdText: '', extraNotes: '', depth: 'standard' })
  const [resumeMode, setResumeMode] = useState('file')
  const [jdMode, setJdMode] = useState('text')
  const [resumeFiles, setResumeFiles] = useState([])
  const [jdFiles, setJdFiles] = useState([])
  const [extraFiles, setExtraFiles] = useState([])
  const [forceDemo, setForceDemo] = useState(false)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const sampleLoaded = useRef(false)

  const set = (patch) => setForm((f) => ({ ...f, ...patch }))
  const aiMode = health?.mode === 'ai' && !forceDemo
  const depths = health?.depths || FALLBACK_DEPTHS
  const plan = depths[form.depth] || FALLBACK_DEPTHS.standard

  const years = Number(form.years)
  const targetDone = form.company.trim().length > 0 && form.years !== '' && !Number.isNaN(years) && years >= 0 && years <= 50
  const resumeDone = resumeMode === 'file' ? resumeFiles.length > 0 : form.resumeText.trim().length >= MIN_CHARS
  const jdDone = jdMode === 'file' ? jdFiles.length > 0 : form.jdText.trim().length >= MIN_CHARS
  const requiredDone = [form.company.trim().length > 0, targetDone, resumeDone, jdDone]
  const doneCount = [form.company.trim().length > 0, form.years !== '' && !Number.isNaN(years) && years >= 0 && years <= 50, resumeDone, jdDone].filter(
    Boolean,
  ).length

  const loadSample = async () => {
    try {
      const sample = await api.sample()
      setForm((f) => ({
        ...f,
        company: sample.company,
        role: sample.role,
        years: String(sample.years_experience),
        resumeText: sample.resume_text,
        jdText: sample.job_description,
        extraNotes: sample.extra_notes,
      }))
      setResumeMode('text')
      setJdMode('text')
      setErrors({})
      notify('Sample inputs loaded. Press "Build my prep kit" to start the agent.')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  useEffect(() => {
    if (params.get('sample') === '1' && !sampleLoaded.current) {
      sampleLoaded.current = true
      loadSample()
      navigate('/new', { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  const validate = () => {
    const e = {}
    if (!form.company.trim()) e.company = 'Enter the company you are interviewing with.'
    if (form.years === '' || Number.isNaN(years) || years < 0 || years > 50) e.years = 'Enter your total experience (0-50 years).'
    if (!resumeDone) e.resume = resumeMode === 'file' ? 'Upload your resume, or switch to "Paste text".' : `Paste at least ${MIN_CHARS} characters of your resume.`
    if (!jdDone) e.jd = jdMode === 'file' ? 'Upload the job description, or paste it.' : `Paste the job description (at least ${MIN_CHARS} characters).`
    setErrors(e)
    if (Object.keys(e).length) {
      requestAnimationFrame(() => document.querySelector('.field-error')?.closest('.form-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
    }
    return Object.keys(e).length === 0
  }

  const submit = async (event) => {
    event?.preventDefault()
    if (!validate()) return
    const data = new FormData()
    data.append('company', form.company.trim())
    data.append('role', form.role.trim())
    data.append('years_experience', String(years))
    data.append('depth', form.depth)
    data.append('extra_notes', form.extraNotes)
    data.append('mode', forceDemo ? 'demo' : 'auto')
    if (resumeMode === 'file') data.append('resume_file', resumeFiles[0])
    else data.append('resume_text', form.resumeText)
    if (jdMode === 'file') data.append('jd_file', jdFiles[0])
    else data.append('job_description', form.jdText)
    extraFiles.forEach((f) => data.append('extra_files', f))
    setSubmitting(true)
    try {
      const created = await api.createSession(data)
      navigate(`/prep/${created.id}`)
    } catch (e) {
      notify(e.message, 'error')
      setSubmitting(false)
    }
  }

  const sliderValue = Math.min(20, Math.max(0, Number.isNaN(years) ? 0 : years))
  const steps = [
    { label: 'Target', done: targetDone },
    { label: 'Resume', done: resumeDone },
    { label: 'Job description', done: jdDone },
    { label: 'Launch', done: requiredDone.every(Boolean) },
  ]

  const buildButton = (size = 'btn-xl', extraClass = '') => (
    <button className={`btn btn-primary ${size} ${extraClass}`} type="submit" form="new-prep-form" disabled={submitting}>
      {submitting ? <LoaderCircle size={18} className="spin" /> : <Zap size={18} fill="currentColor" strokeWidth={1.6} />}
      {submitting ? 'Starting the agent…' : 'Build my prep kit'}
    </button>
  )

  return (
    <>
      <div className="new-shell">
      <main className="page new-page">
        <motion.header className="new-head" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
          <Link to="/" className="back-link">
            <ArrowLeft size={15} /> Home
          </Link>
          <h1>Create your prep kit</h1>
          <p>Four quick inputs. The agent does the rest: company research, a topic plan, model answers, scenarios and a quiz.</p>
          <div className="stepper" aria-label="Progress">
            {steps.map((step, i) => (
              <div key={step.label} style={{ display: 'contents' }}>
                <span className={`st ${step.done ? 'done' : ''}`}>
                  <span className="st-dot">{step.done ? <Check size={14} strokeWidth={3} /> : i + 1}</span>
                  <span className="label">{step.label}</span>
                </span>
                {i < steps.length - 1 && (
                  <span className={`st-line ${step.done ? 'done' : ''}`} aria-hidden="true">
                    <span />
                  </span>
                )}
              </div>
            ))}
          </div>
        </motion.header>

        <div className="new-grid">
          <motion.form id="new-prep-form" className="new-form" onSubmit={submit} noValidate variants={stagger(0.08)} initial="hidden" animate="show">
            <FormSection index={1} title="Your target" desc="Who are you interviewing with, and how much experience do you bring?" done={targetDone}>
              <div className="form-grid">
                <div className="field">
                  <label className="label" htmlFor="company">
                    Target company <span className="req">*</span>
                  </label>
                  <div className="input-wrap">
                    <Building2 size={17} />
                    <input
                      id="company"
                      className={`input ${errors.company ? 'invalid' : ''}`}
                      value={form.company}
                      maxLength={120}
                      placeholder="e.g. Tiger Analytics"
                      autoComplete="organization"
                      onChange={(e) => set({ company: e.target.value })}
                    />
                  </div>
                  <FieldError>{errors.company}</FieldError>
                </div>
                <div className="field">
                  <label className="label" htmlFor="role">
                    Role title <span className="opt">(optional)</span>
                  </label>
                  <div className="input-wrap">
                    <Briefcase size={17} />
                    <input id="role" className="input" value={form.role} maxLength={160} placeholder="Detected from the JD if empty" onChange={(e) => set({ role: e.target.value })} />
                  </div>
                </div>
                <div className="field span-2">
                  <label className="label" htmlFor="years">
                    Total years of experience <span className="req">*</span>
                  </label>
                  <div className="years-row">
                    <div>
                      <input
                        type="range"
                        className="range"
                        min="0"
                        max="20"
                        step="0.5"
                        value={sliderValue}
                        style={{ '--fill': `${(sliderValue / 20) * 100}%` }}
                        aria-label="Years of experience slider"
                        onChange={(e) => set({ years: e.target.value })}
                      />
                      <div className="range-scale" aria-hidden="true">
                        <span>0</span>
                        <span>5</span>
                        <span>10</span>
                        <span>15</span>
                        <span>20+</span>
                      </div>
                    </div>
                    <input
                      id="years"
                      type="number"
                      min="0"
                      max="50"
                      step="0.5"
                      inputMode="decimal"
                      className={`input ${errors.years ? 'invalid' : ''}`}
                      value={form.years}
                      placeholder="e.g. 4"
                      onChange={(e) => set({ years: e.target.value })}
                    />
                    <span className="band">
                      {form.years !== '' && !Number.isNaN(years) && <span className="chip chip-brand chip-lg">{seniority(years)}</span>}
                    </span>
                  </div>
                  <FieldError>{errors.years}</FieldError>
                </div>
              </div>
            </FormSection>

            <FormSection index={2} title="Your resume" desc="Used to find your strengths, gaps and the projects interviewers will dig into." done={resumeDone}>
              <div className="field">
                <div className="field-tabs">
                  <span className="label">
                    <FileText size={15} /> Resume <span className="req">*</span>
                  </span>
                  <SegmentedTabs
                    ariaLabel="Resume input"
                    value={resumeMode}
                    onChange={setResumeMode}
                    options={[
                      { value: 'file', label: 'Upload file' },
                      { value: 'text', label: 'Paste text' },
                    ]}
                  />
                </div>
                {resumeMode === 'file' ? (
                  <FileDrop files={resumeFiles} onChange={setResumeFiles} label="Drop your resume here or click to browse" invalid={Boolean(errors.resume)} />
                ) : (
                  <>
                    <textarea
                      className={`textarea ${errors.resume ? 'invalid' : ''}`}
                      rows={8}
                      value={form.resumeText}
                      placeholder="Paste your resume text…"
                      aria-label="Resume text"
                      onChange={(e) => set({ resumeText: e.target.value })}
                    />
                    <div className="textarea-foot">
                      <span className="hint">Plain text is fine; formatting is not needed.</span>
                      <span className="char-count">{form.resumeText.length.toLocaleString()} chars</span>
                    </div>
                  </>
                )}
                <FieldError>{errors.resume}</FieldError>
              </div>
            </FormSection>

            <FormSection index={3} title="Job description" desc="Paste the full JD: responsibilities, required skills and nice-to-haves." done={jdDone}>
              <div className="field">
                <div className="field-tabs">
                  <label className="label" htmlFor="jd">
                    <ClipboardList size={15} /> Job description <span className="req">*</span>
                  </label>
                  <SegmentedTabs
                    ariaLabel="Job description input"
                    value={jdMode}
                    onChange={setJdMode}
                    options={[
                      { value: 'text', label: 'Paste text' },
                      { value: 'file', label: 'Upload file' },
                    ]}
                  />
                </div>
                {jdMode === 'text' ? (
                  <>
                    <textarea
                      id="jd"
                      className={`textarea ${errors.jd ? 'invalid' : ''}`}
                      rows={8}
                      value={form.jdText}
                      placeholder="Paste the full job description of the role you are targeting…"
                      onChange={(e) => set({ jdText: e.target.value })}
                    />
                    <div className="textarea-foot">
                      <span className="hint">The more complete the JD, the sharper the topic plan.</span>
                      <span className="char-count">{form.jdText.length.toLocaleString()} chars</span>
                    </div>
                  </>
                ) : (
                  <FileDrop files={jdFiles} onChange={setJdFiles} label="Drop the JD here or click to browse" invalid={Boolean(errors.jd)} />
                )}
                <FieldError>{errors.jd}</FieldError>
              </div>
            </FormSection>

            <FormSection index={4} title="Fine-tune" optional desc="Choose how deep to go and add anything that helps the agent." done>
              <div className="stack" style={{ gap: 18 }}>
                <div className="field">
                  <span className="label">Prep depth</span>
                  <div className="depth-grid" role="group" aria-label="Prep depth">
                    {DEPTHS.map(({ key, label, blurb, icon: Icon, badge }) => (
                      <button
                        type="button"
                        key={key}
                        className={`depth-card ${form.depth === key ? 'on' : ''}`}
                        aria-pressed={form.depth === key}
                        onClick={() => set({ depth: key })}
                      >
                        {badge && <span className="dc-badge">{badge}</span>}
                        <span className="dc-icon">
                          <Icon size={18} />
                        </span>
                        <strong>{label}</strong>
                        <span className="dc-meta">
                          {total(depths[key])} questions · {depths[key].topics} topics
                        </span>
                        <span className="dc-meta">{blurb}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="field">
                  <label className="label" htmlFor="extra">
                    Anything else the agent should know? <span className="opt">(optional)</span>
                  </label>
                  <textarea
                    id="extra"
                    className="textarea"
                    rows={3}
                    style={{ minHeight: 92 }}
                    value={form.extraNotes}
                    maxLength={8000}
                    placeholder="e.g. rounds the recruiter mentioned, topics to focus on, notes from your own research…"
                    onChange={(e) => set({ extraNotes: e.target.value })}
                  />
                </div>
                <div className="field">
                  <span className="label">
                    Attachments <span className="opt">(optional, up to 5)</span>
                  </span>
                  <FileDrop files={extraFiles} onChange={setExtraFiles} multiple label="Notes or past interview experiences" hint="PDF, DOCX, TXT or MD" />
                </div>
                {health?.mode === 'ai' && (
                  <label className="toggle">
                    <input type="checkbox" checked={forceDemo} onChange={(e) => setForceDemo(e.target.checked)} />
                    Use the offline demo knowledge base for this kit (no API calls)
                  </label>
                )}
              </div>
            </FormSection>
          </motion.form>

          <motion.aside className="new-summary" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.15 }}>
            <div className="card summary-card">
              <div className="spread" style={{ marginBottom: 14 }}>
                <span className="subtle" style={{ fontWeight: 650 }}>
                  Your kit preview
                </span>
                {health && <ModeBadge mode={aiMode ? 'ai' : 'demo'} />}
              </div>
              <div className="sum-company">
                <span className="avatar" style={form.company ? avatarStyle(form.company) : { background: 'var(--surface-3)', color: 'var(--ink-3)' }}>
                  {form.company ? initials(form.company) : <Target size={18} />}
                </span>
                <span style={{ minWidth: 0 }}>
                  <strong className="ellipsis">{form.company || 'Target company'}</strong>
                  <span className="subtle ellipsis" style={{ display: 'block' }}>
                    {form.role || 'Role from the JD'}
                    {form.years !== '' && !Number.isNaN(years) ? ` · ${years} yrs · ${seniority(years)}` : ''}
                  </span>
                </span>
              </div>
              <div className="sum-tiles">
                {[
                  { key: 'theory', label: 'Theory', icon: MessagesSquare },
                  { key: 'practical', label: 'Practical', icon: Code2 },
                  { key: 'scenario', label: 'Scenario', icon: Puzzle },
                  { key: 'quiz', label: 'MCQs', icon: ListChecks },
                ].map(({ key, label, icon: Icon }) => (
                  <div className="sum-tile" data-section={key} key={key}>
                    <Icon size={18} />
                    <span>
                      <strong>{plan[key]}</strong>
                      <small>{label}</small>
                    </span>
                  </div>
                ))}
              </div>
              <div className="subtle">
                + crash-revision notes for {plan.topics} topics, company intel and a study plan
              </div>
              <ul className="checklist">
                {[
                  ['Company', form.company.trim().length > 0],
                  ['Years of experience', form.years !== '' && !Number.isNaN(years) && years >= 0 && years <= 50],
                  ['Resume', resumeDone],
                  ['Job description', jdDone],
                ].map(([label, ok]) => (
                  <li key={label} className={ok ? 'ok' : ''}>
                    <span className="check-dot" aria-hidden="true">
                      <Check size={13} strokeWidth={3} />
                    </span>
                    {label}
                    <span className="sr-only">{ok ? 'done' : 'missing'}</span>
                  </li>
                ))}
              </ul>
              <div className="stack" style={{ gap: 10 }}>
                {buildButton('btn-xl', 'btn-block')}
                <button className="btn btn-lg btn-block" type="button" onClick={loadSample} disabled={submitting}>
                  <Sparkles size={17} /> Try a sample
                </button>
              </div>
              {healthError && (
                <div className="banner-note error" style={{ marginTop: 14 }}>
                  <CircleAlert size={18} />
                  <span>{healthError}</span>
                </div>
              )}
              {health && (
                <div className={`banner-note ${aiMode ? '' : 'warn'}`} style={{ marginTop: 14, fontSize: 13 }}>
                  <Info size={17} />
                  <span>
                    {aiMode
                      ? `AI mode: Claude ${health.web_search ? 'researches the company live on the web' : '(web search off)'}. A kit takes a few minutes; sections unlock as they finish.`
                      : health.mode === 'ai'
                        ? 'Demo mode selected: this kit comes from the built-in knowledge base.'
                        : 'Demo mode: add ANTHROPIC_API_KEY to backend/.env and restart the server for live research.'}
                  </span>
                </div>
              )}
            </div>
          </motion.aside>
        </div>

        <div className="mobile-cta">
          <span className="subtle" style={{ fontWeight: 650 }}>
            {doneCount}/4 required
          </span>
          {buildButton('btn-lg')}
        </div>
      </main>
      </div>
      <Footer />
    </>
  )
}
