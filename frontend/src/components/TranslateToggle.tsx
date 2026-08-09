interface Props {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

export function TranslateToggle({ checked, onChange, disabled }: Props) {
  return (
    <label className="field">
      <span className="field-label">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />
        {' '}Translate to English
      </span>
      <p className="field-hint">Whisper only translates into English, not any other target language.</p>
    </label>
  )
}
