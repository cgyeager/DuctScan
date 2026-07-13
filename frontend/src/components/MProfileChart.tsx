/**
 * M-profile chart: modified refractivity (X) vs height (Y).
 *
 * Renders placeholder sample data until real analysis results arrive.
 * TODO(ui): once /analyze is implemented, verify the real MProfile renders
 * correctly (level ordering, units) and consider annotating detected duct
 * layers as shaded horizontal bands.
 */

import createPlotlyComponent from 'react-plotly.js/factory'
// plotly.js-dist-min ships no types; the factory only needs the runtime object.
// @ts-expect-error -- untyped dist bundle
import Plotly from 'plotly.js-dist-min'
import type { MProfile } from '../api/types'

const Plot = createPlotlyComponent(Plotly)

/** Placeholder: a smooth standard-atmosphere-like M profile (no duct). */
const SAMPLE: MProfile = {
  height_m: Array.from({ length: 30 }, (_, i) => i * 100),
  m_units: Array.from({ length: 30 }, (_, i) => 320 + i * 100 * 0.118),
}

interface Props {
  profile: MProfile | null
}

export function MProfileChart({ profile }: Props) {
  const data = profile ?? SAMPLE
  const isSample = profile === null

  return (
    <section className="panel">
      <h2>
        M-profile{' '}
        {isSample && <span className="panel-hint">(sample data — upload a sounding)</span>}
      </h2>

      <Plot
        data={[
          {
            x: data.m_units,
            y: data.height_m,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#2a78d6', width: 2 },
            hovertemplate: 'M %{x:.1f}<br>%{y:.0f} m<extra></extra>',
          },
        ]}
        layout={{
          autosize: true,
          height: 420,
          margin: { l: 60, r: 16, t: 8, b: 48 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'system-ui, sans-serif', color: '#52514e', size: 12 },
          xaxis: {
            title: { text: 'Modified refractivity M (M-units)' },
            gridcolor: '#e1e0d9',
            zeroline: false,
          },
          yaxis: {
            title: { text: 'Height (m)' },
            gridcolor: '#e1e0d9',
            zeroline: false,
            rangemode: 'tozero',
          },
          showlegend: false,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%' }}
      />
    </section>
  )
}
