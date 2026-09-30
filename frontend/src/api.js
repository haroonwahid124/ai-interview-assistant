// fetch wrapper for /api
// sends the saved HR key if there is one, asks for it on a 401
function storedHrKey() {
  return localStorage.getItem('hrApiKey') || ''
}

function askForHrKey() {
  const key = window.prompt('HR access key:')
  if (key === null) return null // cancelled
  localStorage.setItem('hrApiKey', key)
  return key
}

async function send(path, { method, body }) {
  const headers = {}
  const key = storedHrKey()
  if (key) headers['X-HR-Key'] = key
  if (body) headers['Content-Type'] = 'application/json'
  return fetch(`/api${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
}

async function request(path, { method = 'GET', body } = {}) {
  let res = await send(path, { method, body })

  // wrong/missing HR key, ask and retry once
  if (res.status === 401 && askForHrKey() !== null) {
    res = await send(path, { method, body })
  }

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = data?.detail
    // fastapi validation errors are a list
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