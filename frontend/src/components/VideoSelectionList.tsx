import type { DiscoveredVideo } from '../api/types'

interface Props {
  videos: DiscoveredVideo[]
  selected: Set<string>
  onToggle: (path: string) => void
  onToggleAll: (checked: boolean) => void
}

export function VideoSelectionList({ videos, selected, onToggle, onToggleAll }: Props) {
  const allSelected = videos.length > 0 && videos.every((video) => selected.has(video.absolute_path))

  if (videos.length === 0) {
    return <p className="field-hint">No videos found in this folder.</p>
  }

  return (
    <div className="video-list">
      <label className="video-row video-row-header">
        <input type="checkbox" checked={allSelected} onChange={(e) => onToggleAll(e.target.checked)} />
        <span>Select all ({videos.length} found)</span>
      </label>
      {videos.map((video) => (
        <label key={video.absolute_path} className="video-row">
          <input
            type="checkbox"
            checked={selected.has(video.absolute_path)}
            onChange={() => onToggle(video.absolute_path)}
          />
          <span className="video-path">{video.relative_path}</span>
          <span className="video-size">{(video.size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
          {video.existing_srt && <span className="badge">already has .srt</span>}
        </label>
      ))}
    </div>
  )
}
