// Thin wrapper around fetch. Every call goes to /api on the same origin.

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
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
