import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Brain,
  Briefcase,
  Building2,
  ClipboardList,
  FileText,
  Globe,
  GraduationCap,
  Info,
  Layers,
  LoaderCircle,
  Sparkles,
  Target,
  WandSparkles,
} from 'lucide-react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'
import FileDrop from '../components/FileDrop.jsx'
import { ModeBadge } from '../components/Badges.jsx'

const MIN_CHARS = 80
const DEPTH_META = {
  quick: { label: 'Quick', blurb: 'Night-before crash prep' },
  standard: { label: 'Standard', blurb: 'Balanced, recommended' },
  deep: { label: 'Deep', blurb: 'Full week of preparation' },
}

function totalQuestions(plan) {
  if (!plan) return 0
  return plan.theory + plan.practical + plan.scenario + plan.quiz
}

export default function NewPrep() {
  const { health, healthError, notify } = useApp()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    company: '',
    role: '',
    years: '',
    resumeText: '',
    jdText: '',
    extraNotes: '',
    depth: 'standard',
  })
  const [resumeMode, setResumeMode] = useState('file')
  const [jdMode, setJdMode] = useState('text')
  const [resumeFiles, setResumeFiles] = useState([])
  const [jdFiles, setJdFiles] = useState([])
  const [extraFiles, setExtraFiles] = useState([])
  const [forceDemo, setForceDemo] = useState(false)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [recent, setRecent] = useState([])

  useEffect(() => {
    api
      .listSessions()
      .then((list) => setRecent(list.slice(0, 4)))
      .catch(() => {})
  }, [])

  const set = (patch) => setForm((f) => ({ ...f, ...patch }))
  const aiMode = health?.mode === 'ai' && !forceDemo
  const depths = health?.depths

  const validate = () => {
    const e = {}
    if (!form.company.trim()) e.company = 'Enter the company you are interviewing with.'
    const years = Number(form.years)
    if (form.years === '' || Number.isNaN(years) || years < 0 || years > 50) e.years = 'Enter your total experience (0-50 years).'
    if (resumeMode === 'file' ? resumeFiles.length === 0 : form.resumeText.trim().length < MIN_CHARS)
      e.resume = resumeMode === 'file' ? 'Upload your resume (or switch to paste text).' : `Paste at least ${MIN_CHARS} characters of your resume.`
    if (jdMode === 'file' ? jdFiles.length === 0 : form.jdText.trim().length < MIN_CHARS)
      e.jd = jdMode === 'file' ? 'Upload the job description (or paste it).' : `Paste the job description (at least ${MIN_CHARS} characters).`
    setErrors(e)
    if (Object.keys(e).length) {
      requestAnimationFrame(() =>
        document.querySelector('.field-error')?.closest('.field')?.scrollIntoView({ behavior: 'smooth', block: 'center' }),
      )
    }
    return Object.keys(e).length === 0
  }

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
      notify('Sample inputs loaded - press "Build my prep kit".')
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const submit = async (event) => {
    event.preventDefault()
    if (!validate()) return
    const data = new FormData()
    data.append('company', form.company.trim())
    data.append('role', form.role.trim())
    data.append('years_experience', String(Number(form.years)))
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

  const steps = useMemo(
    () => [
      { icon: Globe, title: 'Researches the company', text: 'Searches the web for interview experiences, rounds and questions candidates actually reported.' },
      { icon: Brain, title: 'Matches you to the JD', text: 'Finds your strengths, gaps and the resume projects interviewers will dig into.' },
      { icon: Layers, title: 'Builds your prep kit', text: 'Crash revision notes plus level-wise theory, practical and scenario questions with model answers.' },
      { icon: Target, title: 'Lets you practise', text: 'Scored MCQ quizzes, answer feedback and fresh questions whenever you want more.' },
    ],
    [],
  )

  return (
    <main className="page">
      <div className="hero">
        <form className="card" onSubmit={submit} noValidate style={{ padding: 24 }}>
          <h1 className="hero-title">Prepare for your next interview</h1>
          <p className="hero-lead">
            Give the agent your resume, the job description, your experience and the company. It researches how they
            interview and builds a complete, personalised prep kit with 50+ questions.
          </p>

          <div className="form-grid">
            <div className="field">
              <label htmlFor="company">
                <Building2 size={14} style={{ verticalAlign: '-2px' }} /> Target company<span className="req">*</span>
              </label>
              <input
                id="company"
                className={`input ${errors.company ? 'invalid' : ''}`}
                value={form.company}
                maxLength={120}
                placeholder="e.g. Tiger Analytics"
                onChange={(e) => set({ company: e.target.value })}
              />
              {errors.company && <span className="field-error">{errors.company}</span>}
            </div>
            <div className="field">
              <label htmlFor="years">
                <GraduationCap size={14} style={{ verticalAlign: '-2px' }} /> Total years of experience<span className="req">*</span>
              </label>
              <input
                id="years"
                type="number"
                min="0"
                max="50"
                step="0.5"
                className={`input ${errors.years ? 'invalid' : ''}`}
                value={form.years}
                placeholder="e.g. 4"
                onChange={(e) => set({ years: e.target.value })}
              />
              {errors.years && <span className="field-error">{errors.years}</span>}
            </div>

            <div className="field span-2">
              <div className="spread">
                <span className="label">
                  <FileText size={14} style={{ verticalAlign: '-2px' }} /> Your resume<span className="req">*</span>
                </span>
                <div className="segmented" role="radiogroup" aria-label="Resume input">
                  <button type="button" className={resumeMode === 'file' ? 'on' : ''} aria-pressed={resumeMode === 'file'} onClick={() => setResumeMode('file')}>
                    Upload file
                  </button>
                  <button type="button" className={resumeMode === 'text' ? 'on' : ''} aria-pressed={resumeMode === 'text'} onClick={() => setResumeMode('text')}>
                    Paste text
                  </button>
                </div>
              </div>
              {resumeMode === 'file' ? (
                <FileDrop files={resumeFiles} onChange={setResumeFiles} label="Drop your resume here or click to browse" invalid={Boolean(errors.resume)} />
              ) : (
                <textarea
                  className={`textarea ${errors.resume ? 'invalid' : ''}`}
                  rows={7}
                  value={form.resumeText}
                  placeholder="Paste your resume text…"
                  onChange={(e) => set({ resumeText: e.target.value })}
                  aria-label="Resume text"
                />
              )}
              {errors.resume && <span className="field-error">{errors.resume}</span>}
            </div>

            <div className="field span-2">
              <div className="spread">
                <label className="label" htmlFor="jd">
                  <ClipboardList size={14} style={{ verticalAlign: '-2px' }} /> Job description<span className="req">*</span>
                </label>
                <div className="segmented" role="radiogroup" aria-label="Job description input">
                  <button type="button" className={jdMode === 'text' ? 'on' : ''} aria-pressed={jdMode === 'text'} onClick={() => setJdMode('text')}>
                    Paste text
                  </button>
                  <button type="button" className={jdMode === 'file' ? 'on' : ''} aria-pressed={jdMode === 'file'} onClick={() => setJdMode('file')}>
                    Upload file
                  </button>
                </div>
              </div>
              {jdMode === 'text' ? (
                <textarea
                  id="jd"
                  className={`textarea ${errors.jd ? 'invalid' : ''}`}
                  rows={7}
                  value={form.jdText}
                  placeholder="Paste the full job description of the role you are targeting…"
                  onChange={(e) => set({ jdText: e.target.value })}
                />
              ) : (
                <FileDrop files={jdFiles} onChange={setJdFiles} label="Drop the JD here or click to browse" invalid={Boolean(errors.jd)} />
              )}
              {errors.jd && <span className="field-error">{errors.jd}</span>}
            </div>

            <div className="field">
              <label htmlFor="role">
                <Briefcase size={14} style={{ verticalAlign: '-2px' }} /> Role title <span className="subtle">(optional)</span>
              </label>
              <input
                id="role"
                className="input"
                value={form.role}
                maxLength={160}
                placeholder="Detected from the JD if empty"
                onChange={(e) => set({ role: e.target.value })}
              />
            </div>
            <div className="field">
              <span className="label">Attachments <span className="subtle">(optional)</span></span>
              <FileDrop
                files={extraFiles}
                onChange={setExtraFiles}
                multiple
                label="Notes, past interview experiences…"
                hint="Up to 5 files: PDF, DOCX, TXT, MD"
              />
            </div>

            <div className="field span-2">
              <label htmlFor="extra">
                Anything else the agent should know? <span className="subtle">(optional)</span>
              </label>
              <textarea
                id="extra"
                className="textarea"
                rows={3}
                style={{ minHeight: 80 }}
                value={form.extraNotes}
                maxLength={8000}
                placeholder="e.g. rounds the recruiter mentioned, topics to focus on, notes from your own research…"
                onChange={(e) => set({ extraNotes: e.target.value })}
              />
            </div>

            <div className="field span-2">
              <span className="label">Prep depth</span>
              <div className="depth-options" role="radiogroup" aria-label="Prep depth">
                {Object.entries(DEPTH_META).map(([key, meta]) => (
                  <button
                    type="button"
                    key={key}
                    className={`depth-option ${form.depth === key ? 'on' : ''}`}
                    aria-pressed={form.depth === key}
                    onClick={() => set({ depth: key })}
                  >
                    <strong>{meta.label}</strong>
                    <span>
                      {depths ? `${totalQuestions(depths[key])} questions · ${depths[key].topics} topics` : meta.blurb}
                    </span>
                    <span style={{ display: 'block' }}>{meta.blurb}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {health?.mode === 'ai' && (
            <label className="toggle" style={{ marginTop: 16 }}>
              <input type="checkbox" checked={forceDemo} onChange={(e) => setForceDemo(e.target.checked)} />
              Use the offline demo knowledge base instead of Claude (no API calls)
            </label>
          )}

          <div className="row wrap" style={{ marginTop: 22 }}>
            <button className="btn btn-primary btn-lg" type="submit" disabled={submitting}>
              {submitting ? <LoaderCircle size={18} className="spin" /> : <WandSparkles size={18} />}
              {submitting ? 'Starting the agent…' : 'Build my prep kit'}
            </button>
            <button className="btn btn-lg" type="button" onClick={loadSample} disabled={submitting}>
              <Sparkles size={18} /> Try a sample
            </button>
          </div>
        </form>

        <aside className="stack">
          <div className="card">
            <div className="spread" style={{ marginBottom: 12 }}>
              <div className="card-title" style={{ margin: 0 }}>
                <Sparkles size={18} /> How the agent works
              </div>
              {health && <ModeBadge mode={aiMode ? 'ai' : 'demo'} />}
            </div>
            <ol className="how-steps">
              {steps.map(({ icon: Icon, title, text }) => (
                <li key={title}>
                  <span className="step-icon">
                    <Icon size={18} />
                  </span>
                  <div>
                    <strong>{title}</strong>
                    <p>{text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          {healthError && (
            <div className="banner error">
              <Info size={18} />
              <span>{healthError}</span>
            </div>
          )}
          {health && !aiMode && (
            <div className="banner warn">
              <Info size={18} />
              <span>
                {health.mode === 'ai'
                  ? 'Demo mode selected: the kit will come from the built-in knowledge base.'
                  : 'Running in offline demo mode. Add ANTHROPIC_API_KEY to backend/.env and restart the server for live web research and fully personalised questions.'}
              </span>
            </div>
          )}
          {health && aiMode && (
            <div className="banner">
              <Info size={18} />
              <span>
                AI mode: Claude ({health.model}) {health.web_search ? 'with live web research' : 'without web search'}. A
                standard kit takes a few minutes; sections unlock as they finish.
              </span>
            </div>
          )}

          {recent.length > 0 && (
            <div className="card">
              <div className="spread" style={{ marginBottom: 10 }}>
                <div className="card-title" style={{ margin: 0 }}>
                  Recent prep kits
                </div>
                <Link to="/preps" className="subtle">
                  View all
                </Link>
              </div>
              <div className="stack" style={{ gap: 8 }}>
                {recent.map((s) => (
                  <Link key={s.id} to={`/prep/${s.id}`} className="file-pill" style={{ justifyContent: 'space-between', color: 'var(--text)' }}>
                    <span>
                      <strong>{s.company}</strong> · {s.role || 'Role from JD'}
                    </span>
                    <span className="subtle">{s.summary?.questions ?? 0} Qs</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </main>
  )
}
