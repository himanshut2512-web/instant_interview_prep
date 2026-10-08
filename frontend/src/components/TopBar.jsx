import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { ChevronDown, History, LogOut, Menu, Moon, Plus, Sun, X, Zap } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { useApp, useTheme } from '../context.jsx'
import { avatarStyle, initials } from '../lib/format.js'
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

export function UserAvatar({ user, size = 34 }) {
  const name = `${user.first_name} ${user.last_name}`.trim()
  const [broken, setBroken] = useState(false)
  if (user.avatar_url && !broken) {
    return (
      <img
        className="user-avatar"
        src={user.avatar_url}
        alt=""
        width={size}
        height={size}
        referrerPolicy="no-referrer"
        onError={() => setBroken(true)}
      />
    )
  }
  return (
    <span className="user-avatar" style={{ ...avatarStyle(name || user.email), width: size, height: size }} aria-hidden="true">
      {initials(name || user.email)}
    </span>
  )
}

/** Sign out; the route guard then shows the sign-in page. */
function useSignOut() {
  const { logout } = useAuth()
  const { notify } = useApp()
  return async () => {
    await logout()
    notify('You’re signed out.')
  }
}

function UserMenu({ user }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  const signOut = useSignOut()
  const location = useLocation()

  useEffect(() => setOpen(false), [location.pathname])
  useEffect(() => {
    if (!open) return undefined
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false)
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="menu-wrap user-menu" ref={ref}>
      <button className="user-trigger" aria-label="Account menu" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <UserAvatar user={user} />
        <ChevronDown size={15} className="user-chevron" aria-hidden="true" />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            className="menu user-dropdown"
            role="menu"
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.16 }}
          >
            <div className="user-card">
              <UserAvatar user={user} size={40} />
              <div>
                <strong>
                  {user.first_name} {user.last_name}
                </strong>
                <span>{user.email}</span>
              </div>
            </div>
            <div className="menu-sep" />
            <Link className="menu-item" role="menuitem" to="/preps">
              <History size={16} /> My prep kits
            </Link>
            <Link className="menu-item" role="menuitem" to="/new">
              <Plus size={16} /> New prep kit
            </Link>
            <div className="menu-sep" />
            <button className="menu-item" role="menuitem" onClick={signOut}>
              <LogOut size={16} /> Sign out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

const LANDING_LINKS = [
  { href: '#how', label: 'How it works' },
  { href: '#dashboards', label: 'Dashboards' },
  { href: '#faq', label: 'FAQ' },
]

export default function TopBar() {
  const { health } = useApp()
  const { user } = useAuth()
  const signOut = useSignOut()
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
          {user && (
            <span className="desktop-only">
              <UserMenu user={user} />
            </span>
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
            {user && (
              <div className="mobile-user">
                <UserAvatar user={user} size={40} />
                <div>
                  <strong>
                    {user.first_name} {user.last_name}
                  </strong>
                  <span>{user.email}</span>
                </div>
              </div>
            )}
            <div className="menu-foot">
              {!onNew && (
                <Link to="/new" className="btn btn-primary btn-lg btn-block">
                  <Plus size={17} /> New prep kit
                </Link>
              )}
              <button className="btn btn-lg btn-block" onClick={signOut}>
                <LogOut size={17} /> Sign out
              </button>
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
