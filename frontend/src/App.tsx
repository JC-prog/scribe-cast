import { useState } from 'react'
import { FolderBatchPage } from './pages/FolderBatchPage'
import { UploadPage } from './pages/UploadPage'
import { UrlPage } from './pages/UrlPage'

type Tab = 'upload' | 'url' | 'folder'

function App() {
  const [tab, setTab] = useState<Tab>('upload')

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-mark">SC</div>
        <div className="app-title">
          <h1>scribe-cast</h1>
          <p className="app-subtitle">Local-first video transcription</p>
        </div>
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
          className={`tab${tab === 'url' ? ' tab-active' : ''}`}
          onClick={() => setTab('url')}
        >
          Paste a link
        </button>
        <button
          type="button"
          className={`tab${tab === 'folder' ? ' tab-active' : ''}`}
          onClick={() => setTab('folder')}
        >
          Batch folder
        </button>
      </nav>

      <main>
        {tab === 'upload' && <UploadPage />}
        {tab === 'url' && <UrlPage />}
        {tab === 'folder' && <FolderBatchPage />}
      </main>
    </div>
  )
}

export default App
