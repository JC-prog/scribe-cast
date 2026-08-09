import { Loader2 } from 'lucide-react'

interface Props {
  size?: number
}

export function Spinner({ size = 14 }: Props) {
  return <Loader2 size={size} className="spinner" aria-hidden="true" />
}
