import { motion } from 'motion/react'
import { EASE } from '../lib/motion.js'
import { CountUp } from './Motion.jsx'

/** Friendly empty / waiting state with an animated illustration tile. */
export function EmptyState({ icon: Icon, title, text, action, className = '' }) {
  return (
    <motion.div
      className={`card empty ${className}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: EASE }}
    >
      {Icon && (
        <div className="empty-art" aria-hidden="true">
          <Icon size={30} />
        </div>
      )}
      {title && <h3>{title}</h3>}
      {text && <p>{text}</p>}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </motion.div>
  )
}

/**
 * Hero banner at the top of each dashboard. The surrounding [data-section]
 * decides its colour and texture, so every dashboard looks distinct.
 * stats: [{ label, value }]
 */
export function PageBanner({ icon: Icon, kicker, title, description, stats, actions, children }) {
  return (
    <motion.section className="page-banner" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: EASE }}>
      {Icon && (
        <motion.div
          className="banner-icon"
          aria-hidden="true"
          initial={{ scale: 0.6, rotate: -12, opacity: 0 }}
          animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 16, delay: 0.1 }}
        >
          <Icon size={28} />
        </motion.div>
      )}
      <div className="banner-body">
        {kicker && <div className="banner-kicker">{kicker}</div>}
        <h1>{title}</h1>
        {description && <p>{description}</p>}
        {stats?.length > 0 && (
          <div className="banner-stats">
            {stats.map((s) => (
              <div className="banner-stat" key={s.label}>
                <strong>{typeof s.value === 'number' ? <CountUp value={s.value} /> : s.value}</strong>
                <span>{s.label}</span>
              </div>
            ))}
          </div>
        )}
        {children}
      </div>
      {actions && <div className="banner-actions no-print">{actions}</div>}
    </motion.section>
  )
}

/** Card heading with a coloured icon tile. */
export function CardTitle({ icon: Icon, title, sub, tone = '', right }) {
  return (
    <div className="card-head">
      <div style={{ minWidth: 0 }}>
        <h3 className="card-title">
          {Icon && (
            <span className={`title-icon ${tone}`} aria-hidden="true">
              <Icon size={17} />
            </span>
          )}
          {title}
        </h3>
        {sub && <p className="card-sub">{sub}</p>}
      </div>
      {right}
    </div>
  )
}
