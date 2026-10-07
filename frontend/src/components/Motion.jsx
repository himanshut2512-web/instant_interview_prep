import { useEffect, useRef } from 'react'
import { animate, motion, useInView, useReducedMotion } from 'motion/react'
import { EASE } from '../lib/motion.js'

/** Fades/slides its children in the first time they scroll into view. */
export function Reveal({ children, delay = 0, y = 18, className, as = 'div', amount = 0.2, ...rest }) {
  const Comp = motion[as] || motion.div
  return (
    <Comp
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount }}
      transition={{ duration: 0.6, delay, ease: EASE }}
      {...rest}
    >
      {children}
    </Comp>
  )
}

/** Animated number. Counts from its previous value (0 on first view) to `value`. */
export function CountUp({ value, duration = 1.1, format = defaultFormat, startOnView = false, className }) {
  const ref = useRef(null)
  const previous = useRef(0)
  const reduce = useReducedMotion()
  const visible = useInView(ref, { once: true, amount: 0.4 })
  const numeric = typeof value === 'number' && Number.isFinite(value)

  useEffect(() => {
    const node = ref.current
    if (!node) return undefined
    if (!numeric) {
      node.textContent = value ?? ''
      return undefined
    }
    if (reduce || (startOnView && !visible)) {
      if (reduce) {
        node.textContent = format(value)
        previous.current = value
      }
      return undefined
    }
    const controls = animate(previous.current, value, {
      duration,
      ease: EASE,
      onUpdate: (v) => {
        node.textContent = format(v)
      },
    })
    previous.current = value
    return () => controls.stop()
  }, [value, numeric, reduce, visible, startOnView, duration, format])

  return (
    <span ref={ref} className={className}>
      {numeric ? format(reduce ? value : 0) : value}
    </span>
  )
}

function defaultFormat(v) {
  return Math.round(v).toLocaleString()
}

/** Wrapper that animates a page's content in on mount. */
export function Page({ children, className, ...rest }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: EASE }}
      {...rest}
    >
      {children}
    </motion.div>
  )
}
