import { FolderOpen, History, Link as LinkIcon, Settings, Upload } from 'lucide-react'

export type Tab = 'upload' | 'url' | 'folder' | 'history' | 'admin'

interface NavItem {
  tab: Tab
  label: string
  icon: typeof Upload
}

const NAV_ITEMS: NavItem[] = [
  { tab: 'upload', label: 'Upload video', icon: Upload },
  { tab: 'url', label: 'Paste a link', icon: LinkIcon },
  { tab: 'folder', label: 'Batch folder', icon: FolderOpen },
  { tab: 'history', label: 'History', icon: History },
  { tab: 'admin', label: 'Admin', icon: Settings },
]

interface Props {
  tab: Tab
  onTabChange: (tab: Tab) => void
}

export function Sidebar({ tab, onTabChange }: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="app-mark">SC</div>
        <div className="app-title">
          <h1>scribe-cast</h1>
          <p className="app-subtitle">Local-first transcription</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ tab: itemTab, label, icon: Icon }) => (
          <button
            key={itemTab}
            type="button"
            className={`nav-item${tab === itemTab ? ' nav-item-active' : ''}`}
            onClick={() => onTabChange(itemTab)}
            aria-label={label}
          >
            <Icon size={17} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
