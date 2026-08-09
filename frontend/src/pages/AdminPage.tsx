import { useEffect, useState } from 'react'
import { getRuntimeSettings, resetRuntimeSettings, updateRuntimeSettings } from '../api/client'
import type { RuntimeSettings, RuntimeSettingsUpdate, VadMethod } from '../api/types'
import { ModelLoadWarningBanner } from '../components/ModelLoadWarningBanner'
import { Spinner } from '../components/Spinner'

export function AdminPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const [batchSize, setBatchSize] = useState(16)
  const [chunkSize, setChunkSize] = useState(30)
  const [beamSize, setBeamSize] = useState('')
  const [temperature, setTemperature] = useState('')
  const [conditionOnPreviousText, setConditionOnPreviousText] = useState<'' | 'true' | 'false'>('')
  const [vadMethod, setVadMethod] = useState<VadMethod>('silero')
  const [hfToken, setHfToken] = useState('')
  const [hfTokenSet, setHfTokenSet] = useState(false)
  const [maxCharsPerCue, setMaxCharsPerCue] = useState(84)
  const [maxSecondsPerCue, setMaxSecondsPerCue] = useState(7)

  function applySettings(s: RuntimeSettings) {
    setBatchSize(s.batch_size)
    setChunkSize(s.chunk_size)
    setBeamSize(s.beam_size === null ? '' : String(s.beam_size))
    setTemperature(s.temperature === null ? '' : String(s.temperature))
    setConditionOnPreviousText(
      s.condition_on_previous_text === null ? '' : s.condition_on_previous_text ? 'true' : 'false',
    )
    setVadMethod(s.vad_method)
    setHfToken('')
    setHfTokenSet(s.hf_token_set)
    setMaxCharsPerCue(s.max_chars_per_cue)
    setMaxSecondsPerCue(s.max_seconds_per_cue)
  }

  useEffect(() => {
    getRuntimeSettings()
      .then(applySettings)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load settings'))
      .finally(() => setLoading(false))
  }, [])

  async function handleSave() {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      const update: RuntimeSettingsUpdate = {
        batch_size: batchSize,
        chunk_size: chunkSize,
        beam_size: beamSize === '' ? null : Number(beamSize),
        temperature: temperature === '' ? null : Number(temperature),
        condition_on_previous_text: conditionOnPreviousText === '' ? null : conditionOnPreviousText === 'true',
        vad_method: vadMethod,
        max_chars_per_cue: maxCharsPerCue,
        max_seconds_per_cue: maxSecondsPerCue,
      }
      // Only send hf_token if the user actually typed one - an empty field
      // must mean "leave the existing token alone", not "clear it".
      if (hfToken.trim()) update.hf_token = hfToken.trim()

      const updated = await updateRuntimeSettings(update)
      applySettings(updated)
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  async function handleReset() {
    setSaving(true)
    setError(null)
    setSuccess(false)
    try {
      applySettings(await resetRuntimeSettings())
      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="page">
        <section className="panel">
          <div className="panel-body">
            <div className="job-progress-stage">
              <Spinner /> Loading settings…
            </div>
          </div>
        </section>
      </div>
    )
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-header">
          <h2>Transcription behavior</h2>
        </div>
        <div className="panel-body">
          <div className="field-row">
            <label className="field">
              <span className="field-label">Batch size</span>
              <input
                type="number"
                min={1}
                max={128}
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                disabled={saving}
              />
              <p className="field-hint">WhisperX's batched-decoding batch size. Higher = faster, more VRAM.</p>
            </label>
            <label className="field">
              <span className="field-label">Chunk size (seconds)</span>
              <input
                type="number"
                min={1}
                max={120}
                value={chunkSize}
                onChange={(e) => setChunkSize(Number(e.target.value))}
                disabled={saving}
              />
              <p className="field-hint">VAD-batching window. Smaller means more, shorter raw segments.</p>
            </label>
          </div>

          <div className="field-row">
            <label className="field">
              <span className="field-label">Beam size</span>
              <input
                type="number"
                min={1}
                max={20}
                placeholder="Default"
                value={beamSize}
                onChange={(e) => setBeamSize(e.target.value)}
                disabled={saving}
              />
              <p className="field-hint">Decoding beam width. Blank uses WhisperX's own default.</p>
            </label>
            <label className="field">
              <span className="field-label">Temperature</span>
              <input
                type="number"
                min={0}
                max={1}
                step={0.1}
                placeholder="Default"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                disabled={saving}
              />
              <p className="field-hint">Decoding sampling temperature. Blank uses the default.</p>
            </label>
          </div>

          <label className="field">
            <span className="field-label">Condition on previous text</span>
            <select
              value={conditionOnPreviousText}
              onChange={(e) => setConditionOnPreviousText(e.target.value as '' | 'true' | 'false')}
              disabled={saving}
            >
              <option value="">Default</option>
              <option value="true">On</option>
              <option value="false">Off</option>
            </select>
            <p className="field-hint">
              Whether decoding conditions on prior segment text. Can help coherence, but can also cause repetition
              loops on some audio.
            </p>
          </label>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Voice activity detection</h2>
        </div>
        <div className="panel-body">
          <label className="field">
            <span className="field-label">VAD method</span>
            <select value={vadMethod} onChange={(e) => setVadMethod(e.target.value as VadMethod)} disabled={saving}>
              <option value="silero">Silero (default, no account needed)</option>
              <option value="pyannote">Pyannote (requires a Hugging Face token)</option>
            </select>
          </label>

          {vadMethod === 'pyannote' && (
            <label className="field">
              <span className="field-label">Hugging Face token</span>
              <input
                type="password"
                placeholder={hfTokenSet ? 'Leave blank to keep the existing token' : 'Required for pyannote'}
                value={hfToken}
                onChange={(e) => setHfToken(e.target.value)}
                disabled={saving}
              />
              <p className="field-hint">
                Needs access to <code>pyannote/segmentation</code> on Hugging Face. Never shown back once saved.
              </p>
            </label>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Subtitles</h2>
        </div>
        <div className="panel-body">
          <div className="field-row">
            <label className="field">
              <span className="field-label">Max characters per cue</span>
              <input
                type="number"
                min={10}
                max={500}
                value={maxCharsPerCue}
                onChange={(e) => setMaxCharsPerCue(Number(e.target.value))}
                disabled={saving}
              />
            </label>
            <label className="field">
              <span className="field-label">Max seconds per cue</span>
              <input
                type="number"
                min={0.1}
                max={60}
                step={0.5}
                value={maxSecondsPerCue}
                onChange={(e) => setMaxSecondsPerCue(Number(e.target.value))}
                disabled={saving}
              />
            </label>
          </div>
          <p className="field-hint">Caps how long a single subtitle cue can be before it's split into more.</p>

          {error && <ModelLoadWarningBanner variant="error" message={error} />}
          {success && !error && <ModelLoadWarningBanner variant="success" message="Settings saved." />}
        </div>
        <div className="panel-footer">
          <button type="button" className="button" onClick={handleReset} disabled={saving}>
            Reset to defaults
          </button>
          <button type="button" className="button button-primary" onClick={handleSave} disabled={saving}>
            {saving && <Spinner />}
            Save
          </button>
        </div>
      </section>
    </div>
  )
}
