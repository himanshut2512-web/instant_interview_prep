import { lazy, Suspense, useEffect } from 'react'
import { Link, Route, Routes, useLocation } from 'react-router-dom'
import { Compass, Home, Zap } from 'lucide-react'
import { AppProvider } from './context.jsx'
import TopBar from './components/TopBar.jsx'
import Landing from './pages/Landing.jsx'
import { EmptyState } from './components/UI.jsx'
import { Page } from './components/Motion.jsx'

// The landing page loads instantly; the app screens (and the Markdown/code
// highlighting they need) load on demand.
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

export default function App() {
  return (
    <AppProvider>
      <ScrollManager />
      <TopBar />
      <div className="app-main">
        <Suspense fallback={<Loader />}>
          <Routes>
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
          </Routes>
        </Suspense>
      </div>
    </AppProvider>
  )
}
