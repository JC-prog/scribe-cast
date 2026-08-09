import { useState } from 'react'
import type { Tab } from './components/Sidebar'
import { Sidebar } from './components/Sidebar'
import { AdminPage } from './pages/AdminPage'
import { FolderBatchPage } from './pages/FolderBatchPage'
import { HistoryPage } from './pages/HistoryPage'
import { UploadPage } from './pages/UploadPage'
import { UrlPage } from './pages/UrlPage'

function App() {
  const [tab, setTab] = useState<Tab>('upload')

  return (
    <div className="app-shell">
      <Sidebar tab={tab} onTabChange={setTab} />

      <main className="app-main">
        {tab === 'upload' && <UploadPage />}
        {tab === 'url' && <UrlPage />}
        {tab === 'folder' && <FolderBatchPage />}
        {tab === 'history' && <HistoryPage />}
        {tab === 'admin' && <AdminPage />}
      </main>
    </div>
  )
}

export default App
