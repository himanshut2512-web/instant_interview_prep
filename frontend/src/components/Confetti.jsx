import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

const COLORS = ['#6366f1', '#7c3aed', '#2a78d6', '#1baf7a', '#eb6834', '#e87ba4', '#fab219']

/** One celebratory burst (skipped entirely when the user prefers reduced motion). */
export default function Confetti({ fire }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!fire) return undefined
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return undefined
    const canvas = canvasRef.current
    if (!canvas) return undefined
    const ctx = canvas.getContext('2d')
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    const resize = () => {
      canvas.width = window.innerWidth * dpr
      canvas.height = window.innerHeight * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    const w = window.innerWidth
    const pieces = Array.from({ length: 150 }, (_, i) => {
      const fromLeft = i % 2 === 0
      return {
        x: fromLeft ? w * 0.15 : w * 0.85,
        y: window.innerHeight * 0.65,
        vx: (fromLeft ? 1 : -1) * (3 + Math.random() * 7),
        vy: -(9 + Math.random() * 9),
        size: 5 + Math.random() * 6,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.3,
        color: COLORS[i % COLORS.length],
        shape: i % 3,
      }
    })
    const start = performance.now()
    let frame
    const draw = (now) => {
      const t = now - start
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const fade = Math.max(0, 1 - Math.max(0, t - 1800) / 900)
      for (const p of pieces) {
        p.vy += 0.32
        p.vx *= 0.992
        p.x += p.vx
        p.y += p.vy
        p.rot += p.vr
        ctx.save()
        ctx.globalAlpha = fade
        ctx.translate(p.x, p.y)
        ctx.rotate(p.rot)
        ctx.fillStyle = p.color
        if (p.shape === 0) ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2)
        else if (p.shape === 1) {
          ctx.beginPath()
          ctx.arc(0, 0, p.size / 2.6, 0, Math.PI * 2)
          ctx.fill()
        } else ctx.fillRect(-p.size / 3, -p.size / 3, p.size / 1.5, p.size / 1.5)
        ctx.restore()
      }
      if (t < 2700) frame = requestAnimationFrame(draw)
      else ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    frame = requestAnimationFrame(draw)
    window.addEventListener('resize', resize)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
    }
  }, [fire])

  if (!fire) return null
  return createPortal(
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{ position: 'fixed', inset: 0, width: '100vw', height: '100vh', pointerEvents: 'none', zIndex: 120 }}
    />,
    document.body,
  )
}
