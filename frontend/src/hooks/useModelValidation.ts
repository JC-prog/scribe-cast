import { useCallback, useState } from 'react'
import { validateModel } from '../api/client'
import { useJobPolling } from './useJobPolling'

export interface ModelValidationResult {
  ok: boolean
  deviceUsed?: string
  fallbackOccurred?: boolean
  error: string | null
}

/**
 * Shared by UploadPage and FolderBatchPage: enqueues a model-load pre-check
 * (POST /api/models/validate) and polls it to completion. Runs on the same
 * worker/model cache real jobs use, so a successful validation leaves the
 * model warm — the follow-up transcription job's model_load timing should
 * be ~0.
 */
export function useModelValidation() {
  const [jobId, setJobId] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const [startError, setStartError] = useState<string | null>(null)
  const { job, error: pollError, isDone } = useJobPolling(jobId)

  const validate = useCallback(async (modelSize: string) => {
    setStarting(true)
    setStartError(null)
    setJobId(null)
    try {
      const response = await validateModel(modelSize)
      setJobId(response.job_id)
    } catch (err) {
      setStartError(err instanceof Error ? err.message : 'Failed to start model validation')
    } finally {
      setStarting(false)
    }
  }, [])

  const reset = useCallback(() => {
    setJobId(null)
    setStartError(null)
  }, [])

  const validating = starting || (jobId !== null && !isDone)

  let result: ModelValidationResult | null = null
  if (isDone && job) {
    if (job.status === 'finished' && job.result) {
      result = {
        ok: Boolean(job.result.ok),
        deviceUsed: job.result.device_used as string | undefined,
        fallbackOccurred: Boolean(job.result.fallback_occurred),
        error: (job.result.error as string | null) ?? null,
      }
    } else {
      result = { ok: false, error: job.error ?? 'Model validation failed' }
    }
  }

  return { validate, reset, validating, result, error: startError ?? pollError }
}
