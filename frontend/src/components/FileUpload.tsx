/**
 * Upload a NetCDF sounding and trigger analysis.
 *
 * The plumbing is real; the backend pipeline is stubbed, so expect a 501
 * ("Analysis pipeline not implemented yet") until you implement the core.
 */

import { useState } from 'react'
import { analyze } from '../api/client'
import type { AnalyzeResponse } from '../api/types'

interface Props {
  onResult: (result: AnalyzeResponse) => void
}

export function FileUpload({ onResult }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleAnalyze() {
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      onResult(await analyze(file))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>Sounding upload</h2>
      <div className="upload-row">
        <input
          type="file"
          accept=".nc,application/x-netcdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button onClick={handleAnalyze} disabled={!file || busy}>
          {busy ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  )
}
