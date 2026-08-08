import { useEffect, useState } from 'react'
import { getModels } from '../api/client'
import type { ModelInfo } from '../api/types'

export function useModels() {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getModels()
      .then((res) => {
        if (!cancelled) setModels(res.models)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load models')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { models, loading, error }
}
