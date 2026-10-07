import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowLeft, ArrowRight, CircleCheck, Eye, PartyPopper, RotateCcw, Shuffle } from 'lucide-react'
import { EASE } from '../lib/motion.js'
import { Meter } from './Viz.jsx'
import { QuestionBody, QuestionLead, StatusChips } from './QuestionCard.jsx'

/** Focused flashcard-style drill through the filtered questions, one at a time. */
export default function DrillView({ items, allItems, resetKey, section, userItems, evaluations, onSetStatus }) {
  // The deck is a snapshot of the filtered ids, so marking a card (which may drop it
  // from a "not mastered" filter) never shifts the position. It resets when filters change.
  const [deck, setDeck] = useState(() => items.map((q) => q.id))
  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [direction, setDirection] = useState(1)
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDeck(items.map((q) => q.id))
    setIndex(0)
    setDone(false)
    setRevealed(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetKey])

  const byId = useMemo(() => new Map(allItems.map((q) => [q.id, q])), [allItems])
  const cards = useMemo(() => deck.map((id) => byId.get(id)).filter(Boolean), [deck, byId])
  const item = cards[Math.min(index, cards.length - 1)]

  const go = useCallback(
    (step) => {
      setDirection(step)
      setRevealed(false)
      const next = index + step
      if (next >= cards.length) {
        setDone(true)
        return
      }
      setIndex(Math.max(0, next))
    },
    [index, cards.length],
  )

  const mark = useCallback(
    (status) => {
      if (!item) return
      onSetStatus(item.id, status)
      go(1)
    },
    [item, onSetStatus, go],
  )

  useEffect(() => {
    if (done || !item) return undefined
    const onKey = (e) => {
      if (e.target.closest('input, textarea, select, button, a')) return
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault()
        setRevealed(true)
      } else if (e.key === 'ArrowRight') go(1)
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key.toLowerCase() === 'm') mark('mastered')
      else if (e.key.toLowerCase() === 'r') mark('review')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [done, item, go, mark])

  if (!cards.length || !item) return null

  const masteredHere = cards.filter((q) => userItems[q.id] === 'mastered').length
  const reviewHere = cards.filter((q) => userItems[q.id] === 'review').length

  if (done) {
    return (
      <motion.div className="drill" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, ease: EASE }}>
        <div className="drill-card empty" style={{ minHeight: 0 }}>
          <div className="empty-art">
            <PartyPopper size={30} />
          </div>
          <h3>Drill complete</h3>
          <p>
            You went through {cards.length} questions: {masteredHere} mastered, {reviewHere} marked for review.
          </p>
          <div className="row wrap" style={{ justifyContent: 'center', marginTop: 10 }}>
            <button
              className="btn btn-sec"
              onClick={() => {
                setDone(false)
                setIndex(0)
                setRevealed(false)
              }}
            >
              <RotateCcw size={16} /> Start again
            </button>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="drill">
      <div className="drill-top">
        <span>
          Card {index + 1} of {cards.length}
        </span>
        <Meter value={index + 1} max={cards.length} label="Drill progress" />
        <span className="row" style={{ gap: 6 }}>
          <CircleCheck size={15} className="icon-ok" /> {masteredHere} mastered
        </span>
      </div>
      <div className="drill-deck">
        <AnimatePresence mode="wait" custom={direction} initial={false}>
          <motion.div
            key={item.id}
            className="drill-card"
            custom={direction}
            initial={{ opacity: 0, x: 48 * direction, rotate: direction * 1.2 }}
            animate={{ opacity: 1, x: 0, rotate: 0 }}
            exit={{ opacity: 0, x: -48 * direction, rotate: -direction * 1.2 }}
            transition={{ duration: 0.32, ease: EASE }}
          >
            <div className="row wrap">
              <StatusChips item={item} status={userItems[item.id]} evaluation={evaluations[item.id]} />
            </div>
            <div className="drill-q">{item.question}</div>
            {!revealed && <QuestionLead section={section} item={item} />}
            {revealed ? (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35, ease: EASE }}>
                <QuestionBody section={section} item={item} />
              </motion.div>
            ) : (
              <div className="qblock">
                <button className="btn btn-sec btn-lg" onClick={() => setRevealed(true)}>
                  <Eye size={17} /> Reveal model answer
                </button>
                <p className="subtle" style={{ marginTop: 10 }}>
                  Say your answer out loud first, then reveal and compare.
                </p>
              </div>
            )}
            <div className="drill-actions">
              <button className="btn btn-ghost" onClick={() => go(-1)} disabled={index === 0}>
                <ArrowLeft size={16} /> Previous
              </button>
              <div className="row wrap">
                <button className="btn" onClick={() => mark('review')}>
                  <RotateCcw size={16} /> Review later
                </button>
                <button className="btn btn-sec" onClick={() => mark('mastered')}>
                  <CircleCheck size={16} /> Got it
                </button>
              </div>
              <button className="btn btn-ghost" onClick={() => go(1)}>
                {index + 1 === cards.length ? 'Finish' : 'Skip'} <ArrowRight size={16} />
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="drill-keys" aria-hidden="true">
        <span>
          <kbd className="kbd">Space</kbd> reveal
        </span>
        <span>
          <kbd className="kbd">←</kbd>
          <kbd className="kbd">→</kbd> navigate
        </span>
        <span>
          <kbd className="kbd">M</kbd> got it
        </span>
        <span>
          <kbd className="kbd">R</kbd> review later
        </span>
        <span>
          <Shuffle size={13} /> uses your current filters
        </span>
      </div>
    </div>
  )
}
