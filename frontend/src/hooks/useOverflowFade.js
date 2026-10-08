import { useEffect } from 'react'

/**
 * Marks a horizontal scroller with data-fade="start" | "end" | "both" while part
 * of its content is clipped, so CSS can fade that edge and hint that it scrolls.
 */
export function useOverflowFade(ref) {
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    const update = () => {
      const hidden = el.scrollWidth - el.clientWidth
      const start = el.scrollLeft > 2
      const end = el.scrollLeft < hidden - 2
      const fade = start && end ? 'both' : start ? 'start' : end ? 'end' : ''
      if (fade) el.dataset.fade = fade
      else delete el.dataset.fade
    }
    update()
    el.addEventListener('scroll', update, { passive: true })
    const observer = new ResizeObserver(update)
    observer.observe(el)
    for (const child of el.children) observer.observe(child)
    return () => {
      el.removeEventListener('scroll', update)
      observer.disconnect()
    }
  }, [ref])
}
