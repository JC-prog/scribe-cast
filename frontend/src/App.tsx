import { useState } from 'react'
import type { Tab } from './components/Sidebar'
import { Sidebar } from './components/Sidebar'
import { FolderBatchPage } from './pages/FolderBatchPage'
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
      </main>
    </div>
  )
}

export default App
