import { FileVideo, UploadCloud } from 'lucide-react'
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
      {file ? (
        <FileVideo className="dropzone-icon" size={28} aria-hidden="true" />
      ) : (
        <UploadCloud className="dropzone-icon" size={28} aria-hidden="true" />
      )}
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
