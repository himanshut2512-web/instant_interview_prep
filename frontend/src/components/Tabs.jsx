import { useId, useRef } from 'react'
import { motion } from 'motion/react'
import { useOverflowFade } from '../hooks/useOverflowFade.js'

const SPRING = { type: 'spring', stiffness: 520, damping: 40 }

// On narrow screens the row scrolls sideways; bring a picked option fully into view.
const reveal = (event) => event.currentTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })

/**
 * Segmented control with a sliding pill. Used for filters, so each option is a
 * toggle button (aria-pressed) inside a labelled group.
 * options: [{ value, label, icon?, count? }]
 */
export function SegmentedTabs({ value, onChange, options, ariaLabel, full = false, className = '' }) {
  const id = useId()
  const ref = useRef(null)
  useOverflowFade(ref)
  return (
    <div ref={ref} className={`tabs ${full ? 'full' : ''} ${className}`} role="group" aria-label={ariaLabel}>
      {options.map((option) => {
        const on = option.value === value
        return (
          <button
            key={String(option.value)}
            type="button"
            className={`tab ${on ? 'on' : ''}`}
            aria-pressed={on}
            onClick={(event) => {
              reveal(event)
              onChange(option.value)
            }}
          >
            {on && <motion.span layoutId={`seg-${id}`} className="tab-pill" transition={SPRING} />}
            {option.icon}
            {option.label}
            {option.count !== undefined && <span className="count">{option.count}</span>}
          </button>
        )
      })}
    </div>
  )
}

/** Content tabs with an animated underline (tablist semantics). */
export function UnderlineTabs({ value, onChange, options, ariaLabel, idPrefix }) {
  const id = useId()
  const ref = useRef(null)
  useOverflowFade(ref)
  return (
    <div ref={ref} className="utabs" role="tablist" aria-label={ariaLabel}>
      {options.map((option) => {
        const on = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="tab"
            id={`${idPrefix}-tab-${option.value}`}
            aria-selected={on}
            aria-controls={`${idPrefix}-panel`}
            className={`utab ${on ? 'on' : ''}`}
            onClick={(event) => {
              reveal(event)
              onChange(option.value)
            }}
          >
            {option.icon}
            {option.label}
            {on && <motion.span layoutId={`ul-${id}`} className="utab-bar" transition={SPRING} />}
          </button>
        )
      })}
    </div>
  )
}
