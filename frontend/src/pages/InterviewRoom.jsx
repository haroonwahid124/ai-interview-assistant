// The candidate's page: consent, the live voice interview, then a link to results.
import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { ErrorNote, Loading } from '../components/Status.jsx'
import { useVoiceInterview } from '../hooks/useVoiceInterview.js'

const SPEAKER_TEXT = {
  interviewer: 'Interviewer is speaking',
  candidate: 'Listening to you',
  none: 'Your turn when you are ready',
}

function Transcript({ turns }) {
  const end = useRef(null)
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' }) }, [turns])
  if (turns.length === 0) return <p className="muted">The conversation will appear here as you talk.</p>
  return (
    <ol className="transcript" aria-live="polite">
      {turns.map((t, i) => (
        <li key={i} className={`turn turn-${t.role}`}>
          <span className="turn-who">{t.role === 'candidate' ? 'You' : 'Interviewer'}</span>
          <p>{t.text}</p>
        </li>
      ))}
      <li ref={end} aria-hidden="true" />
    </ol>
  )
}

export default function InterviewRoom({ id }) {
  const [interview, setInterview] = useState(null)
  const [loadError, setLoadError] = useState('')
  const [consent, setConsent] = useState(false)
  const voice = useVoiceInterview(id)

  useEffect(() => {
    api.getInterview(id).then(setInterview).catch((e) => setLoadError(e.message))
  }, [id])

  if (loadError) return <ErrorNote>{loadError}</ErrorNote>
  if (!interview) return <Loading what="Loading your interview" />

  const alreadyDone = interview.status !== 'created' && voice.phase === 'idle'
  if (alreadyDone || voice.phase === 'done') {
    return (
      <section className="room-finished">
        <h1>Thanks, {interview.candidate_name.split(' ')[0]}</h1>
        <p>Your interview for {interview.role_title} is complete.</p>
        <a className="button primary" href={`#/results/${id}`}>See your feedback</a>
      </section>
    )
  }

  const { phase, speaker, turns, error } = voice
  const inCall = phase === 'connecting' || phase === 'live' || phase === 'ending'

  return (
    <div className="room">
      <div className="room-intro">
        <h1>{interview.role_title} interview</h1>
        <p className="lead">
          Hi {interview.candidate_name}. This is a spoken, first-round interview of about ten minutes.
          An AI interviewer will ask you a few questions, one at a time.
        </p>
      </div>

      {phase === 'idle' || phase === 'error' ? (
        <section className="panel">
          <h2>Before you start</h2>
          <ul className="checklist">
            <li>Use Chrome or Edge on a laptop or desktop.</li>
            <li>Wear headphones, so the interviewer's voice isn't picked up by your microphone.</li>
            <li>Find a quiet place. You can interrupt the interviewer at any time by speaking.</li>
            <li>Your audio isn't stored. A text transcript is saved and assessed by AI.</li>
          </ul>
          <label className="consent">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            <span>
              I understand my answers will be transcribed and assessed by AI, and that a person on the
              hiring team makes the final decision.
            </span>
          </label>
          <ErrorNote
            action={phase === 'error' && turns.length > 0 && (
              <button onClick={voice.retrySubmit}>Try sending again</button>
            )}
          >
            {error}
          </ErrorNote>
          <button className="primary large" onClick={voice.start} disabled={!consent}>
            {phase === 'error' ? 'Start again' : 'Start interview'}
          </button>
        </section>
      ) : (
        <section className="call">
          <div className={`presence presence-${phase === 'live' ? speaker : 'waiting'}`} aria-hidden="true">
            <span className="presence-ring" />
            <span className="presence-core" />
          </div>
          <p className="presence-label" role="status">
            {phase === 'connecting' && 'Connecting…'}
            {phase === 'live' && SPEAKER_TEXT[speaker]}
            {phase === 'ending' && 'Wrapping up…'}
            {phase === 'submitting' && 'Preparing your results. This can take up to a minute.'}
          </p>
          {error && <ErrorNote>{error}</ErrorNote>}
          {inCall && (
            <button className="danger" onClick={voice.end} disabled={phase !== 'live'}>
              End interview
            </button>
          )}
          <div className="panel transcript-panel">
            <h2>Transcript</h2>
            <Transcript turns={turns} />
          </div>
        </section>
      )}
    </div>
  )
}
