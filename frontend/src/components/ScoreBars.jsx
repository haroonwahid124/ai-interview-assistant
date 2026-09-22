// Criterion scores as simple bars. Evidence is optional (HR view only).
export default function ScoreBars({ criteria, showEvidence = false }) {
  return (
    <dl className="scores">
      {criteria.map((c) => (
        <div key={c.key} className="score-row">
          <dt>{c.label}</dt>
          <dd>
            <span className="score-value">{c.score}/5</span>
            <span className="score-track" aria-hidden="true">
              <span className="score-fill" style={{ width: `${c.percent}%` }} />
            </span>
            {showEvidence && c.evidence && <q className="evidence">{c.evidence}</q>}
          </dd>
        </div>
      ))}
    </dl>
  )
}
