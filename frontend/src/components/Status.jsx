// Small shared pieces used across pages.

export function Loading({ what = 'Loading' }) {
  return <p className="muted" role="status">{what}…</p>
}

export function ErrorNote({ children, action }) {
  if (!children) return null
  return (
    <div className="error-note" role="alert">
      <p>{children}</p>
      {action}
    </div>
  )
}

const RECOMMENDATION_TONE = {
  'Strongly recommend': 'best',
  Consider: 'suitable',
  'Further interview': 'training',
  'Not recommended': 'not',
}

export function RecommendationBadge({ label }) {
  if (!label) return <span className="muted">Pending</span>
  return <span className={`badge tone-${RECOMMENDATION_TONE[label] || 'neutral'}`}>{label}</span>
}

export function StatusText({ status }) {
  const text = { created: 'Not started', completed: 'Completed', failed: 'Scoring failed' }[status] || status
  return <span className={`status status-${status}`}>{text}</span>
}

export function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}
