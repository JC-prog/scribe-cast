export function formatDuration(ms: number): string {
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  return `${minutes}m ${remainingSeconds}s`
}

export const STAGE_LABELS: Record<string, string> = {
  queued: 'Queued',
  downloading: 'Downloading',
  loading_model: 'Loading model',
  extracting_audio: 'Extracting audio',
  transcribing: 'Transcribing',
  aligning: 'Aligning',
  writing_subtitles: 'Writing subtitles',
  completed: 'Completed',
  failed: 'Failed',
}

export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  const diffSeconds = Math.round((Date.now() - then) / 1000)

  if (diffSeconds < 5) return 'just now'
  if (diffSeconds < 60) return `${diffSeconds}s ago`
  const minutes = Math.floor(diffSeconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}
