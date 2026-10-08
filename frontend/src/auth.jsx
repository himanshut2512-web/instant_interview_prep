import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { api, UNAUTHORIZED_EVENT } from './api.js'

const AuthContext = createContext(null)

/**
 * Who is signed in. status: 'loading' | 'signed-in' | 'signed-out'.
 * The session itself is an httpOnly cookie; this only mirrors the user record.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')
  const [landing, setLanding] = useState(null)
  const [signedOutOnPurpose, setSignedOutOnPurpose] = useState(false)
  const [config, setConfig] = useState({ google_enabled: false, email_delivery: false, email_sender: null, setup_hints: false })

  // settle both before leaving 'loading', so the sign-in page renders with the right options at once
  useEffect(() => {
    let alive = true
    Promise.allSettled([api.me(), api.authConfig()]).then(([me, settings]) => {
      if (!alive) return
      if (settings.status === 'fulfilled') setConfig(settings.value)
      if (me.status === 'fulfilled') {
        setUser(me.value.user)
        setStatus('signed-in')
      } else {
        setUser(null)
        setStatus('signed-out')
      }
    })
    return () => {
      alive = false
    }
  }, [])

  // any API call that comes back 401 means the session expired or was revoked
  useEffect(() => {
    const onUnauthorized = () => {
      setUser(null)
      setStatus('signed-out')
    }
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized)
  }, [])

  // The sign-in page calls this once its success animation has played. It does
  // not navigate itself: the sign-in routes' guard sends the user to `to`, so
  // there is exactly one redirect and nothing to race.
  const setSignedIn = useCallback((nextUser, to = null) => {
    setLanding(to)
    setSignedOutOnPurpose(false)
    setUser(nextUser)
    setStatus('signed-in')
  }, [])

  const value = useMemo(
    () => ({
      user,
      status,
      config,
      landing,
      signedOutOnPurpose,
      setSignedIn,
      clearLanding: () => setLanding(null),
      logout: async () => {
        try {
          await api.logout()
        } finally {
          setLanding(null)
          setSignedOutOnPurpose(true)
          setUser(null)
          setStatus('signed-out')
        }
      },
    }),
    [user, status, config, landing, signedOutOnPurpose, setSignedIn],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthSplash() {
  return (
    <div className="auth-splash" role="status">
      <span className="loader-orb">
        <Zap size={22} fill="currentColor" strokeWidth={1.6} />
      </span>
      <span className="sr-only">Loading…</span>
    </div>
  )
}

/** Only signed-in users get past this; others go to sign-in and come back afterwards. */
export function RequireAuth({ children }) {
  const { status, landing, clearLanding, signedOutOnPurpose } = useAuth()
  const location = useLocation()
  // the post-sign-in destination has been reached; forget it
  useEffect(() => {
    if (status === 'signed-in' && landing) clearLanding()
  }, [status, landing, clearLanding])
  if (status === 'loading') return <AuthSplash />
  if (status === 'signed-out') {
    // an expired session brings you back here after signing in; signing out does not
    const here = location.pathname + location.search + location.hash
    const next = here === '/' || signedOutOnPurpose ? '' : `?next=${encodeURIComponent(here)}`
    return <Navigate to={`/login${next}`} replace />
  }
  return children
}

/** Where to go after signing in: a safe in-app path from ?next=, else home. */
export function nextPath(search) {
  const next = new URLSearchParams(search).get('next') || ''
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

/**
 * Sign-in pages: signed-in visitors skip straight to the app, and a sign-in
 * that just finished here goes where the page asked (`landing`).
 * allowSignedIn keeps the page open for already signed-in visitors (reset links).
 */
export function GuestOnly({ children, allowSignedIn = false }) {
  const { status, landing } = useAuth()
  const location = useLocation()
  if (status === 'loading') return <AuthSplash />
  if (status === 'signed-in' && (landing || !allowSignedIn)) {
    return <Navigate to={landing || nextPath(location.search)} replace />
  }
  return children
}
