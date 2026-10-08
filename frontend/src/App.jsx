import { lazy, Suspense, useEffect } from 'react'
import { Link, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { Compass, Home, Zap } from 'lucide-react'
import { AppProvider, useApp } from './context.jsx'
import { AuthProvider, GuestOnly, RequireAuth, useAuth } from './auth.jsx'
import TopBar from './components/TopBar.jsx'
import Landing from './pages/Landing.jsx'
import AuthPage from './pages/AuthPage.jsx'
import { EmptyState } from './components/UI.jsx'
import { Page } from './components/Motion.jsx'

// Sign-in and the home page load instantly; the app screens (and the
// Markdown/code highlighting they need) load on demand.
const NewPrep = lazy(() => import('./pages/NewPrep.jsx'))
const History = lazy(() => import('./pages/History.jsx'))
const Workspace = lazy(() => import('./pages/Workspace.jsx'))
const PrintView = lazy(() => import('./pages/PrintView.jsx'))

function Loader() {
  return (
    <div className="center-loader" role="status">
      <span className="loader-orb">
        <Zap size={22} fill="currentColor" strokeWidth={1.6} />
      </span>
      <span>Loading…</span>
    </div>
  )
}

/** Scroll to the top on page changes, or to #anchors when the URL has one. */
function ScrollManager() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (hash) {
      const timer = setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth' }), 60)
      return () => clearTimeout(timer)
    }
    if (!pathname.startsWith('/prep/')) window.scrollTo({ top: 0 })
    return undefined
  }, [pathname, hash])
  return null
}

function NotFound() {
  return (
    <main className="page">
      <EmptyState
        icon={Compass}
        title="Page not found"
        text="The page you are looking for does not exist or was moved."
        action={
          <Link to="/" className="btn btn-primary">
            <Home size={16} /> Go home
          </Link>
        }
      />
    </main>
  )
}

/** After Google sign-in the server adds ?welcome=new|back: greet once, then drop it from the URL. */
function WelcomeNotice() {
  const { user } = useAuth()
  const { notify } = useApp()
  const location = useLocation()
  const navigate = useNavigate()
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const welcome = params.get('welcome')
    if (!welcome || !user) return
    notify(welcome === 'new' ? `Welcome, ${user.first_name}! Let's build your first prep kit.` : `Welcome back, ${user.first_name}.`)
    params.delete('welcome')
    navigate({ pathname: location.pathname, search: params.toString() ? `?${params}` : '', hash: location.hash }, { replace: true })
  }, [location, user, notify, navigate])
  return null
}

/** Signed-in screens: top bar + page. */
function AppShell() {
  return (
    <>
      <WelcomeNotice />
      <TopBar />
      <div className="app-main">
        <Suspense fallback={<Loader />}>
          <Outlet />
        </Suspense>
      </div>
    </>
  )
}

export default function App() {
  return (
    <AppProvider>
      <AuthProvider>
        <ScrollManager />
        <Routes>
          <Route
            path="/login"
            element={
              <GuestOnly>
                <AuthPage view="signin" />
              </GuestOnly>
            }
          />
          <Route
            path="/signup"
            element={
              <GuestOnly>
                <AuthPage view="signup" />
              </GuestOnly>
            }
          />
          <Route
            path="/forgot-password"
            element={
              <GuestOnly>
                <AuthPage view="forgot" />
              </GuestOnly>
            }
          />
          <Route
            path="/reset-password"
            element={
              <GuestOnly allowSignedIn>
                <AuthPage view="reset" />
              </GuestOnly>
            }
          />
          <Route
            element={
              <RequireAuth>
                <AppShell />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Landing />} />
            <Route
              path="/new"
              element={
                <Page>
                  <NewPrep />
                </Page>
              }
            />
            <Route
              path="/preps"
              element={
                <Page>
                  <History />
                </Page>
              }
            />
            <Route path="/prep/:id/print" element={<PrintView />} />
            <Route path="/prep/:id/*" element={<Workspace />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AuthProvider>
    </AppProvider>
  )
}
