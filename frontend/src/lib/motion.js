// Shared animation presets. MotionConfig (reducedMotion="user") in main.jsx turns
// transform animations off for people who ask their OS for reduced motion.

export const EASE = [0.22, 1, 0.36, 1]

export const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: EASE } },
}

export const fadeIn = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.5, ease: EASE } },
}

export const scaleIn = {
  hidden: { opacity: 0, scale: 0.94, y: 10 },
  show: { opacity: 1, scale: 1, y: 0, transition: { duration: 0.55, ease: EASE } },
}

export function stagger(staggerChildren = 0.07, delayChildren = 0) {
  return { hidden: {}, show: { transition: { staggerChildren, delayChildren } } }
}

// spread onto a motion element to animate it (and its variant children) on first scroll into view
export const inView = { initial: 'hidden', whileInView: 'show', viewport: { once: true, amount: 0.18 } }

export const pageTransition = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: EASE },
}

export const collapse = {
  initial: { height: 0, opacity: 0 },
  animate: { height: 'auto', opacity: 1, transition: { height: { duration: 0.35, ease: EASE }, opacity: { duration: 0.25, delay: 0.05 } } },
  exit: { height: 0, opacity: 0, transition: { height: { duration: 0.28, ease: EASE }, opacity: { duration: 0.15 } } },
}
