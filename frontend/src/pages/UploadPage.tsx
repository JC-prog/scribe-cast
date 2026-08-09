import { useEffect, useState } from 'react'
import { uploadVideo } from '../api/client'
import { CompletionOverlay } from '../components/CompletionOverlay'
import { FileDropzone } from '../components/FileDropzone'
import { JobProgress } from '../components/JobProgress'
import { LanguageSelector } from '../components/LanguageSelector'
import { ModelLoadWarningBanner } from '../components/ModelLoadWarningBanner'
import { ModelSelector } from '../components/ModelSelector'
import { Spinner } from '../components/Spinner'
import { TranslateToggle } from '../components/TranslateToggle'
import { useJobPolling } from '../hooks/useJobPolling'
import { useLanguages } from '../hooks/useLanguages'
import { useModelValidation } from '../hooks/useModelValidation'
import { useModels } from '../hooks/useModels'

export function UploadPage() {
  const { models, loading: modelsLoading } = useModels()
  const { languages, loading: languagesLoading } = useLanguages()
  const {
    validate,
    reset: resetValidation,
    validating,
    result: validationResult,
    error: validationError,
  } = useModelValidation()

  const [file, setFile] = useState<File | null>(null)
  const [modelSize, setModelSize] = useState('')
  const [language, setLanguage] = useState('auto')
  const [translate, setTranslate] = useState(false)
  const [pendingUpload, setPendingUpload] = useState(false)
  const [uploadJobId, setUploadJobId] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [overlayDismissed, setOverlayDismissed] = useState(false)

  const { job } = useJobPolling(uploadJobId)

  useEffect(() => {
    if (models.length > 0 && !modelSize) setModelSize(models[0].size)
  }, [models, modelSize])

  // Fires once the model pre-check (triggered from handleTranscribeClick) resolves.
  useEffect(() => {
    if (!pendingUpload || !validationResult) return
    setPendingUpload(false)
    if (!validationResult.ok || !file) return

    setUploadError(null)
    uploadVideo(file, modelSize, language, translate)
      .then((res) => {
        setOverlayDismissed(false)
        setUploadJobId(res.job_id)
      })
      .catch((err) => setUploadError(err instanceof Error ? err.message : 'Upload failed'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingUpload, validationResult])

  function handleFileSelected(selected: File | null) {
    setFile(selected)
    setUploadJobId(null)
    resetValidation()
  }

  function handleTranscribeClick() {
    if (!file || !modelSize) return
    resetValidation()
    setUploadJobId(null)
    setUploadError(null)
    setPendingUpload(true)
    validate(modelSize)
  }

  const jobInFlight = uploadJobId !== null && job?.status !== 'finished' && job?.status !== 'failed'
  const busy = validating || pendingUpload || jobInFlight
  const showOverlay = job?.status === 'finished' && !overlayDismissed

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-header">
          <h2>Upload a video</h2>
        </div>
        <div className="panel-body">
          <FileDropzone file={file} onFileSelected={handleFileSelected} disabled={busy} />

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
          {(validationError || uploadError) && (
            <ModelLoadWarningBanner variant="error" message={validationError ?? uploadError ?? ''} />
          )}
        </div>
        <div className="panel-footer">
          <button
            type="button"
            className="button button-primary"
            onClick={handleTranscribeClick}
            disabled={!file || !modelSize || busy}
          >
            {busy && <Spinner />}
            {validating ? 'Checking model…' : jobInFlight ? 'Transcribing…' : 'Transcribe'}
          </button>
        </div>
      </section>

      {uploadJobId && !showOverlay && (
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
          filename={file?.name}
          elapsedMs={job.meta.timings_ms?.total ?? 0}
          detectedLanguage={job.meta.detected_language}
          translated={job.meta.translate}
          onClose={() => setOverlayDismissed(true)}
        />
      )}
    </div>
  )
}
