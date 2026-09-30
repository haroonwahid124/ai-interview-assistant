// voice interview logic
// mic -> get token -> websocket -> stream audio -> collect transcript -> submit
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { base64ToFloat32, int16ToBase64 } from '../audio/pcm'

const SAMPLE_RATE = 24000
const GOODBYE_TIMEOUT_MS = 10000
const SUBMIT_FALLBACK_MS = 5000 // in case session.ended never comes

export function useVoiceInterview(interviewId) {
  // idle | connecting | live | ending | submitting | done | error
  const [phase, setPhase] = useState('idle')
  // who is talking right now: none | interviewer | candidate
  const [speaker, setSpeaker] = useState('none')
  const [turns, setTurns] = useState([])
  const [error, setError] = useState('')

  // refs so the websocket callbacks see current values
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

  // audio out
  const play = (base64) => {
    const { ctx } = r.current
    const samples = base64ToFloat32(base64)
    const buffer = ctx.createBuffer(1, samples.length, SAMPLE_RATE)
    buffer.copyToChannel(samples, 0)
    const src = ctx.createBufferSource()
    src.buffer = buffer
    src.connect(ctx.destination)
    // queue chunks back to back so there's no gaps
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

  // mic in
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
    source.connect(node) // not to speakers or you hear yourself
    r.current.micNode = node
  }

  const stopMic = () => {
    r.current.micNode?.disconnect()
    r.current.micNode = null
    r.current.micStream?.getTracks().forEach((t) => t.stop())
    r.current.micStream = null
  }

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
      // 502 = saved but scoring failed, don't resubmit
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
      // send session.end, just closing keeps a paid 30s resume window open
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
        stopPlayback() // candidate interrupted
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
        // tool result has to be sent after reply.done
        state.pendingTools.push({ call_id: msg.call_id, result: JSON.stringify({ ok: true }) })
        if (msg.name === 'end_interview') state.endStage = 'tool_called'
        break

      case 'reply.done': {
        const pending = state.pendingTools
        state.pendingTools = []
        pending.forEach((t) => state.ws?.send(JSON.stringify({ type: 'tool.result', ...t })))

        later(() => setSpeaker((s) => (s === 'interviewer' ? 'none' : s)), msUntilPlaybackEnds())

        if (state.endStage === 'tool_called') {
          // wait for the goodbye, with a timeout
          state.endStage = 'waiting_goodbye'
          later(endSession, msUntilPlaybackEnds() + GOODBYE_TIMEOUT_MS)
        } else if (state.endStage === 'waiting_goodbye') {
          later(endSession, msUntilPlaybackEnds() + 300)
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

    // has to be created on click or the browser blocks audio
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
        submit() // connection dropped, submit what we have
      } else {
        cleanup()
        setError(event.code === 1006
          ? 'Could not connect to the voice service. Refresh the page and try again.'
          : 'The voice session closed before the interview started.')
        setPhase('error')
      }
    }
  }, [interviewId, handleEvent, submit])

  // end the session if they leave the page
  useEffect(() => () => {
    const { ws } = r.current
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: 'session.end' }))
    r.current.submitted = true
    cleanup()
  }, [])

  return { phase, speaker, turns, error, start, end: endSession, retrySubmit: submit }
}
