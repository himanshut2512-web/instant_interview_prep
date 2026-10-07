import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { CircleAlert, CircleCheck, TriangleAlert, X } from 'lucide-react'
import { api } from './api.js'
import Dialog from './components/Dialog.jsx'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [toasts, setToasts] = useState([])
  const [confirmState, setConfirmState] = useState(null)
  const nextId = useRef(1)

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e) => setHealthError(e.message))
  }, [])

  const dismiss = useCallback((id) => setToasts((list) => list.filter((t) => t.id !== id)), [])

  const notify = useCallback(
    (message, kind = 'info') => {
      const id = nextId.current++
      const duration = kind === 'error' ? 7000 : 4000
      setToasts((list) => [...list.slice(-3), { id, message, kind, duration }])
      setTimeout(() => dismiss(id), duration)
    },
    [dismiss],
  )

  /** Promise-based replacement for window.confirm. */
  const confirm = useCallback(
    (options) =>
      new Promise((resolve) => {
        setConfirmState({ ...options, resolve })
      }),
    [],
  )

  const closeConfirm = (result) => {
    confirmState?.resolve(result)
    setConfirmState(null)
  }

  const value = useMemo(() => ({ health, healthError, notify, confirm }), [health, healthError, notify, confirm])

  return (
    <AppContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        <AnimatePresence initial={false}>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              layout
              className={`toast ${t.kind === 'error' ? 'error' : ''}`}
              initial={{ opacity: 0, y: 24, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, transition: { duration: 0.2 } }}
              transition={{ type: 'spring', stiffness: 420, damping: 32 }}
            >
              {t.kind === 'error' ? <CircleAlert size={18} /> : <CircleCheck size={18} />}
              <span>{t.message}</span>
              <button className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss notification">
                <X size={16} />
              </button>
              <motion.span
                className="toast-timer"
                initial={{ scaleX: 1 }}
                animate={{ scaleX: 0 }}
                transition={{ duration: t.duration / 1000, ease: 'linear' }}
                style={{ width: '100%' }}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      <Dialog open={Boolean(confirmState)} onClose={() => closeConfirm(false)} labelledBy="confirm-title" width={440}>
        {confirmState && (
          <>
            <div className={`confirm-icon ${confirmState.tone === 'danger' ? 'danger' : ''}`} aria-hidden="true">
              {confirmState.tone === 'danger' ? <TriangleAlert size={22} /> : <CircleAlert size={22} />}
            </div>
            <h2 id="confirm-title" style={{ fontSize: '1.2rem', marginBottom: 6 }}>
              {confirmState.title}
            </h2>
            {confirmState.message && <p className="muted" style={{ margin: 0 }}>{confirmState.message}</p>}
            <div className="dialog-foot">
              <button className="btn" onClick={() => closeConfirm(false)}>
                {confirmState.cancelLabel || 'Cancel'}
              </button>
              <button
                className={`btn ${confirmState.tone === 'danger' ? 'btn-danger-solid' : 'btn-primary'}`}
                onClick={() => closeConfirm(true)}
                data-autofocus
              >
                {confirmState.confirmLabel || 'Confirm'}
              </button>
            </div>
          </>
        )}
      </Dialog>
    </AppContext.Provider>
  )
}

export function useApp() {
  return useContext(AppContext)
}

// ------------------------------------------------------------------ theme
const THEME_KEY = 'iip-theme'

function systemPrefersDark() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches
}

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY)
      if (saved === 'light' || saved === 'dark') return saved
    } catch {
      /* storage unavailable */
    }
    return systemPrefersDark() ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#090c17' : '#f5f6fa')
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      /* storage unavailable */
    }
  }, [theme])

  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}
