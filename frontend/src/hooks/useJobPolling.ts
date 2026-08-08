import { useEffect, useRef, useState } from 'react'
import { getBatchStatus, getJobStatus } from '../api/client'
import type { BatchStatusResponse, JobStatusResponse } from '../api/types'

const POLL_INTERVAL_MS = 1200
const TERMINAL_STATUSES = new Set(['finished', 'failed', 'stopped', 'canceled'])

function isTerminal(status: string): boolean {
  return TERMINAL_STATUSES.has(status)
}

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setJob(null)
    setError(null)
    if (!jobId) return

    let cancelled = false

    const poll = async () => {
      try {
        const status = await getJobStatus(jobId)
        if (cancelled) return
        setJob(status)
        if (!isTerminal(status.status)) {
          timerRef.current = setTimeout(poll, POLL_INTERVAL_MS)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to fetch job status')
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [jobId])

  return {
    job,
    error,
    isDone: job ? isTerminal(job.status) : false,
  }
}

export function useBatchPolling(batchId: string | null) {
  const [batch, setBatch] = useState<BatchStatusResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setBatch(null)
    setError(null)
    if (!batchId) return

    let cancelled = false

    const poll = async () => {
      try {
        const status = await getBatchStatus(batchId)
        if (cancelled) return
        setBatch(status)
        const allDone = status.jobs.every((job) => isTerminal(job.status))
        if (!allDone) {
          timerRef.current = setTimeout(poll, POLL_INTERVAL_MS)
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to fetch batch status')
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [batchId])

  const isDone = batch ? batch.jobs.every((job) => isTerminal(job.status)) : false

  return { batch, error, isDone }
}
