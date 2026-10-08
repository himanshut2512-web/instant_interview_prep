import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useAnimationControls, useReducedMotion } from 'motion/react'
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CircleAlert,
  CircleCheck,
  Eye,
  EyeOff,
  Flame,
  Globe,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  LoaderCircle,
  Lock,
  Mail,
  MailCheck,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
  TriangleAlert,
  UserRound,
} from 'lucide-react'
import { api } from '../api.js'
import { nextPath, useAuth } from '../auth.jsx'
import { useApp, useTheme } from '../context.jsx'
import { BrandMark } from '../components/TopBar.jsx'
import GoogleSignIn from '../components/GoogleSignIn.jsx'
import { EASE } from '../lib/motion.js'

const TITLES = {
  signin: 'Sign in',
  signup: 'Create your account',
  forgot: 'Reset your password',
  reset: 'Choose a new password',
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// ?error= codes the server sends back after a Google sign-in attempt
const SIGN_IN_ERRORS = {
  google_cancelled: 'Google sign-in was cancelled.',
  google_failed: 'Google sign-in didn’t complete. Please try again.',
  google_expired: 'That Google sign-in expired or was already used. Please try again.',
  google_email: 'Your Google account has no verified email address.',
  google_unavailable: 'Google sign-in isn’t set up on this server yet. Use your email and password for now.',
  too_many: 'Too many attempts. Please wait a few minutes and try again.',
}
const swap = {
  initial: { opacity: 0, y: 14, filter: 'blur(4px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)' },
  exit: { opacity: 0, y: -10, filter: 'blur(4px)' },
  transition: { duration: 0.32, ease: EASE },
}

// ---------------------------------------------------------------- helpers
function passwordRules(password, email = '') {
  return [
    { key: 'length', label: 'At least 8 characters', ok: password.length >= 8 },
    { key: 'mix', label: 'A letter and a number', ok: /[A-Za-z]/.test(password) && /\d/.test(password) },
    { key: 'email', label: 'Different from your email', ok: !email || password.toLowerCase() !== email.trim().toLowerCase() },
  ]
}

const STRENGTH = ['Too short', 'Weak', 'Fair', 'Good', 'Strong']

function passwordStrength(password) {
  if (password.length < 8) return 0
  let score = 1
  if (password.length >= 12) score++
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++
  if (/\d/.test(password) && /[^A-Za-z0-9]/.test(password)) score++
  if (password.length >= 16) score++
  if (/^(password|qwerty|letmein|welcome|admin|12345)/i.test(password) || /^(.)\1+$/.test(password)) score = 1
  return Math.min(4, score)
}

/** Shared submit plumbing: field errors, a form-level error and a little shake. */
function useFormState(initial) {
  const [values, setValues] = useState(initial)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const controls = useAnimationControls()
  const set = (key) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setValues((v) => ({ ...v, [key]: value }))
    if (errors[key]) setErrors((e) => ({ ...e, [key]: undefined }))
    if (formError) setFormError('')
  }
  const fail = (fieldErrors, message = '') => {
    setErrors(fieldErrors)
    setFormError(message)
    controls.start({ x: [0, -9, 9, -6, 6, -2, 0], transition: { duration: 0.45 } })
    const first = Object.keys(fieldErrors).find((k) => fieldErrors[k])
    if (first) requestAnimationFrame(() => document.getElementById(`auth-${first}`)?.focus())
  }
  const failFromServer = (error) => {
    if (error.field && error.field !== 'token') fail({ [error.field]: error.message })
    else fail({}, error.message)
  }
  return { values, setValues, set, errors, formError, setFormError, busy, setBusy, done, setDone, controls, fail, failFromServer }
}

// ----------------------------------------------------------------- pieces
function Field({ id, label, icon: Icon, error, trailing, hint, className = '', ...input }) {
  const describedBy = [error && `auth-${id}-error`, hint && `auth-${id}-hint`].filter(Boolean).join(' ') || undefined
  return (
    <div className={`field ${error ? 'invalid' : ''} ${className}`}>
      <div className="field-box">
        <Icon className="field-icon" size={18} aria-hidden="true" />
        <input id={`auth-${id}`} name={id} placeholder=" " aria-invalid={Boolean(error)} aria-describedby={describedBy} {...input} />
        <label htmlFor={`auth-${id}`}>{label}</label>
        {trailing}
      </div>
      <AnimatePresence initial={false}>
        {error && (
          <motion.p
            id={`auth-${id}-error`}
            className="field-error"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <CircleAlert size={14} aria-hidden="true" /> {error}
          </motion.p>
        )}
      </AnimatePresence>
      {hint}
    </div>
  )
}

function PasswordField({ id = 'password', label = 'Password', value, onChange, error, autoComplete, children }) {
  const [visible, setVisible] = useState(false)
  const [caps, setCaps] = useState(false)
  const capsCheck = (event) => setCaps(Boolean(event.getModifierState?.('CapsLock')))
  return (
    <Field
      id={id}
      label={label}
      icon={Lock}
      type={visible ? 'text' : 'password'}
      value={value}
      onChange={onChange}
      onKeyUp={capsCheck}
      onKeyDown={capsCheck}
      onBlur={() => setCaps(false)}
      error={error}
      autoComplete={autoComplete}
      maxLength={128}
      spellCheck={false}
      trailing={
        <button
          type="button"
          className="field-action"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
          aria-controls={`auth-${id}`}
        >
          {visible ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      }
      hint={
        <>
          <AnimatePresence initial={false}>
            {caps && (
              <motion.p className="field-note warn" initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <TriangleAlert size={14} aria-hidden="true" /> Caps Lock is on
              </motion.p>
            )}
          </AnimatePresence>
          {children}
        </>
      }
    />
  )
}

function StrengthMeter({ password, email }) {
  const score = passwordStrength(password)
  const rules = passwordRules(password, email)
  return (
    <div className="strength" id="auth-password-hint" aria-live="polite">
      <div className="strength-bar" data-score={password ? score : -1}>
        {[1, 2, 3, 4].map((step) => (
          <span key={step} className={password && score >= step ? 'on' : ''} />
        ))}
      </div>
      <div className="strength-row">
        <span className="strength-label">{password ? STRENGTH[score] : 'Password strength'}</span>
      </div>
      <ul className="rules">
        {rules.map((rule) => (
          <li key={rule.key} className={rule.ok && password ? 'ok' : ''}>
            <span className="rule-dot" aria-hidden="true">
              {rule.ok && password ? <Check size={11} strokeWidth={3.2} /> : null}
            </span>
            {rule.label}
            <span className="sr-only">{rule.ok && password ? ' (done)' : ' (missing)'}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function SubmitButton({ busy, done, children, busyLabel, doneLabel }) {
  return (
    <button type="submit" className={`btn btn-primary btn-lg btn-block auth-submit ${done ? 'done' : ''}`} disabled={busy || done} aria-busy={busy}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={done ? 'done' : busy ? 'busy' : 'idle'}
          className="auth-submit-inner"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
        >
          {done ? (
            <>
              <CircleCheck size={18} /> {doneLabel}
            </>
          ) : busy ? (
            <>
              <LoaderCircle size={18} className="spin" /> {busyLabel}
            </>
          ) : (
            children
          )}
        </motion.span>
      </AnimatePresence>
    </button>
  )
}

function FormAlert({ message, tone = 'error' }) {
  return (
    <AnimatePresence initial={false}>
      {message && (
        <motion.div
          className={`auth-alert ${tone}`}
          role={tone === 'error' ? 'alert' : 'status'}
          initial={{ opacity: 0, height: 0, marginBottom: 0 }}
          animate={{ opacity: 1, height: 'auto', marginBottom: 16 }}
          exit={{ opacity: 0, height: 0, marginBottom: 0 }}
          transition={{ duration: 0.22 }}
        >
          <span className="auth-alert-inner">
            {tone === 'error' ? <CircleAlert size={17} aria-hidden="true" /> : <ShieldCheck size={17} aria-hidden="true" />}
            <span>{message}</span>
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function RotatingWord({ words }) {
  const [index, setIndex] = useState(0)
  const reduce = useReducedMotion()
  useEffect(() => {
    if (reduce) return undefined
    const timer = setInterval(() => setIndex((i) => (i + 1) % words.length), 2600)
    return () => clearInterval(timer)
  }, [words.length, reduce])
  return (
    <span className="sc-rotator" aria-hidden="true">
      <AnimatePresence initial={false}>
        <motion.span
          key={words[index]}
          initial={{ y: '100%', opacity: 0, filter: 'blur(6px)' }}
          animate={{ y: '0%', opacity: 1, filter: 'blur(0px)' }}
          exit={{ y: '-100%', opacity: 0, filter: 'blur(6px)' }}
          transition={{ duration: 0.6, ease: EASE }}
        >
          {words[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

// ------------------------------------------------------------- showcase
const ROTATING = ['prepared.', 'confident.', 'ready.']

function Showcase() {
  const ref = useRef(null)
  const reduce = useReducedMotion()
  const onMove = (event) => {
    if (reduce || !ref.current) return
    const box = ref.current.getBoundingClientRect()
    ref.current.style.setProperty('--px', ((event.clientX - box.left) / box.width - 0.5).toFixed(3))
    ref.current.style.setProperty('--py', ((event.clientY - box.top) / box.height - 0.5).toFixed(3))
  }
  return (
    <aside className="auth-showcase" ref={ref} onPointerMove={onMove}>
      <div className="sc-aurora" aria-hidden="true">
        <i />
        <i />
        <i />
      </div>
      <div className="sc-grid" aria-hidden="true" />
      <div className="sc-inner">
        <Link to="/login" className="sc-brand" aria-label="InstantInterviewPrep">
          <BrandMark />
          <span>
            Instant<b>Interview</b>Prep
          </span>
        </Link>

        <motion.div className="sc-copy" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE, delay: 0.1 }}>
          <span className="sc-kicker">
            <Sparkles size={14} /> Your AI interview coach
          </span>
          <h1>
            Walk into your next interview <span className="sr-only">prepared, confident and ready.</span>
            <RotatingWord words={ROTATING} />
          </h1>
          <p>
            Share your resume, the job description and the company. The agent researches how they interview and builds your
            personal prep kit in minutes.
          </p>
        </motion.div>

        <div className="sc-stage" aria-hidden="true">
          <div className="sc-card sc-agent" style={{ '--depth': 1.4 }}>
            <div className="sc-float">
              <div className="sc-agent-head">
                <svg className="sc-ring" viewBox="0 0 44 44">
                  <circle cx="22" cy="22" r="18" />
                  <circle cx="22" cy="22" r="18" className="fill" />
                </svg>
                <div>
                  <strong>Researching interviews</strong>
                  <small>Live agent · sources kept</small>
                </div>
              </div>
              <ul className="sc-steps">
                <li>
                  <Globe size={13} /> Reading interview experiences
                </li>
                <li>
                  <ListChecks size={13} /> Planning 10 topics for your JD
                </li>
                <li>
                  <LayoutDashboard size={13} /> Writing 79 questions
                </li>
              </ul>
            </div>
          </div>
          <div className="sc-card sc-hot" style={{ '--depth': 2.2 }}>
            <div className="sc-float" style={{ animationDelay: '-2.2s' }}>
              <span className="sc-flame">
                <Flame size={16} />
              </span>
              <div>
                <strong>Explain the bias-variance trade-off</strong>
                <small>Hot · asked in technical rounds</small>
              </div>
            </div>
          </div>
          <div className="sc-card sc-score" style={{ '--depth': 1.8 }}>
            <div className="sc-float" style={{ animationDelay: '-4s' }}>
              <span className="sc-score-ring">
                92<small>%</small>
              </span>
              <div>
                <strong>Quiz score</strong>
                <small>23 of 25 correct</small>
              </div>
            </div>
          </div>
          <div className="sc-card sc-ready" style={{ '--depth': 1 }}>
            <div className="sc-float" style={{ animationDelay: '-1s' }}>
              <div className="sc-ready-top">
                <span>Interview readiness</span>
                <b>78%</b>
              </div>
              <span className="sc-meter">
                <i />
              </span>
            </div>
          </div>
        </div>

        <ul className="sc-points">
          <li>
            <LayoutDashboard size={16} /> 5 study dashboards
          </li>
          <li>
            <ListChecks size={16} /> 50+ questions per kit
          </li>
          <li>
            <Globe size={16} /> Company research
          </li>
        </ul>
      </div>
    </aside>
  )
}

// ---------------------------------------------------------------- views
function ModeSwitch({ view, search }) {
  return (
    <nav className="auth-switch" aria-label="Sign in or create an account">
      {[
        { key: 'signin', to: '/login', label: 'Sign in' },
        { key: 'signup', to: '/signup', label: 'Create account' },
      ].map((tab) => (
        <Link key={tab.key} to={{ pathname: tab.to, search }} replace className={view === tab.key ? 'on' : ''} aria-current={view === tab.key ? 'page' : undefined}>
          {view === tab.key && <motion.span layoutId="auth-switch-pill" className="auth-switch-pill" transition={{ type: 'spring', stiffness: 480, damping: 38 }} />}
          <span>{tab.label}</span>
        </Link>
      ))}
    </nav>
  )
}

/** After a successful sign-in: let the success state show, then hand over to the app. */
function useFinish() {
  const location = useLocation()
  const { setSignedIn } = useAuth()
  const { notify } = useApp()
  return useCallback(
    (user, { welcome, fallback = '/' }) => {
      const hasNext = new URLSearchParams(location.search).has('next')
      const target = hasNext ? nextPath(location.search) : fallback
      setTimeout(() => {
        setSignedIn(user, target)
        notify(welcome)
      }, 650)
    },
    [location.search, setSignedIn, notify],
  )
}

function CredentialsView({ view }) {
  const signup = view === 'signup'
  const location = useLocation()
  const navigate = useNavigate()
  const { config } = useAuth()
  const finish = useFinish()
  const form = useFormState({ first_name: '', last_name: '', email: '', password: '', remember: true })
  const { values, set, errors, busy, done } = form
  const { setFormError } = form
  const next = new URLSearchParams(location.search).get('next') || ''

  // a Google sign-in that didn't complete comes back here with ?error=
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const code = params.get('error')
    if (!code) return
    setFormError(SIGN_IN_ERRORS[code] || 'Sign-in didn’t complete. Please try again.')
    params.delete('error')
    navigate({ pathname: location.pathname, search: params.toString() ? `?${params}` : '' }, { replace: true })
  }, [location.search, location.pathname, navigate, setFormError])

  const succeed = (user, isNew) => {
    form.setDone(true)
    finish(user, {
      welcome: isNew ? `Welcome, ${user.first_name}! Let's build your first prep kit.` : `Welcome back, ${user.first_name}.`,
      fallback: isNew ? '/new' : '/',
    })
  }

  const validate = () => {
    const e = {}
    if (signup) {
      if (!values.first_name.trim()) e.first_name = 'Enter your first name.'
      if (!values.last_name.trim()) e.last_name = 'Enter your last name.'
    }
    if (!values.email.trim()) e.email = 'Enter your email address.'
    else if (!EMAIL_RE.test(values.email.trim())) e.email = 'Enter a valid email address.'
    if (!values.password) e.password = signup ? 'Create a password.' : 'Enter your password.'
    else if (signup) {
      const missing = passwordRules(values.password, values.email).find((r) => !r.ok)
      if (missing) e.password = `Your password needs: ${missing.label.toLowerCase()}.`
    }
    return e
  }

  const submit = async (event) => {
    event.preventDefault()
    if (busy || done) return
    const problems = validate()
    if (Object.keys(problems).length) return form.fail(problems)
    form.setBusy(true)
    try {
      const body = signup
        ? await api.register({ ...values, email: values.email.trim(), remember: true })
        : await api.login({ email: values.email.trim(), password: values.password, remember: values.remember })
      succeed(body.user, body.new_account)
    } catch (error) {
      form.failFromServer(error)
      form.setBusy(false)
    }
  }

  return (
    <motion.div key="credentials" {...swap}>
      <div className="auth-head">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={view} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.22 }}>
            <h2>{signup ? 'Create your account' : 'Welcome back'}</h2>
            <p>{signup ? 'Start preparing in under a minute. It’s free.' : 'Sign in to continue your interview prep.'}</p>
          </motion.div>
        </AnimatePresence>
      </div>

      <ModeSwitch view={view} search={location.search} />

      <FormAlert message={form.formError} />

      <motion.form className="auth-form" onSubmit={submit} noValidate animate={form.controls}>
        <AnimatePresence initial={false}>
          {signup && (
            <motion.div
              className="name-row"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: EASE }}
            >
              <Field
                id="first_name"
                label="First name"
                icon={UserRound}
                value={values.first_name}
                onChange={set('first_name')}
                error={errors.first_name}
                autoComplete="given-name"
                maxLength={60}
              />
              <Field
                id="last_name"
                label="Last name"
                icon={UserRound}
                value={values.last_name}
                onChange={set('last_name')}
                error={errors.last_name}
                autoComplete="family-name"
                maxLength={60}
              />
            </motion.div>
          )}
        </AnimatePresence>

        <Field
          id="email"
          label="Email address"
          icon={Mail}
          type="email"
          inputMode="email"
          value={values.email}
          onChange={set('email')}
          error={errors.email}
          autoComplete="email"
          maxLength={320}
          spellCheck={false}
          autoCapitalize="none"
        />

        <PasswordField
          value={values.password}
          onChange={set('password')}
          error={errors.password}
          autoComplete={signup ? 'new-password' : 'current-password'}
        >
          {signup && <StrengthMeter password={values.password} email={values.email} />}
        </PasswordField>

        {!signup && (
          <div className="auth-row">
            <label className="check">
              <input type="checkbox" checked={values.remember} onChange={set('remember')} />
              <span className="check-box" aria-hidden="true">
                <Check size={12} strokeWidth={3.2} />
              </span>
              Keep me signed in
            </label>
            <Link to={{ pathname: '/forgot-password', search: values.email ? `?email=${encodeURIComponent(values.email.trim())}` : '' }} className="auth-link">
              Forgot password?
            </Link>
          </div>
        )}

        <SubmitButton busy={busy} done={done} busyLabel={signup ? 'Creating your account…' : 'Signing in…'} doneLabel={signup ? 'Account created' : 'Signed in'}>
          {signup ? 'Create account' : 'Sign in'} <ArrowRight size={18} />
        </SubmitButton>
      </motion.form>

      <div className="auth-divider">
        <span>or</span>
      </div>
      <GoogleSignIn
        label={signup ? 'Sign up with Google' : 'Continue with Google'}
        next={next}
        remember={signup || values.remember}
        enabled={config.google_enabled}
        onUnavailable={() => setFormError(SIGN_IN_ERRORS.google_unavailable)}
      />

      <p className="auth-alt">
        {signup ? 'Already have an account?' : 'New to InstantInterviewPrep?'}{' '}
        <Link to={{ pathname: signup ? '/login' : '/signup', search: location.search }} replace className="auth-link">
          {signup ? 'Sign in' : 'Create a free account'}
        </Link>
      </p>
    </motion.div>
  )
}

function ForgotView() {
  const location = useLocation()
  const { config } = useAuth()
  const form = useFormState({ email: new URLSearchParams(location.search).get('email') || '' })
  const { values, set, errors, busy } = form
  const [sentTo, setSentTo] = useState('')
  const [cooldown, setCooldown] = useState(0)

  useEffect(() => {
    if (!cooldown) return undefined
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000)
    return () => clearTimeout(timer)
  }, [cooldown])

  const send = async (event) => {
    event?.preventDefault()
    const email = values.email.trim()
    if (!email) return form.fail({ email: 'Enter the email you signed up with.' })
    if (!EMAIL_RE.test(email)) return form.fail({ email: 'Enter a valid email address.' })
    form.setBusy(true)
    try {
      await api.forgotPassword(email)
      setSentTo(email)
      setCooldown(30)
    } catch (error) {
      form.failFromServer(error)
    } finally {
      form.setBusy(false)
    }
  }

  return (
    <motion.div key="forgot" {...swap}>
      <AnimatePresence mode="wait" initial={false}>
        {sentTo ? (
          <motion.div key="sent" className="auth-state" {...swap}>
            <span className="state-icon ok">
              <MailCheck size={30} />
            </span>
            <h2>Check your inbox</h2>
            <p>
              If an account exists for <strong>{sentTo}</strong>, we’ve sent a link to reset your password. It expires in 60 minutes.
            </p>
            {!config.email_delivery && (
              <p className="field-note warn center">Email delivery isn’t set up on this server yet, so the link was written to the server log.</p>
            )}
            <button type="button" className="btn btn-block" onClick={send} disabled={busy || cooldown > 0}>
              {busy ? <LoaderCircle size={17} className="spin" /> : <Mail size={17} />}
              {cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend the link'}
            </button>
            <Link to="/login" className="auth-back">
              <ArrowLeft size={16} /> Back to sign in
            </Link>
          </motion.div>
        ) : (
          <motion.div key="ask" {...swap}>
            <span className="state-icon">
              <KeyRound size={28} />
            </span>
            <div className="auth-head">
              <h2>Forgot your password?</h2>
              <p>Enter the email you use for InstantInterviewPrep and we’ll send you a link to choose a new one.</p>
            </div>
            <FormAlert message={form.formError} />
            <motion.form className="auth-form" onSubmit={send} noValidate animate={form.controls}>
              <Field
                id="email"
                label="Email address"
                icon={Mail}
                type="email"
                inputMode="email"
                value={values.email}
                onChange={set('email')}
                error={errors.email}
                autoComplete="email"
                autoCapitalize="none"
                spellCheck={false}
                autoFocus
              />
              <SubmitButton busy={busy} done={false} busyLabel="Sending…">
                Send reset link <ArrowRight size={18} />
              </SubmitButton>
            </motion.form>
            <Link to="/login" className="auth-back">
              <ArrowLeft size={16} /> Back to sign in
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ResetView() {
  const location = useLocation()
  const finish = useFinish()
  // read the token once, then drop it from the address bar and history
  const [token] = useState(() => new URLSearchParams(location.search).get('token') || '')
  const [check, setCheck] = useState({ state: token ? 'checking' : 'invalid', email: '' })
  const form = useFormState({ password: '', confirm: '' })
  const { values, set, errors, busy, done } = form

  useEffect(() => {
    window.history.replaceState(window.history.state, '', '/reset-password')
    if (!token) return undefined
    let alive = true
    api
      .checkResetToken(token)
      .then((body) => alive && setCheck({ state: body.valid ? 'valid' : 'invalid', email: body.email || '' }))
      .catch(() => alive && setCheck({ state: 'error', email: '' }))
    return () => {
      alive = false
    }
  }, [token])

  const submit = async (event) => {
    event.preventDefault()
    if (busy || done) return
    const problems = {}
    const missing = passwordRules(values.password, check.email).find((r) => !r.ok)
    if (!values.password) problems.password = 'Choose a new password.'
    else if (missing) problems.password = `Your password needs: ${missing.label.toLowerCase()}.`
    if (!problems.password && values.confirm !== values.password) problems.confirm = 'The passwords don’t match.'
    if (Object.keys(problems).length) return form.fail(problems)
    form.setBusy(true)
    try {
      const body = await api.resetPassword({ token, password: values.password, remember: true })
      form.setDone(true)
      finish(body.user, { welcome: 'Your password is updated and you’re signed in.' })
    } catch (error) {
      if (error.field === 'token') setCheck({ state: 'invalid', email: '' })
      else form.failFromServer(error)
      form.setBusy(false)
    }
  }

  return (
    <motion.div key="reset" {...swap}>
      <AnimatePresence mode="wait" initial={false}>
        {check.state === 'checking' && (
          <motion.div key="checking" className="auth-state" {...swap} role="status">
            <span className="state-icon">
              <LoaderCircle size={28} className="spin" />
            </span>
            <h2>Checking your link…</h2>
          </motion.div>
        )}
        {(check.state === 'invalid' || check.state === 'error') && (
          <motion.div key="invalid" className="auth-state" {...swap}>
            <span className="state-icon bad">
              <TriangleAlert size={28} />
            </span>
            <h2>{check.state === 'error' ? 'We couldn’t check this link' : 'This link has expired'}</h2>
            <p>
              {check.state === 'error'
                ? 'Check your connection and open the link from your email again.'
                : 'Reset links work once and expire after 60 minutes. Request a new one and use the latest email.'}
            </p>
            <Link to="/forgot-password" className="btn btn-primary btn-lg btn-block">
              Request a new link <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="auth-back">
              <ArrowLeft size={16} /> Back to sign in
            </Link>
          </motion.div>
        )}
        {check.state === 'valid' && (
          <motion.div key="form" {...swap}>
            <span className="state-icon">
              <ShieldCheck size={28} />
            </span>
            <div className="auth-head">
              <h2>Choose a new password</h2>
              <p>
                For <strong>{check.email}</strong>. You’ll be signed out on other devices.
              </p>
            </div>
            <FormAlert message={form.formError} />
            <motion.form className="auth-form" onSubmit={submit} noValidate animate={form.controls}>
              <input type="email" name="email" autoComplete="username" value={check.email} readOnly hidden />
              <PasswordField label="New password" value={values.password} onChange={set('password')} error={errors.password} autoComplete="new-password">
                <StrengthMeter password={values.password} email={check.email} />
              </PasswordField>
              <PasswordField id="confirm" label="Confirm new password" value={values.confirm} onChange={set('confirm')} error={errors.confirm} autoComplete="new-password" />
              <SubmitButton busy={busy} done={done} busyLabel="Saving…" doneLabel="Password updated">
                Update password <ArrowRight size={18} />
              </SubmitButton>
            </motion.form>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ------------------------------------------------------------------ page
export default function AuthPage({ view }) {
  const [theme, toggleTheme] = useTheme()
  const cardRef = useRef(null)
  const reduce = useReducedMotion()

  useEffect(() => {
    document.title = `${TITLES[view]} · InstantInterviewPrep`
    return () => {
      document.title = 'InstantInterviewPrep · AI interview prep agent'
    }
  }, [view])

  const spotlight = (event) => {
    if (reduce || !cardRef.current) return
    const box = cardRef.current.getBoundingClientRect()
    cardRef.current.style.setProperty('--mx', `${event.clientX - box.left}px`)
    cardRef.current.style.setProperty('--my', `${event.clientY - box.top}px`)
  }

  const credentials = view === 'signin' || view === 'signup'
  const themeLabel = `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`
  const year = useMemo(() => new Date().getFullYear(), [])

  return (
    <div className="auth">
      <Showcase />
      <main className="auth-panel">
        <div className="auth-panel-bg" aria-hidden="true" />
        <div className="auth-topline">
          <Link to="/login" className="auth-mobile-brand" aria-label="InstantInterviewPrep">
            <BrandMark />
            <span>
              Instant<b>Interview</b>Prep
            </span>
          </Link>
          <button className="icon-btn theme-toggle" onClick={toggleTheme} aria-label={themeLabel} title={themeLabel}>
            <AnimatePresence mode="wait" initial={false}>
              <motion.span
                key={theme}
                initial={{ rotate: -90, opacity: 0, scale: 0.6 }}
                animate={{ rotate: 0, opacity: 1, scale: 1 }}
                exit={{ rotate: 90, opacity: 0, scale: 0.6 }}
                transition={{ duration: 0.25 }}
                style={{ display: 'grid' }}
              >
                {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </motion.span>
            </AnimatePresence>
          </button>
        </div>

        <div className="auth-center">
          <p className="auth-mobile-tag">
            <Sparkles size={14} /> Your AI interview coach
          </p>
          <motion.div
            ref={cardRef}
            className="auth-card"
            onPointerMove={spotlight}
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.55, ease: EASE }}
            layout
          >
            <AnimatePresence mode="wait" initial={false}>
              {credentials && <CredentialsView key="credentials" view={view} />}
              {view === 'forgot' && <ForgotView key="forgot" />}
              {view === 'reset' && <ResetView key="reset" />}
            </AnimatePresence>
          </motion.div>
          <p className="auth-trust">
            <ShieldCheck size={15} aria-hidden="true" />
            Passwords are stored only as secure hashes, and your prep kits are private to your account.
          </p>
        </div>
        <footer className="auth-footer">© {year} InstantInterviewPrep</footer>
      </main>
    </div>
  )
}
