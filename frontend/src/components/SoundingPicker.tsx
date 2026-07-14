/**
 * Pick a cycle (date + hour) and a station, then fetch + analyze the sounding
 * from the U. Wyoming database.
 *
 * The plumbing is real; the backend conversion (load_sounding_from_wyoming) is
 * stubbed, so expect a 501 until you implement it.
 *
 * TODO(ui): a later phase adds a second mode here — picking a grid point from
 * GRIB2 model data instead of a station.
 */

import { useState } from 'react'
import { analyze } from '../api/client'
import type { AnalyzeResponse, Station } from '../api/types'
import { StationMapModal } from './StationMapModal'

const HOURS = ['00', '03', '06', '09', '12', '15', '18', '21']

/** Today's date (UTC) as YYYY-MM-DD for the date input's default/max. */
function todayUtc(): string {
  return new Date().toISOString().slice(0, 10)
}

interface Props {
  onResult: (result: AnalyzeResponse) => void
}

export function SoundingPicker({ onResult }: Props) {
  const [date, setDate] = useState(todayUtc())
  const [hour, setHour] = useState('12')
  const [station, setStation] = useState<Station | null>(null)
  const [mapOpen, setMapOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cycleIso = `${date}T${hour}:00:00`

  async function handleAnalyze() {
    if (!station) return
    setBusy(true)
    setError(null)
    try {
      onResult(
        await analyze({ station_id: station.station_id, src: station.src, datetime: cycleIso }),
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>Sounding</h2>
      <div className="picker-row">
        <label>
          Date{' '}
          <input type="date" value={date} max={todayUtc()} onChange={(e) => setDate(e.target.value)} />
        </label>
        <label>
          Hour{' '}
          <select value={hour} onChange={(e) => setHour(e.target.value)}>
            {HOURS.map((h) => (
              <option key={h} value={h}>
                {h} Z
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="picker-row">
        <button onClick={() => setMapOpen(true)}>Choose station…</button>
        <span className={station ? '' : 'panel-hint'}>
          {station
            ? `${station.name || 'Unnamed'} (${station.station_id}, ${station.src})`
            : 'no station selected'}
        </span>
      </div>
      <div className="picker-row">
        <button onClick={handleAnalyze} disabled={!station || busy}>
          {busy ? 'Analyzing…' : 'Get sounding & analyze'}
        </button>
      </div>
      {error && <p className="error">{error}</p>}

      {mapOpen && (
        <StationMapModal
          datetime={cycleIso}
          onClose={() => setMapOpen(false)}
          onSelect={(s) => {
            setStation(s)
            setMapOpen(false)
          }}
        />
      )}
    </section>
  )
}
