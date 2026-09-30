// role fit bars with the 50% / 75% zones shown
const TONE = { best_fit: 'best', suitable: 'suitable', training: 'training', not_suitable: 'not' }

export default function RoleFitLadder({ fits, appliedRole, showGaps = true }) {
  return (
    <ol className="ladder">
      {fits.map((fit) => (
        <li key={fit.role_title} className={`ladder-row tone-${TONE[fit.category]}`}>
          <div className="ladder-head">
            <span className="ladder-role">
              {fit.role_title}
              {fit.role_title === appliedRole && <span className="applied"> (applied)</span>}
            </span>
            <span className="ladder-verdict">{fit.category_label}</span>
            <span className="ladder-score">{Math.round(fit.fit_score)}%</span>
          </div>

          <div
            className="ladder-track"
            role="img"
            aria-label={`${fit.role_title}: ${Math.round(fit.fit_score)}% fit, ${fit.category_label}`}
          >
            <span className="zone zone-training" />
            <span className="zone zone-suitable" />
            <span className="ladder-fill" style={{ width: `${fit.fit_score}%` }} />
          </div>

          {showGaps && fit.gaps.length > 0 && (
            <p className="ladder-gaps">
              {fit.gaps.map((g, i) => (
                <span key={g.skill}>
                  {i > 0 && ', '}
                  {g.critical ? <strong>{g.skill}</strong> : g.skill} ({g.candidate_level}/{g.required_level})
                </span>
              ))}
            </p>
          )}
        </li>
      ))}
    </ol>
  )
}
