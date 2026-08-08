import { downloadUrl } from '../api/client'
import { formatDuration } from '../utils/format'

interface Props {
  jobId: string
  filename?: string
  elapsedMs: number
  detectedLanguage?: string | null
  onClose: () => void
}

export function CompletionOverlay({ jobId, filename, elapsedMs, detectedLanguage, onClose }: Props) {
  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div className="overlay-card" onClick={(e) => e.stopPropagation()}>
        <h2>Transcription complete</h2>
        {filename && <p className="overlay-filename">{filename}</p>}
        <p className="overlay-time">
          Took <strong>{formatDuration(elapsedMs)}</strong>
        </p>
        {detectedLanguage && <p className="overlay-language">Detected language: {detectedLanguage}</p>}
        <div className="overlay-actions">
          <a className="button button-primary" href={downloadUrl(jobId)} download>
            Download subtitle
          </a>
          <button type="button" className="button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
