import { useRef, useState } from 'react'

interface Props {
  file: File | null
  onFileSelected: (file: File | null) => void
  disabled?: boolean
}

export function FileDropzone({ file, onFileSelected, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  return (
    <div
      className={`dropzone${dragOver ? ' dropzone-active' : ''}${disabled ? ' dropzone-disabled' : ''}`}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        if (!disabled) setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        if (disabled) return
        const dropped = e.dataTransfer.files[0]
        if (dropped) onFileSelected(dropped)
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        hidden
        disabled={disabled}
        onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
      />
      <svg
        className="dropzone-icon"
        width="28"
        height="28"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M12 16V4" />
        <path d="M6.5 9.5 12 4l5.5 5.5" />
        <path d="M4 16v2.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V16" />
      </svg>
      {file ? (
        <div>
          <strong>{file.name}</strong>
          <div className="dropzone-hint">{(file.size / (1024 * 1024)).toFixed(1)} MB — click to change</div>
        </div>
      ) : (
        <div className="dropzone-hint">Drag & drop a video here, or click to browse</div>
      )}
    </div>
  )
}
