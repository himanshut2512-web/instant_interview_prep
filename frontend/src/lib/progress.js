// Derived study progress for a prep session (shared by the sidebar, overview and banners).

export const QUESTION_SECTIONS = ['theory', 'practical', 'scenario']

export function computeProgress(session) {
  const result = session?.result || {}
  const items = session?.user_state?.items || {}
  const revisedTopics = session?.user_state?.topics || {}
  const sections = {}
  let interviewTotal = 0
  let mastered = 0
  for (const key of QUESTION_SECTIONS) {
    const list = result[key] || []
    const done = list.filter((q) => items[q.id] === 'mastered').length
    sections[key] = { total: list.length, mastered: done, review: list.filter((q) => items[q.id] === 'review').length }
    interviewTotal += list.length
    mastered += done
  }
  const notes = result.revision || []
  const revised = notes.filter((n) => revisedTopics[n.id]).length
  const attempts = session?.quiz_attempts || []
  const best = attempts.length ? Math.max(...attempts.map((a) => a.score_pct)) : 0
  const parts = [notes.length ? revised / notes.length : 0, interviewTotal ? mastered / interviewTotal : 0, best / 100]
  const readiness = Math.round((100 * parts.reduce((a, b) => a + b, 0)) / parts.length)
  return {
    sections,
    interviewTotal,
    mastered,
    revisionTotal: notes.length,
    revised,
    bestQuiz: attempts.length ? best : null,
    attempts: attempts.length,
    readiness,
  }
}
