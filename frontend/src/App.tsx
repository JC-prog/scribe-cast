import { useState } from 'react'
import { FolderBatchPage } from './pages/FolderBatchPage'
import { UploadPage } from './pages/UploadPage'

type Tab = 'upload' | 'folder'

function App() {
  const [tab, setTab] = useState<Tab>('upload')

  return (
    <div className="app">
      <header className="app-header">
        <h1>scribe-cast</h1>
        <p className="app-subtitle">Local-first video transcription</p>
      </header>

      <nav className="tabs">
        <button
          type="button"
          className={`tab${tab === 'upload' ? ' tab-active' : ''}`}
          onClick={() => setTab('upload')}
        >
          Upload video
        </button>
        <button
          type="button"
          className={`tab${tab === 'folder' ? ' tab-active' : ''}`}
          onClick={() => setTab('folder')}
        >
          Batch folder
        </button>
      </nav>

      <main>{tab === 'upload' ? <UploadPage /> : <FolderBatchPage />}</main>
    </div>
  )
}

export default App
