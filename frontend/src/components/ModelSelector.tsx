import type { ModelInfo } from '../api/types'

interface Props {
  models: ModelInfo[]
  value: string
  onChange: (size: string) => void
  disabled?: boolean
}

export function ModelSelector({ models, value, onChange, disabled }: Props) {
  return (
    <label className="field">
      <span className="field-label">Model</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        <option value="" disabled>
          Select a model…
        </option>
        {models.map((model) => (
          <option key={model.size} value={model.size}>
            {model.label} — {model.hint}
          </option>
        ))}
      </select>
    </label>
  )
}
