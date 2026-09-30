// candidate feedback (no hiring decision shown)
import { useEffect, useState } from 'react'
import { api } from '../api'
import RoleFitLadder from '../components/RoleFitLadder.jsx'
import ScoreBars from '../components/ScoreBars.jsx'
import { ErrorNote, Loading } from '../components/Status.jsx'

export default function CandidateReport({ id }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.candidateReport(id).then(setReport).catch((e) => setError(e.message))
  }, [id])

  if (error) return <ErrorNote>{error}</ErrorNote>
  if (!report) return <Loading what="Loading your feedback" />

  return (
    <article className="report">
      <header className="report-head">
        <div>
          <h1>Your interview feedback</h1>
          <p className="muted">{report.applied_role}</p>
        </div>
        <div className="verdict">
          <p className="verdict-score"><span className="num">{Math.round(report.overall_score)}</span>/100 overall</p>
        </div>
      </header>

      <section className="panel">
        <p>{report.summary}</p>
        <ScoreBars criteria={report.criteria} />
      </section>

      <div className="two-col">
        <section className="panel">
          <h2>What went well</h2>
          <ul>{report.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
        </section>
        <section className="panel">
          <h2>What to work on</h2>
          <ul>{report.improvement_tips.map((s) => <li key={s}>{s}</li>)}</ul>
          {report.skills_to_build.length > 0 && (
            <>
              <h3>Skills to build for {report.applied_role}</h3>
              <ul>
                {report.skills_to_build.map((g) => (
                  <li key={g.skill}>{g.skill}: aim for level {g.required_level} (you showed {g.candidate_level})</li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>

      {report.recommended_roles.length > 0 && (
        <section className="panel">
          <h2>Roles that match your skills</h2>
          <RoleFitLadder fits={report.recommended_roles} appliedRole={report.applied_role} showGaps={false} />
        </section>
      )}

      <p className="advisory">{report.next_steps}</p>
    </article>
  )
}
