// Thin wrapper around fetch. Every call goes to /api on the same origin.

// HR staff are prompted once for the shared key; it's stashed in localStorage
// so they don't retype it on every page load. Candidate-facing calls send it
// too, but the backend only checks it on HR routes, so this is harmless there.
function getHrKey() {
  let key = localStorage.getItem('hrApiKey')
  if (key === null) {
    key = window.prompt('HR access key (leave blank if none set):') || ''
    localStorage.setItem('hrApiKey', key)
  }
  return key
}

async function request(path, { method = 'GET', body } = {}) {
  const headers = { 'X-HR-Key': getHrKey() }
  if (body) headers['Content-Type'] = 'application/json'

  const res = await fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    // FastAPI validation errors come back as a list of problems.
    const message = Array.isArray(detail)
      ? detail.map((d) => `${d.loc.slice(1).join('.')}: ${d.msg}`).join('; ')
      : detail || `Request failed with status ${res.status}`
    const error = new Error(message)
    error.status = res.status
    throw error
  }
  return data
}

export const api = {
  health: () => request('/health'),
  listRoles: () => request('/roles'),
  createRole: (role) => request('/roles', { method: 'POST', body: role }),
  listInterviews: () => request('/interviews'),
  createInterview: (data) => request('/interviews', { method: 'POST', body: data }),
  getInterview: (id) => request(`/interviews/${id}`),
  startSession: (id) => request(`/interviews/${id}/session`, { method: 'POST' }),
  submitTranscript: (id, turns) => request(`/interviews/${id}/transcript`, { method: 'POST', body: { turns } }),
  retryEvaluation: (id) => request(`/interviews/${id}/evaluate`, { method: 'POST' }),
  hrReport: (id) => request(`/interviews/${id}/report/hr`),
  candidateReport: (id) => request(`/interviews/${id}/report/candidate`),
}
