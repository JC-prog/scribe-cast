import { useEffect, useState } from 'react'
import { scanFolder, startFolderBatch } from '../api/client'
import type { DiscoveredVideo } from '../api/types'
import { FolderPathInput } from '../components/FolderPathInput'
import { JobProgress } from '../components/JobProgress'
import { LanguageSelector } from '../components/LanguageSelector'
import { ModelLoadWarningBanner } from '../components/ModelLoadWarningBanner'
import { ModelSelector } from '../components/ModelSelector'
import { VideoSelectionList } from '../components/VideoSelectionList'
import { useBatchPolling } from '../hooks/useJobPolling'
import { useLanguages } from '../hooks/useLanguages'
import { useModelValidation } from '../hooks/useModelValidation'
import { useModels } from '../hooks/useModels'

const TERMINAL_STATUSES = new Set(['finished', 'failed', 'stopped', 'canceled'])

export function FolderBatchPage() {
  const { models, loading: modelsLoading } = useModels()
  const { languages, loading: languagesLoading } = useLanguages()
  const {
    validate,
    reset: resetValidation,
    validating,
    result: validationResult,
    error: validationError,
  } = useModelValidation()

  const [folderPath, setFolderPath] = useState('')
  const [modelSize, setModelSize] = useState('')
  const [language, setLanguage] = useState('auto')
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [videos, setVideos] = useState<DiscoveredVideo[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [pendingBatch, setPendingBatch] = useState(false)
  const [batchId, setBatchId] = useState<string | null>(null)
  const [batchError, setBatchError] = useState<string | null>(null)

  const { batch } = useBatchPolling(batchId)

  useEffect(() => {
    if (models.length > 0 && !modelSize) setModelSize(models[0].size)
  }, [models, modelSize])

  useEffect(() => {
    if (!pendingBatch || !validationResult) return
    setPendingBatch(false)
    if (!validationResult.ok || selected.size === 0) return

    setBatchError(null)
    startFolderBatch(folderPath, Array.from(selected), modelSize, language)
      .then((res) => setBatchId(res.batch_id))
      .catch((err) => setBatchError(err instanceof Error ? err.message : 'Failed to start batch'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingBatch, validationResult])

  async function handleScan() {
    setScanning(true)
    setScanError(null)
    setVideos([])
    setSelected(new Set())
    setBatchId(null)
    try {
      const res = await scanFolder(folderPath)
      setVideos(res.videos)
      setSelected(new Set(res.videos.map((video) => video.absolute_path)))
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Failed to scan folder')
    } finally {
      setScanning(false)
    }
  }

  function toggleVideo(path: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(path)) next.delete(path)
      else next.add(path)
      return next
    })
  }

  function toggleAll(checked: boolean) {
    setSelected(checked ? new Set(videos.map((video) => video.absolute_path)) : new Set())
  }

  function handleStartBatch() {
    if (selected.size === 0 || !modelSize) return
    resetValidation()
    setBatchId(null)
    setBatchError(null)
    setPendingBatch(true)
    validate(modelSize)
  }

  const batchInFlight = batch !== null && !batch.jobs.every((jobStatus) => TERMINAL_STATUSES.has(jobStatus.status))
  const busy = validating || pendingBatch || batchInFlight

  return (
    <div className="page">
      <h2>Batch transcribe a folder</h2>
      <FolderPathInput value={folderPath} onChange={setFolderPath} onScan={handleScan} scanning={scanning} disabled={busy} />
      {scanError && <ModelLoadWarningBanner variant="error" message={scanError} />}

      {videos.length > 0 && (
        <>
          <VideoSelectionList videos={videos} selected={selected} onToggle={toggleVideo} onToggleAll={toggleAll} />

          <div className="field-row">
            <ModelSelector models={models} value={modelSize} onChange={setModelSize} disabled={busy || modelsLoading} />
            <LanguageSelector
              languages={languages}
              value={language}
              onChange={setLanguage}
              disabled={busy || languagesLoading}
            />
          </div>

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
          {(validationError || batchError) && (
            <ModelLoadWarningBanner variant="error" message={validationError ?? batchError ?? ''} />
          )}

          <button
            type="button"
            className="button button-primary"
            onClick={handleStartBatch}
            disabled={selected.size === 0 || busy}
          >
            {validating ? 'Checking model…' : `Transcribe ${selected.size} video${selected.size === 1 ? '' : 's'}`}
          </button>
        </>
      )}

      {batch && (
        <div className="batch-progress">
          {batch.jobs.map((jobStatus) => (
            <JobProgress key={jobStatus.job_id} job={jobStatus} label={jobStatus.meta.source_filename} />
          ))}
        </div>
      )}
    </div>
  )
}
