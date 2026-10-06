import { NavLink, Link } from 'react-router-dom'
import { History, Moon, Plus, Sun, Zap } from 'lucide-react'
import { useApp, useTheme } from '../context.jsx'
import { ModeBadge } from './Badges.jsx'

export default function TopBar() {
  const { health } = useApp()
  const [theme, toggleTheme] = useTheme()
  return (
    <header className="topbar">
      <Link to="/" className="brand" aria-label="InstantInterviewPrep home">
        <span className="brand-mark">
          <Zap size={17} />
        </span>
        <span>
          InstantInterviewPrep
          <small>AI interview research agent</small>
        </span>
      </Link>
      <nav className="topnav" aria-label="Main">
        <NavLink to="/" end>
          <Plus size={15} style={{ verticalAlign: '-2px', marginRight: 4 }} />
          <span className="label">New prep</span>
        </NavLink>
        <NavLink to="/preps">
          <History size={15} style={{ verticalAlign: '-2px', marginRight: 4 }} />
          <span className="label">My preps</span>
        </NavLink>
      </nav>
      <div className="topbar-right">
        {health && <ModeBadge mode={health.mode} />}
        <button className="icon-btn" onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
    </header>
  )
}
