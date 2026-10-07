import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { History, Menu, Moon, Plus, Sun, X, Zap } from 'lucide-react'
import { useApp, useTheme } from '../context.jsx'
import { ModeBadge } from './Badges.jsx'

export function BrandMark({ size = 18 }) {
  return (
    <span className="brand-mark" aria-hidden="true">
      <Zap size={size} fill="currentColor" strokeWidth={1.6} />
    </span>
  )
}

export function Brand() {
  return (
    <Link to="/" className="brand" aria-label="InstantInterviewPrep home">
      <BrandMark />
      <span className="brand-word">
        Instant<b>Interview</b>Prep
      </span>
    </Link>
  )
}

const LANDING_LINKS = [
  { href: '#how', label: 'How it works' },
  { href: '#dashboards', label: 'Dashboards' },
  { href: '#faq', label: 'FAQ' },
]

export default function TopBar() {
  const { health } = useApp()
  const [theme, toggleTheme] = useTheme()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const onLanding = location.pathname === '/'
  const onNew = location.pathname === '/new'

  useEffect(() => setOpen(false), [location.pathname])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const links = onLanding ? LANDING_LINKS : []
  const themeLabel = `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`

  return (
    <header className={`topbar no-print ${onLanding && !scrolled && !open ? 'at-top' : ''} ${scrolled ? 'scrolled' : ''}`}>
      <div className="topbar-inner">
        <Brand />
        <nav className="nav-links" aria-label="Main">
          {links.map((l) => (
            <a key={l.href} className="nav-link" href={l.href}>
              {l.label}
            </a>
          ))}
          <NavLink to="/preps" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <History size={16} /> My prep kits
          </NavLink>
        </nav>
        <div className="topbar-right">
          {health && (
            <span className="desktop-only">
              <ModeBadge mode={health.mode} />
            </span>
          )}
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
          {!onNew && (
            <Link to="/new" className="btn btn-primary btn-sm desktop-only">
              <Plus size={16} /> New prep kit
            </Link>
          )}
          <button
            className="icon-btn menu-toggle"
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.nav
            id="mobile-menu"
            className="mobile-menu"
            aria-label="Mobile"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22 }}
          >
            {links.map((l) => (
              <a key={l.href} className="nav-link" href={l.href} onClick={() => setOpen(false)}>
                {l.label}
              </a>
            ))}
            <NavLink to="/preps" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <History size={17} /> My prep kits
            </NavLink>
            <div className="menu-foot">
              {!onNew && (
                <Link to="/new" className="btn btn-primary btn-lg btn-block">
                  <Plus size={17} /> New prep kit
                </Link>
              )}
              {health && (
                <div className="row" style={{ justifyContent: 'center' }}>
                  <ModeBadge mode={health.mode} />
                </div>
              )}
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
