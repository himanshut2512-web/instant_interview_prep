// Thin client for the FastAPI backend. All routes live under /api.
// Sign-in uses an httpOnly session cookie, so requests just include credentials.

/** Fired when the server says the session is gone, so the app can return to sign-in. */
export const UNAUTHORIZED_EVENT = 'iip:unauthorized'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`/api${path}`, { credentials: 'same-origin', ...options })
  } catch {
    throw new Error('Cannot reach the server. Check your connection and try again.')
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
    if (response.status >= 500 && typeof detail !== 'string') message = 'Something went wrong on our side. Please try again.'
    const error = new Error(message)
    error.status = response.status
    error.field = body?.field || null
    if (response.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    throw error
  }
  return body
}

function json(method, body) {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}

export const api = {
  // accounts
  authConfig: () => request('/auth/config'),
  me: () => request('/auth/me'),
  register: (body) => request('/auth/register', json('POST', body)),
  login: (body) => request('/auth/login', json('POST', body)),
  logout: () => request('/auth/logout', { method: 'POST' }),
  forgotPassword: (email) => request('/auth/forgot-password', json('POST', { email })),
  checkResetToken: (token) => request(`/auth/reset-password?token=${encodeURIComponent(token)}`),
  resetPassword: (body) => request('/auth/reset-password', json('POST', body)),

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
