import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { CircleAlert, CircleCheck } from 'lucide-react'
import { api } from './api.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [health, setHealth] = useState(null)
  const [healthError, setHealthError] = useState(null)
  const [toasts, setToasts] = useState([])
  const nextId = useRef(1)

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e) => setHealthError(e.message))
  }, [])

  const notify = useCallback((message, kind = 'info') => {
    const id = nextId.current++
    setToasts((list) => [...list, { id, message, kind }])
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), kind === 'error' ? 7000 : 4000)
  }, [])

  const value = useMemo(() => ({ health, healthError, notify }), [health, healthError, notify])

  return (
    <AppContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind === 'error' ? 'error' : ''}`}>
            {t.kind === 'error' ? <CircleAlert size={18} /> : <CircleCheck size={18} />}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
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
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      /* storage unavailable */
    }
  }, [theme])

  return [theme, () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))]
}
