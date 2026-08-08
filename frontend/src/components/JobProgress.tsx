import type { JobStatusResponse } from '../api/types'
import { formatDuration } from '../utils/format'

const STAGE_LABELS: Record<string, string> = {
  queued: 'Queued',
  loading_model: 'Loading model',
  extracting_audio: 'Extracting audio',
  transcribing: 'Transcribing',
  writing_subtitles: 'Writing subtitles',
  completed: 'Completed',
  failed: 'Failed',
}

interface Props {
  job: JobStatusResponse | null
  label?: string
}

export function JobProgress({ job, label }: Props) {
  if (!job) {
    return (
      <div className="job-progress">
        {label && <div className="job-progress-label">{label}</div>}
        <div className="job-progress-stage">Starting…</div>
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
      <div className="job-progress-stage">
        {isDone ? 'Done' : isFailed ? `Failed: ${job.error ?? job.meta.error ?? 'Unknown error'}` : stageLabel}
      </div>
      {isDone && totalMs !== undefined && <div className="job-progress-time">Took {formatDuration(totalMs)}</div>}
    </div>
  )
}
