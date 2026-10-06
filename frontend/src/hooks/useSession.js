import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { useApp } from '../context.jsx'

const ACTIVE = new Set(['queued', 'running'])

/**
 * Loads a prep session, polls /status while the agent is working (refreshing the
 * full content whenever a new section becomes ready) and exposes the actions the
 * dashboards use, with optimistic updates for progress tracking.
 */
export function useSession(id) {
  const { notify } = useApp()
  const [session, setSession] = useState(null)
  const [error, setError] = useState(null)
  const fingerprint = useRef('')

  const load = useCallback(async () => {
    const data = await api.getSession(id)
    setSession(data)
    return data
  }, [id])

  useEffect(() => {
    setSession(null)
    setError(null)
    load().catch((e) => setError(e.message))
  }, [load])

  const status = session?.status
  useEffect(() => {
    if (!ACTIVE.has(status)) return undefined
    let stopped = false
    let timer
    const tick = async () => {
      try {
        const st = await api.getStatus(id)
        if (stopped) return
        const key = `${st.status}|${(st.progress?.sections_ready || []).join(',')}|${st.summary?.questions}|${st.summary?.revision}`
        if (key !== fingerprint.current || !ACTIVE.has(st.status)) {
          fingerprint.current = key
          const full = await api.getSession(id)
          if (!stopped) setSession(full)
        } else {
          setSession((prev) => (prev ? { ...prev, status: st.status, progress: st.progress, error: st.error, warnings: st.warnings, summary: st.summary } : prev))
        }
      } catch {
        /* transient network error - keep polling */
      }
      if (!stopped) timer = setTimeout(tick, 1500)
    }
    timer = setTimeout(tick, 900)
    return () => {
      stopped = true
      clearTimeout(timer)
    }
  }, [id, status])

  // ------------------------------------------------------------- actions
  const patchState = useCallback((mutate) => {
    setSession((prev) => {
      if (!prev) return prev
      const state = structuredClone(prev.user_state || { items: {}, topics: {}, evaluations: {} })
      mutate(state)
      return { ...prev, user_state: state }
    })
  }, [])

  const setItemStatus = useCallback(
    async (itemId, value) => {
      patchState((s) => {
        s.items = s.items || {}
        if (value) s.items[itemId] = value
        else delete s.items[itemId]
      })
      try {
        await api.updateState(id, { item_id: itemId, status: value || null })
      } catch (e) {
        notify(e.message, 'error')
        load()
      }
    },
    [id, patchState, notify, load],
  )

  const setTopicRevised = useCallback(
    async (topicId, revised) => {
      patchState((s) => {
        s.topics = s.topics || {}
        if (revised) s.topics[topicId] = true
        else delete s.topics[topicId]
      })
      try {
        await api.updateState(id, { topic_id: topicId, revised })
      } catch (e) {
        notify(e.message, 'error')
        load()
      }
    },
    [id, patchState, notify, load],
  )

  const generateMore = useCallback(
    async (body) => {
      const res = await api.generate(id, body)
      setSession((prev) => {
        if (!prev) return prev
        const result = { ...prev.result, [body.section]: [...(prev.result[body.section] || []), ...res.added] }
        return { ...prev, result, summary: res.counts }
      })
      return res
    },
    [id],
  )

  const evaluate = useCallback(
    async (body) => {
      const res = await api.evaluate(id, body)
      patchState((s) => {
        s.evaluations = s.evaluations || {}
        const prev = s.evaluations[body.item_id] || {}
        s.evaluations[body.item_id] = { score: res.score, best: Math.max(res.score, prev.best || 0), attempts: (prev.attempts || 0) + 1 }
      })
      return res
    },
    [id, patchState],
  )

  const addQuizAttempt = useCallback(
    async (body) => {
      const attempts = await api.addQuizAttempt(id, body)
      setSession((prev) => (prev ? { ...prev, quiz_attempts: attempts } : prev))
      return attempts
    },
    [id],
  )

  const retry = useCallback(async () => {
    await api.retry(id)
    fingerprint.current = ''
    await load()
  }, [id, load])

  return { session, error, reload: load, setItemStatus, setTopicRevised, generateMore, evaluate, addQuizAttempt, retry }
}
