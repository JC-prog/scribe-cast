import { useEffect, useState } from 'react'
import { transcribeUrl } from '../api/client'
import { CompletionOverlay } from '../components/CompletionOverlay'
import { JobProgress } from '../components/JobProgress'
import { LanguageSelector } from '../components/LanguageSelector'
import { ModelLoadWarningBanner } from '../components/ModelLoadWarningBanner'
import { ModelSelector } from '../components/ModelSelector'
import { Spinner } from '../components/Spinner'
import { TranslateToggle } from '../components/TranslateToggle'
import { UrlInput } from '../components/UrlInput'
import { useJobPolling } from '../hooks/useJobPolling'
import { useLanguages } from '../hooks/useLanguages'
import { useModelValidation } from '../hooks/useModelValidation'
import { useModels } from '../hooks/useModels'

export function UrlPage() {
  const { models, loading: modelsLoading } = useModels()
  const { languages, loading: languagesLoading } = useLanguages()
  const {
    validate,
    reset: resetValidation,
    validating,
    result: validationResult,
    error: validationError,
  } = useModelValidation()

  const [url, setUrl] = useState('')
  const [modelSize, setModelSize] = useState('')
  const [language, setLanguage] = useState('auto')
  const [translate, setTranslate] = useState(false)
  const [pendingSubmit, setPendingSubmit] = useState(false)
  const [urlJobId, setUrlJobId] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [overlayDismissed, setOverlayDismissed] = useState(false)

  const { job } = useJobPolling(urlJobId)

  useEffect(() => {
    if (models.length > 0 && !modelSize) setModelSize(models[0].size)
  }, [models, modelSize])

  // Fires once the model pre-check (triggered from handleTranscribeClick) resolves.
  useEffect(() => {
    if (!pendingSubmit || !validationResult) return
    setPendingSubmit(false)
    if (!validationResult.ok || !url.trim()) return

    setSubmitError(null)
    transcribeUrl(url.trim(), modelSize, language, translate)
      .then((res) => {
        setOverlayDismissed(false)
        setUrlJobId(res.job_id)
      })
      .catch((err) => setSubmitError(err instanceof Error ? err.message : 'Could not start transcription'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingSubmit, validationResult])

  function handleUrlChange(value: string) {
    setUrl(value)
    setUrlJobId(null)
    resetValidation()
  }

  function handleTranscribeClick() {
    if (!url.trim() || !modelSize) return
    resetValidation()
    setUrlJobId(null)
    setSubmitError(null)
    setPendingSubmit(true)
    validate(modelSize)
  }

  const jobInFlight = urlJobId !== null && job?.status !== 'finished' && job?.status !== 'failed'
  const busy = validating || pendingSubmit || jobInFlight
  const showOverlay = job?.status === 'finished' && !overlayDismissed

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-header">
          <h2>Paste a link</h2>
        </div>
        <div className="panel-body">
          <UrlInput value={url} onChange={handleUrlChange} disabled={busy} />

          <div className="field-row">
            <ModelSelector
              models={models}
              value={modelSize}
              onChange={setModelSize}
              disabled={busy || modelsLoading}
            />
            <LanguageSelector
              languages={languages}
              value={language}
              onChange={setLanguage}
              disabled={busy || languagesLoading}
            />
          </div>

          <TranslateToggle checked={translate} onChange={setTranslate} disabled={busy} />

          {validationResult && !validationResult.ok && (
            <ModelLoadWarningBanner
              variant="error"
              message={`Could not load model: ${validationResult.error ?? 'unknown error'}`}
            />
          )}
          {validationResult?.ok && validationResult.fallbackOccurred && (
            <ModelLoadWarningBanner
              variant="warning"
              message="GPU requested but not available — running on CPU, transcription will be slower."
            />
          )}
          {(validationError || submitError) && (
            <ModelLoadWarningBanner variant="error" message={validationError ?? submitError ?? ''} />
          )}
        </div>
        <div className="panel-footer">
          <button
            type="button"
            className="button button-primary"
            onClick={handleTranscribeClick}
            disabled={!url.trim() || !modelSize || busy}
          >
            {busy && <Spinner />}
            {validating ? 'Checking model…' : jobInFlight ? 'Transcribing…' : 'Transcribe'}
          </button>
        </div>
      </section>

      {urlJobId && !showOverlay && (
        <section className="panel">
          <div className="panel-header">
            <h2>Status</h2>
          </div>
          <div className="panel-body">
            <JobProgress job={job} />
          </div>
        </section>
      )}

      {showOverlay && job && (
        <CompletionOverlay
          jobId={job.job_id}
          filename={job.meta.source_filename}
          elapsedMs={job.meta.timings_ms?.total ?? 0}
          detectedLanguage={job.meta.detected_language}
          translated={job.meta.translate}
          onClose={() => setOverlayDismissed(true)}
        />
      )}
    </div>
  )
}
