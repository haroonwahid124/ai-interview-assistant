// All the voice logic lives here, separate from the UI.
//
// Flow:
//   1. ask for the microphone (before spending a single-use token)
//   2. POST /session -> { token, ws_url, session }
//   3. open the WebSocket, send session.update with the interview config
//   4. on session.ready, start streaming mic audio as input.audio
//   5. collect transcript.user / transcript.agent into `turns`
//   6. when the agent calls end_interview (or the candidate clicks End),
//      send session.end, wait for session.ended, then POST the transcript
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { base64ToFloat32, int16ToBase64 } from '../audio/pcm'

const SAMPLE_RATE = 24000
const GOODBYE_TIMEOUT_MS = 10000 // if the agent never says goodbye after end_interview
const SUBMIT_FALLBACK_MS = 5000 // if session.ended never arrives

export function useVoiceInterview(interviewId) {
  // idle | connecting | live | ending | submitting | done | error
  const [phase, setPhase] = useState('idle')
  // who is talking right now: none | interviewer | candidate
  const [speaker, setSpeaker] = useState('none')
  const [turns, setTurns] = useState([])
  const [error, setError] = useState('')

  // Values the WebSocket callbacks need to read and change without re-rendering.
  const r = useRef(null)
  if (r.current === null) {
    r.current = {
      ws: null, ctx: null, micStream: null, micNode: null,
      nextPlayTime: 0, sources: [], pendingTools: [],
      endStage: 'none', // none | tool_called | waiting_goodbye | closing
      turns: [], submitted: false, timers: [],
    }
  }

  const later = (fn, ms) => r.current.timers.push(setTimeout(fn, ms))

  const addTurn = (role, text) => {
    if (!text?.trim()) return
    const turn = { role, text: text.trim(), at: new Date().toISOString() }
    r.current.turns = [...r.current.turns, turn]
    setTurns(r.current.turns)
  }

  // ---------------- audio out ----------------
  const play = (base64) => {
    const { ctx } = r.current
    const samples = base64ToFloat32(base64)
    const buffer = ctx.createBuffer(1, samples.length, SAMPLE_RATE)
    buffer.copyToChannel(samples, 0)
    const src = ctx.createBufferSource()
    src.buffer = buffer
    src.connect(ctx.destination)
    // Schedule chunks back to back so playback is gapless.
    const start = Math.max(r.current.nextPlayTime, ctx.currentTime)
    src.start(start)
    r.current.nextPlayTime = start + buffer.duration
    r.current.sources.push(src)
    src.onended = () => {
      r.current.sources = r.current.sources.filter((s) => s !== src)
    }
  }

  const stopPlayback = () => {
    r.current.sources.forEach((s) => { try { s.stop() } catch { /* already stopped */ } })
    r.current.sources = []
    if (r.current.ctx) r.current.nextPlayTime = r.current.ctx.currentTime
  }

  const msUntilPlaybackEnds = () => {
    const { ctx, nextPlayTime } = r.current
    return ctx ? Math.max(0, (nextPlayTime - ctx.currentTime) * 1000) : 0
  }

  // ---------------- audio in ----------------
  const startStreaming = async () => {
    const { ctx, micStream } = r.current
    await ctx.audioWorklet.addModule('/mic-processor.js')
    const source = ctx.createMediaStreamSource(micStream)
    const node = new AudioWorkletNode(ctx, 'mic-processor')
    node.port.onmessage = (e) => {
      const ws = r.current.ws
      if (ws?.readyState === WebSocket.OPEN && r.current.endStage !== 'closing') {
        ws.send(JSON.stringify({ type: 'input.audio', audio: int16ToBase64(e.data) }))
      }
    }
    source.connect(node) // not connected to the speakers, so you don't hear yourself
    r.current.micNode = node
  }

  const stopMic = () => {
    r.current.micNode?.disconnect()
    r.current.micNode = null
    r.current.micStream?.getTracks().forEach((t) => t.stop())
    r.current.micStream = null
  }

  // ---------------- lifecycle ----------------
  const cleanup = () => {
    r.current.timers.forEach(clearTimeout)
    r.current.timers = []
    stopMic()
    stopPlayback()
    r.current.ctx?.close().catch(() => {})
    r.current.ctx = null
  }

  const submit = useCallback(async () => {
    if (r.current.submitted) return
    r.current.submitted = true
    cleanup()
    setSpeaker('none')

    if (!r.current.turns.some((t) => t.role === 'candidate')) {
      setError("We didn't capture any answers. Check that your microphone works, then start again.")
      setPhase('error')
      r.current.submitted = false
      return
    }
    setPhase('submitting')
    try {
      await api.submitTranscript(interviewId, r.current.turns)
      setPhase('done')
    } catch (e) {
      setError(e.message)
      setPhase('error')
      // 502 means the transcript was saved but scoring failed: HR can retry, so don't resubmit.
      if (e.status !== 502) r.current.submitted = false
    }
  }, [interviewId])

  const endSession = useCallback(() => {
    const { ws } = r.current
    if (r.current.endStage === 'closing') return
    r.current.endStage = 'closing'
    stopMic()
    setPhase('ending')
    if (ws?.readyState === WebSocket.OPEN) {
      // Always send session.end rather than just closing: a bare close leaves
      // a billable 30-second resume window open.
      ws.send(JSON.stringify({ type: 'session.end' }))
      later(submit, SUBMIT_FALLBACK_MS)
    } else {
      submit()
    }
  }, [submit])

  const handleEvent = useCallback(async (msg) => {
    const state = r.current
    switch (msg.type) {
      case 'session.ready':
        try {
          await startStreaming()
          setPhase('live')
        } catch {
          setError('Could not start the microphone stream. Try Chrome or Edge.')
          endSession()
        }
        break

      case 'input.speech.started':
        stopPlayback() // candidate interrupted: stop the interviewer talking
        setSpeaker('candidate')
        break

      case 'input.speech.stopped':
        setSpeaker('none')
        break

      case 'transcript.user':
        addTurn('candidate', msg.text)
        break

      case 'reply.started':
        setSpeaker('interviewer')
        break

      case 'reply.audio':
        play(msg.data)
        break

      case 'transcript.agent':
        addTurn('interviewer', msg.text)
        break

      case 'tool.call':
        // Don't reply yet: AssemblyAI wants tool results after reply.done.
        state.pendingTools.push({ call_id: msg.call_id, result: JSON.stringify({ ok: true }) })
        if (msg.name === 'end_interview') state.endStage = 'tool_called'
        break

      case 'reply.done': {
        const pending = state.pendingTools
        state.pendingTools = []
        pending.forEach((t) => state.ws?.send(JSON.stringify({ type: 'tool.result', ...t })))

        later(() => setSpeaker((s) => (s === 'interviewer' ? 'none' : s)), msUntilPlaybackEnds())

        if (state.endStage === 'tool_called') {
          // The agent usually says goodbye after the tool result. Wait for that reply,
          // but don't wait forever.
          state.endStage = 'waiting_goodbye'
          later(endSession, msUntilPlaybackEnds() + GOODBYE_TIMEOUT_MS)
        } else if (state.endStage === 'waiting_goodbye') {
          later(endSession, msUntilPlaybackEnds() + 300) // let the goodbye finish playing
        }
        break
      }

      case 'session.error':
        setError(`Voice service error: ${msg.message || msg.error_code}`)
        break

      case 'session.ended':
        submit()
        break

      default:
        break
    }
  }, [endSession, submit])

  const start = useCallback(async () => {
    const state = r.current
    Object.assign(state, { turns: [], pendingTools: [], endStage: 'none', submitted: false })
    setTurns([])
    setError('')
    setPhase('connecting')

    // Created inside the click handler, so the browser allows audio playback.
    state.ctx = new AudioContext({ sampleRate: SAMPLE_RATE })
    state.nextPlayTime = state.ctx.currentTime

    let config
    try {
      state.micStream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
    } catch {
      cleanup()
      setError('Microphone access was blocked. Allow it in your browser settings and try again.')
      setPhase('error')
      return
    }
    try {
      config = await api.startSession(interviewId)
    } catch (e) {
      cleanup()
      setError(e.message)
      setPhase('error')
      return
    }

    const ws = new WebSocket(`${config.ws_url}?token=${encodeURIComponent(config.token)}`)
    state.ws = ws
    ws.onopen = () => ws.send(JSON.stringify({ type: 'session.update', session: config.session }))
    ws.onmessage = (event) => handleEvent(JSON.parse(event.data))
    ws.onclose = (event) => {
      state.ws = null
      if (state.submitted) return
      if (state.turns.length > 0) {
        submit() // connection dropped mid-interview: keep what we have
      } else {
        cleanup()
        setError(event.code === 1006
          ? 'Could not connect to the voice service. Refresh the page and try again.'
          : 'The voice session closed before the interview started.')
        setPhase('error')
      }
    }
  }, [interviewId, handleEvent, submit])

  // If the candidate navigates away, end the session properly.
  useEffect(() => () => {
    const { ws } = r.current
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'session.end' }))
    r.current.submitted = true
    cleanup()
  }, [])

  return { phase, speaker, turns, error, start, end: endSession, retrySubmit: submit }
}
