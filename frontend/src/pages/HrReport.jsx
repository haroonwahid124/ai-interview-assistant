// Full report for the hiring team.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import RoleFitLadder from '../components/RoleFitLadder.jsx'
import ScoreBars from '../components/ScoreBars.jsx'
import { ErrorNote, Loading, RecommendationBadge, formatDate } from '../components/Status.jsx'

export default function HrReport({ id }) {
  const [report, setReport] = useState(null)
  const [interview, setInterview] = useState(null)
  const [error, setError] = useState('')
  const [retrying, setRetrying] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const info = await api.getInterview(id)
      setInterview(info)
      if (info.status === 'completed') setReport(await api.hrReport(id))
    } catch (e) {
      setError(e.message)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  const retry = async () => {
    setRetrying(true)
    try {
      await api.retryEvaluation(id)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setRetrying(false)
    }
  }

  if (error && !interview) return <ErrorNote>{error}</ErrorNote>
  if (!interview) return <Loading what="Loading report" />

  if (interview.status !== 'completed') {
    return (
      <>
        <p><a href="#/">Back to dashboard</a></p>
        <h1>{interview.candidate_name}</h1>
        {interview.status === 'failed' ? (
          <ErrorNote action={<button onClick={retry} disabled={retrying}>{retrying ? 'Scoring…' : 'Retry scoring'}</button>}>
            The transcript was saved, but scoring failed. {error}
          </ErrorNote>
        ) : (
          <p>This candidate hasn't completed the interview yet.</p>
        )}
      </>
    )
  }
  if (!report) return <Loading what="Loading report" />

  return (
    <article className="report">
      <p><a href="#/">Back to dashboard</a></p>

      <header className="report-head">
        <div>
          <h1>{report.candidate_name}</h1>
          <p className="muted">
            Interviewed for {report.applied_role}, {formatDate(report.generated_at)}
          </p>
        </div>
        <div className="verdict">
          <p className="verdict-score"><span className="num">{Math.round(report.overall_score)}</span>/100 overall</p>
          <RecommendationBadge label={report.recommendation.label} />
        </div>
      </header>

      <section className="panel">
        <h2>Why this recommendation</h2>
        <ul>{report.recommendation.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        <p className="advisory">{report.advisory_notice}</p>
      </section>

      <section className="panel">
        <h2>Role fit</h2>
        <p className="muted small">
          Shaded zones mark 50% (possible with training) and 75% (suitable). Gaps show the level the
          candidate showed against the level needed; critical skills are in bold.
        </p>
        <RoleFitLadder fits={report.role_fit} appliedRole={report.applied_role} />
      </section>

      <div className="two-col">
        <section className="panel">
          <h2>Assessment</h2>
          <p>{report.summary}</p>
          <ScoreBars criteria={report.criteria} showEvidence />
        </section>
        <section className="panel">
          <h2>Strengths</h2>
          <ul>{report.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
          <h2>Weaknesses</h2>
          <ul>{report.weaknesses.map((s) => <li key={s}>{s}</li>)}</ul>
        </section>
      </div>

      <section className="panel">
        <h2>Skill evidence</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th scope="col">Skill</th><th scope="col" className="num">Level</th><th scope="col">Evidence</th></tr>
            </thead>
            <tbody>
              {[...report.skills].sort((a, b) => b.level - a.level).map((s) => (
                <tr key={s.skill}>
                  <td>{s.skill}</td>
                  <td className="num">{s.level}/5</td>
                  <td>{s.evidence ? <q>{s.evidence}</q> : <span className="muted">Not discussed</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel">
        <details>
          <summary>Full transcript ({report.transcript.length} turns)</summary>
          <ol className="transcript">
            {report.transcript.map((t, i) => (
              <li key={i} className={`turn turn-${t.role}`}>
                <span className="turn-who">{t.role === 'candidate' ? 'Candidate' : 'Interviewer'}</span>
                <p>{t.text}</p>
              </li>
            ))}
          </ol>
        </details>
      </section>
    </article>
  )
}
