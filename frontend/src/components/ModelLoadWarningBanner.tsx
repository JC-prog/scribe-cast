import { AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react'

interface Props {
  message: string
  variant?: 'error' | 'warning' | 'success'
}

const ICONS = { error: AlertCircle, warning: AlertTriangle, success: CheckCircle2 }

export function ModelLoadWarningBanner({ message, variant = 'warning' }: Props) {
  const Icon = ICONS[variant]
  return (
    <div className={`banner banner-${variant}`}>
      <Icon size={16} aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}
