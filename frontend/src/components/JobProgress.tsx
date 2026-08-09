import { CheckCircle2, XCircle } from 'lucide-react'
import type { JobStatusResponse } from '../api/types'
import { formatDuration, STAGE_LABELS } from '../utils/format'
import { Spinner } from './Spinner'

interface Props {
  job: JobStatusResponse | null
  label?: string
}

export function JobProgress({ job, label }: Props) {
  if (!job) {
    return (
      <div className="job-progress">
        {label && <div className="job-progress-label">{label}</div>}
        <div className="job-progress-stage">
          <Spinner />
          Starting…
        </div>
        <div className="job-progress-bar-track">
          <div className="job-progress-bar-fill" />
        </div>
      </div>
    )
  }

  const stage = job.meta.stage ?? job.status
  const stageLabel = STAGE_LABELS[stage] ?? stage
  const isFailed = job.status === 'failed' || stage === 'failed'
  const isDone = job.status === 'finished'
  const totalMs = job.meta.timings_ms?.total

  return (
    <div className={`job-progress${isFailed ? ' job-progress-failed' : ''}`}>
      {label && <div className="job-progress-label">{label}</div>}
      <div className={`job-progress-stage${isDone ? ' job-progress-stage-success' : ''}`}>
        {isDone && <CheckCircle2 size={15} aria-hidden="true" />}
        {isFailed && <XCircle size={15} aria-hidden="true" />}
        {!isDone && !isFailed && <Spinner />}
        {isDone ? 'Done' : isFailed ? `Failed: ${job.error ?? job.meta.error ?? 'Unknown error'}` : stageLabel}
      </div>
      <div className="job-progress-bar-track">
        <div
          className={`job-progress-bar-fill${isDone ? ' job-progress-bar-done' : ''}${isFailed ? ' job-progress-bar-error' : ''}`}
        />
      </div>
      {isDone && totalMs !== undefined && <div className="job-progress-time">Took {formatDuration(totalMs)}</div>}
    </div>
  )
}
