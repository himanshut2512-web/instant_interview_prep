// Thin client for the FastAPI backend. All routes live under /api.

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    throw new Error('Cannot reach the backend. Is the API server running on port 8000?')
  }
  if (response.status === 204) return null
  const text = await response.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }
  if (!response.ok) {
    const detail = body && body.detail
    let message = `Request failed (${response.status})`
    if (typeof detail === 'string') message = detail
    else if (Array.isArray(detail)) message = detail.map((d) => d.msg || String(d)).join('; ')
    throw new Error(message)
  }
  return body
}

function json(method, body) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}

export const api = {
  health: () => request('/health'),
  sample: () => request('/sample'),
  listSessions: () => request('/sessions'),
  createSession: (formData) => request('/sessions', { method: 'POST', body: formData }),
  getSession: (id) => request(`/sessions/${id}`),
  getStatus: (id) => request(`/sessions/${id}/status`),
  deleteSession: (id) => request(`/sessions/${id}`, { method: 'DELETE' }),
  retry: (id) => request(`/sessions/${id}/retry`, { method: 'POST' }),
  generate: (id, body) => request(`/sessions/${id}/generate`, json('POST', body)),
  evaluate: (id, body) => request(`/sessions/${id}/evaluate`, json('POST', body)),
  updateState: (id, body) => request(`/sessions/${id}/state`, json('PUT', body)),
  addQuizAttempt: (id, body) => request(`/sessions/${id}/quiz-attempts`, json('POST', body)),
  exportUrl: (id) => `/api/sessions/${id}/export.md`,
}
