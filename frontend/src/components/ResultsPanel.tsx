/**
 * Renders the AnalyzeResponse: sounding metadata and the detected ducts.
 *
 * TODO(ui): once /analyze returns real data, refine formatting (e.g. flag
 * strong ducts, link table rows to highlighted bands on the chart).
 */

import type { AnalyzeResponse } from '../api/types'

interface Props {
  result: AnalyzeResponse | null
}

export function ResultsPanel({ result }: Props) {
  return (
    <section className="panel">
      <h2>Detected ducts</h2>
      {result === null ? (
        <p className="panel-hint">No analysis yet. Upload a sounding to see results here.</p>
      ) : (
        <>

          <p>
            Station <strong>{result.sounding.station_id}</strong>
            {result.sounding.launch_time && <> · {result.sounding.launch_time}</>} ·{' '}
            {result.ducts.length} duct{result.ducts.length === 1 ? '' : 's'} detected
          </p>

          {result.ducts.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Base (m)</th>
                  <th>Top (m)</th>
                  <th>Thickness (m)</th>
                  <th>Strength (M-units)</th>
                </tr>
              </thead>
              <tbody>
                {result.ducts.map((duct, i) => (
                  <tr key={i}>
                    <td>{duct.type}</td>
                    <td>{duct.base_height_m.toFixed(0)}</td>
                    <td>{duct.top_height_m.toFixed(0)}</td>
                    <td>{duct.thickness_m.toFixed(0)}</td>
                    <td>{duct.strength_dm.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  )
}
