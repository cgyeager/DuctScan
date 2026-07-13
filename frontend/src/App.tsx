import { useState } from 'react'
import type { AnalyzeResponse } from './api/types'
import { ChatPanel } from './components/ChatPanel'
import { FileUpload } from './components/FileUpload'
import { MProfileChart } from './components/MProfileChart'
import { ResultsPanel } from './components/ResultsPanel'

export default function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)

  return (
    <main className="app">
      <header>
        <h1>Refractivity Duct Analyzer</h1>
        <p className="panel-hint">
          Upload a radiosonde sounding (NetCDF) to compute the modified refractivity profile
          and detect atmospheric ducts.
        </p>
      </header>
      <div className="grid">
        <div className="col">
          <FileUpload onResult={setResult} />
          <ResultsPanel result={result} />
          <ChatPanel />
        </div>
        <div className="col">
          <MProfileChart profile={result?.m_profile ?? null} />
        </div>
      </div>
    </main>
  )
}
