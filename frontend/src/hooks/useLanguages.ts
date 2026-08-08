import { useEffect, useState } from 'react'
import { getLanguages } from '../api/client'
import type { LanguageInfo } from '../api/types'

export function useLanguages() {
  const [languages, setLanguages] = useState<LanguageInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getLanguages()
      .then((res) => {
        if (!cancelled) setLanguages(res.languages)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load languages')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { languages, loading, error }
}
