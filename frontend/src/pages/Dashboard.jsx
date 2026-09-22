// HR home: invite a candidate, see interviews, see roles.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import { ErrorNote, Loading, RecommendationBadge, StatusText, formatDate } from '../components/Status.jsx'

function InviteForm({ roles, onCreated }) {
  const [roleId, setRoleId] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [link, setLink] = useState('')
  const [copied, setCopied] = useState(false)

  const create = async () => {
    setBusy(true)
    setError('')
    try {
      const interview = await api.createInterview({
        role_id: Number(roleId),
        candidate_name: name,
        candidate_email: email || null,
      })
      setLink(`${window.location.origin}/#/interview/${interview.id}`)
      setCopied(false)
      setName('')
      setEmail('')
      onCreated()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const copy = async () => {
    await navigator.clipboard.writeText(link)
    setCopied(true)
  }

  return (
    <section className="panel invite">
      <h2>Invite a candidate</h2>
      <div className="form-row">
        <label>
          Role
          <select value={roleId} onChange={(e) => setRoleId(e.target.value)}>
            <option value="">Choose a role</option>
            {roles.map((r) => <option key={r.id} value={r.id}>{r.title}</option>)}
          </select>
        </label>
        <label>
          Candidate name
          <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
        </label>
        <label>
          <span>Email <span className="muted">(optional)</span></span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="off" />
        </label>
        <button className="primary" onClick={create} disabled={busy || !roleId || !name.trim()}>
          {busy ? 'Creating…' : 'Create interview link'}
        </button>
      </div>
      <ErrorNote>{error}</ErrorNote>
      {link && (
        <div className="link-box">
          <p>Send this link to the candidate:</p>
          <div className="link-row">
            <input readOnly value={link} onFocus={(e) => e.target.select()} aria-label="Interview link" />
            <button onClick={copy}>{copied ? 'Copied' : 'Copy link'}</button>
            <a href={link.slice(link.indexOf('#'))}>Open it here</a>
          </div>
        </div>
      )}
    </section>
  )
}

export default function Dashboard() {
  const [roles, setRoles] = useState(null)
  const [interviews, setInterviews] = useState(null)
  const [mode, setMode] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [r, i, h] = await Promise.all([api.listRoles(), api.listInterviews(), api.health()])
      setRoles(r)
      setInterviews(i)
      setMode(h.llm_provider)
      setError('')
    } catch (e) {
      setError(`Couldn't reach the API. Is the backend running? (${e.message})`)
    }
  }, [])

  useEffect(() => { load() }, [load])

  if (error) return <ErrorNote action={<button onClick={load}>Try again</button>}>{error}</ErrorNote>
  if (!roles || !interviews) return <Loading what="Loading dashboard" />

  return (
    <>
      <h1>Screening interviews</h1>
      {mode === 'mock' && (
        <p className="mock-note">
          Scoring is in mock mode, so reports use keyword counting instead of an AI model.
          Set <code>LLM_PROVIDER=anthropic</code> for real evaluations.
        </p>
      )}

      <InviteForm roles={roles} onCreated={load} />

      <section className="panel">
        <div className="panel-head">
          <h2>Interviews</h2>
          <button onClick={load}>Refresh</button>
        </div>
        {interviews.length === 0 ? (
          <p className="muted">No interviews yet. Create a link above to invite your first candidate.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Candidate</th>
                  <th scope="col">Role</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="num">Score</th>
                  <th scope="col">Recommendation</th>
                  <th scope="col"><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {interviews.map((i) => (
                  <tr key={i.id}>
                    <td>
                      {i.candidate_name}
                      <div className="muted small">{formatDate(i.completed_at || i.created_at)}</div>
                    </td>
                    <td>{i.role_title}</td>
                    <td><StatusText status={i.status} /></td>
                    <td className="num">{i.overall_score != null ? `${Math.round(i.overall_score)}%` : ''}</td>
                    <td>{i.status === 'completed' ? <RecommendationBadge label={i.recommendation} /> : ''}</td>
                    <td className="actions">
                      {i.status === 'created'
                        ? <a href={`#/interview/${i.id}`}>Candidate link</a>
                        : <a href={`#/reports/${i.id}`}>View report</a>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="panel-head">
          <h2>Roles</h2>
          <a className="button" href="#/roles/new">Add a role</a>
        </div>
        <ul className="role-list">
          {roles.map((r) => (
            <li key={r.id}>
              <h3>{r.title}</h3>
              <p className="muted">{r.description}</p>
              <p className="small">
                {r.skills.map((s, idx) => (
                  <span key={s.name}>
                    {idx > 0 && ', '}
                    {s.critical ? <strong>{s.name}</strong> : s.name} (level {s.required_level})
                  </span>
                ))}
              </p>
            </li>
          ))}
        </ul>
        <p className="muted small">Skills in bold are critical: a gap there rules out "Suitable".</p>
      </section>
    </>
  )
}
