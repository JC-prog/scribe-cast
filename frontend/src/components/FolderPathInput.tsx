import { Spinner } from './Spinner'

interface Props {
  value: string
  onChange: (value: string) => void
  onScan: () => void
  scanning: boolean
  disabled?: boolean
}

export function FolderPathInput({ value, onChange, onScan, scanning, disabled }: Props) {
  return (
    <div className="field">
      <span className="field-label">Folder path</span>
      <div className="folder-input-row">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="/data/your-folder"
          disabled={disabled}
        />
        <button
          type="button"
          className="button button-primary"
          onClick={onScan}
          disabled={disabled || scanning || !value.trim()}
        >
          {scanning && <Spinner />}
          {scanning ? 'Scanning…' : 'Scan'}
        </button>
      </div>
      <p className="field-hint">
        Must be a container-visible path under <code>/data/...</code> (mapped from the{' '}
        <code>DATA_DIR</code> you set in <code>.env</code>). Searches the folder itself plus one level of
        subfolders.
      </p>
    </div>
  )
}
