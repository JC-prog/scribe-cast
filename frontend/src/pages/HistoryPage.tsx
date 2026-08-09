import { CheckCircle2, RefreshCw, XCircle } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { downloadUrl, listJobs } from '../api/client'
import type { JobStatusResponse } from '../api/types'
import { ModelLoadWarningBanner } from '../components/ModelLoadWarningBanner'
import { Spinner } from '../components/Spinner'
import { formatDuration, formatRelativeTime, STAGE_LABELS } from '../utils/format'

const POLL_INTERVAL_MS = 3000
const TERMINAL_STATUSES = new Set(['finished', 'failed', 'stopped', 'canceled'])

function isTerminal(status: string): boolean {
  return TERMINAL_STATUSES.has(status)
}

function sourceLabel(job: JobStatusResponse): string {
  return job.meta.source_filename ?? job.meta.source_url ?? job.job_id
}

function durationLabel(job: JobStatusResponse): string {
  const totalMs = job.meta.timings_ms?.total
  if (totalMs !== undefined) return formatDuration(totalMs)
  if (job.started_at && job.ended_at) {
    return formatDuration(new Date(job.ended_at).getTime() - new Date(job.started_at).getTime())
  }
  return '—'
}

export function HistoryPage() {
  const [jobs, setJobs] = useState<JobStatusResponse[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const fetchJobs = useCallback(async (showSpinner: boolean): Promise<JobStatusResponse[] | null> => {
    if (showSpinner) setRefreshing(true)
    try {
      const response = await listJobs()
      if (!mountedRef.current) return response.jobs
      setJobs(response.jobs)
      setError(null)
      return response.jobs
    } catch (err) {
      if (mountedRef.current) setError(err instanceof Error ? err.message : 'Failed to load job history')
      return null
    } finally {
      if (showSpinner && mountedRef.current) setRefreshing(false)
    }
  }, [])

  // Self-scheduling: re-arms itself only while some job is still in flight,
  // so the list view stops polling once everything's settled. Shared by the
  // initial mount fetch and the manual refresh button, so a refresh that
  // reveals a newly-active job resumes background polling for it too.
  const scheduleNext = useCallback(
    (result: JobStatusResponse[] | null) => {
      if (!mountedRef.current) return
      if (timerRef.current) clearTimeout(timerRef.current)
      const stillActive = result?.some((job) => !isTerminal(job.status)) ?? true
      if (stillActive) {
        timerRef.current = setTimeout(async () => scheduleNext(await fetchJobs(false)), POLL_INTERVAL_MS)
      }
    },
    [fetchJobs],
  )

  useEffect(() => {
    fetchJobs(false).then(scheduleNext)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [fetchJobs, scheduleNext])

  async function handleManualRefresh() {
    scheduleNext(await fetchJobs(true))
  }

  return (
    <div className="page">
      <section className="panel">
        <div className="panel-header">
          <h2>Recent jobs</h2>
          <button
            type="button"
            className="button"
            onClick={handleManualRefresh}
            disabled={refreshing}
            aria-label="Refresh"
          >
            {refreshing ? <Spinner /> : <RefreshCw size={15} aria-hidden="true" />}
            Refresh
          </button>
        </div>
        <div className="panel-body">
          {error && <ModelLoadWarningBanner variant="error" message={error} />}

          {jobs === null && (
            <div className="job-progress-stage">
              <Spinner /> Loading job history…
            </div>
          )}

          {jobs !== null && jobs.length === 0 && <p className="field-hint">No jobs yet.</p>}

          {jobs !== null && jobs.length > 0 && (
            <div className="history-list">
              <div className="history-row history-row-header">
                <span>Status</span>
                <span>Source</span>
                <span>Model</span>
                <span>Started</span>
                <span>Duration</span>
                <span>Result</span>
              </div>
              {jobs.map((job) => {
                const isFailed = job.status === 'failed'
                const isDone = job.status === 'finished'
                const stage = job.meta.stage ?? job.status
                return (
                  <div key={job.job_id} className="history-row">
                    <span className={`history-status${isFailed ? ' history-status-failed' : ''}`}>
                      {isDone && <CheckCircle2 size={15} aria-hidden="true" />}
                      {isFailed && <XCircle size={15} aria-hidden="true" />}
                      {!isDone && !isFailed && <Spinner />}
                      {isDone ? 'Done' : isFailed ? 'Failed' : (STAGE_LABELS[stage] ?? stage)}
                    </span>
                    <span className="history-source" title={sourceLabel(job)}>
                      {sourceLabel(job)}
                    </span>
                    <span className="history-model">
                      {job.meta.model_size ?? '—'}
                      {job.meta.translate && <span className="badge">translate</span>}
                    </span>
                    <span className="history-time">{job.enqueued_at ? formatRelativeTime(job.enqueued_at) : '—'}</span>
                    <span className="history-duration">{durationLabel(job)}</span>
                    <span className="history-actions">
                      {isDone && (
                        <a className="button" href={downloadUrl(job.job_id)}>
                          Download
                        </a>
                      )}
                      {isFailed && (
                        <span className="history-error" title={job.error ?? job.meta.error ?? undefined}>
                          {job.error ?? job.meta.error ?? 'Unknown error'}
                        </span>
                      )}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
