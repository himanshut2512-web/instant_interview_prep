import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { AnimatePresence, motion } from 'motion/react'
import { EASE } from '../lib/motion.js'

/**
 * Animated modal rendered in a portal (so page transforms never trap it).
 * Escape and backdrop clicks close it unless `dismissable` is false.
 */
export default function Dialog({ open, onClose, labelledBy, children, className = '', dismissable = true, width }) {
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape' && dismissable) onClose()
    }
    window.addEventListener('keydown', onKey)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const previousFocus = document.activeElement
    const timer = setTimeout(() => {
      const panel = panelRef.current
      if (!panel) return
      const target = panel.querySelector('[autofocus], [data-autofocus]') || panel
      target.focus()
    }, 30)
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = previousOverflow
      clearTimeout(timer)
      if (previousFocus && previousFocus.focus) previousFocus.focus()
    }
  }, [open, dismissable, onClose])

  return createPortal(
    <AnimatePresence>
      {open && (
        <motion.div
          className="dialog-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onMouseDown={(e) => e.target === e.currentTarget && dismissable && onClose()}
        >
          <motion.div
            ref={panelRef}
            tabIndex={-1}
            className={`dialog ${className}`}
            style={width ? { width: `min(${width}px, 100%)` } : undefined}
            role="dialog"
            aria-modal="true"
            aria-labelledby={labelledBy}
            initial={{ opacity: 0, y: 18, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.98 }}
            transition={{ duration: 0.3, ease: EASE }}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}
