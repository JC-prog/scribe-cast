interface Props {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function UrlInput({ value, onChange, disabled }: Props) {
  return (
    <div className="field">
      <span className="field-label">Video URL</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="https://www.youtube.com/watch?v=..."
        disabled={disabled}
      />
      <p className="field-hint">
        Paste a link from YouTube or any other site yt-dlp supports. The audio is downloaded and
        transcribed — nothing is saved to disk beyond the resulting subtitle file.
      </p>
    </div>
  )
}
