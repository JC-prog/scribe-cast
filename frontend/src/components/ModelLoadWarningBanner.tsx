import { AlertCircle, AlertTriangle } from 'lucide-react'

interface Props {
  message: string
  variant?: 'error' | 'warning'
}

export function ModelLoadWarningBanner({ message, variant = 'warning' }: Props) {
  const Icon = variant === 'error' ? AlertCircle : AlertTriangle
  return (
    <div className={`banner banner-${variant}`}>
      <Icon size={16} aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}
