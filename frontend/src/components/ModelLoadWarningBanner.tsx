interface Props {
  message: string
  variant?: 'error' | 'warning'
}

export function ModelLoadWarningBanner({ message, variant = 'warning' }: Props) {
  return <div className={`banner banner-${variant}`}>{message}</div>
}
