import { Link, Route, Routes } from 'react-router-dom'
import { AppProvider } from './context.jsx'
import TopBar from './components/TopBar.jsx'
import NewPrep from './pages/NewPrep.jsx'
import History from './pages/History.jsx'
import Workspace from './pages/Workspace.jsx'
import PrintView from './pages/PrintView.jsx'

function NotFound() {
  return (
    <main className="page">
      <div className="card empty">
        <h2>Page not found</h2>
        <Link to="/" className="btn btn-primary">
          Go to the start page
        </Link>
      </div>
    </main>
  )
}

export default function App() {
  return (
    <AppProvider>
      <TopBar />
      <Routes>
        <Route path="/" element={<NewPrep />} />
        <Route path="/preps" element={<History />} />
        <Route path="/prep/:id/print" element={<PrintView />} />
        <Route path="/prep/:id/*" element={<Workspace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AppProvider>
  )
}
