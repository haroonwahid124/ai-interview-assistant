// AudioWorklet: runs on the browser's audio thread.
// Collects microphone samples (Float32, -1..1) and posts 50 ms chunks of
// Int16 PCM to the main thread, which sends them to AssemblyAI.
const CHUNK_SAMPLES = 1200 // 50 ms at 24 kHz

class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this.buffer = new Int16Array(CHUNK_SAMPLES)
    this.length = 0
  }

  process(inputs) {
    const channel = inputs[0] && inputs[0][0]
    if (!channel) return true

    for (let i = 0; i < channel.length; i++) {
      const s = Math.max(-1, Math.min(1, channel[i]))
      this.buffer[this.length++] = s < 0 ? s * 0x8000 : s * 0x7fff
      if (this.length === CHUNK_SAMPLES) {
        this.port.postMessage(this.buffer.slice(0))
        this.length = 0
      }
    }
    return true // keep the processor alive
  }
}

registerProcessor('mic-processor', MicProcessor)
