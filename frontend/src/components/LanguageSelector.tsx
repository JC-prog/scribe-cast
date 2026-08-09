import type { LanguageInfo } from '../api/types'

interface Props {
  languages: LanguageInfo[]
  value: string
  onChange: (code: string) => void
  disabled?: boolean
}

export function LanguageSelector({ languages, value, onChange, disabled }: Props) {
  return (
    <label className="field">
      <span className="field-label">Audio language</span>
      <select value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
        {languages.map((language) => (
          <option key={language.code} value={language.code}>
            {language.label}
          </option>
        ))}
      </select>
      <p className="field-hint">
        The language spoken in the source audio (or auto-detect), not an output language. To get English
        text from non-English audio, use "Translate to English" below.
      </p>
    </label>
  )
}
