import { useState } from 'react'
import type { AnalyzeResponse } from './api/types'
import { ChatPanel } from './components/ChatPanel'
import { MProfileChart } from './components/MProfileChart'
import { ResultsPanel } from './components/ResultsPanel'
import { SoundingPicker } from './components/SoundingPicker'

export default function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)

  return (
    <main className="app">
      <header>
        <h1>Refractivity Duct Analyzer</h1>
        <p className="panel-hint">
          Pick a station and cycle to fetch a radiosonde sounding (U. Wyoming), compute the
          modified refractivity profile, and detect atmospheric ducts.
        </p>
      </header>
      <div className="grid">
        <div className="col">
          <SoundingPicker onResult={setResult} />
          <ResultsPanel result={result} />
          <ChatPanel result={result}/>
        </div>
        <div className="col">
          <MProfileChart profile={result?.m_profile ?? null} />
        </div>
      </div>
    </main>
  )
}
