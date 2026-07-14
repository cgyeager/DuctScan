/**
 * Full-screen modal with a Leaflet map of radiosonde stations for the chosen
 * cycle. Clicking a marker opens a details popup with a Select button.
 *
 * Markers are colored by data source (BUFR / TEMP), mirroring the Wyoming site.
 * CircleMarker is used instead of image-based pins so no icon assets are needed.
 */

import 'leaflet/dist/leaflet.css'
import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import { getStations } from '../api/client'
import type { Station } from '../api/types'

// Categorical palette slots 1 & 2 (see MProfileChart for slot 1 usage).
const SRC_COLORS: Record<string, string> = {
  BUFR: '#2a78d6',
  TEMP: '#1baf7a',
}
const SRC_FALLBACK = '#898781'

interface Props {
  /** Cycle time (ISO) whose station list should be shown */
  datetime: string
  onSelect: (station: Station) => void
  onClose: () => void
}

export function StationMapModal({ datetime, onSelect, onClose }: Props) {
  const [stations, setStations] = useState<Station[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getStations(datetime)
      .then((s) => !cancelled && setStations(s))
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : String(err)))
    return () => {
      cancelled = true
    }
  }, [datetime])

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            Choose a station{' '}
            <span className="panel-hint">
              {stations ? `${stations.length} stations for ${datetime}Z` : 'loading…'}
            </span>
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        <MapContainer center={[30, 0]} zoom={2} minZoom={1} className="station-map">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {stations?.map((station) => (
            <CircleMarker
              key={`${station.station_id}-${station.src}`}
              center={[station.latitude, station.longitude]}
              radius={5}
              pathOptions={{
                color: '#fcfcfb',
                weight: 1,
                fillColor: SRC_COLORS[station.src] ?? SRC_FALLBACK,
                fillOpacity: 0.9,
              }}
            >
              <Popup>
                <div className="station-popup">
                  <strong>{station.name || 'Unnamed station'}</strong>
                  <table>
                    <tbody>
                      <tr>
                        <td>ID</td>
                        <td>{station.station_id}</td>
                      </tr>
                      <tr>
                        <td>Lat / Lon</td>
                        <td>
                          {station.latitude.toFixed(2)}, {station.longitude.toFixed(2)}
                        </td>
                      </tr>
                      <tr>
                        <td>Source</td>
                        <td>{station.src}</td>
                      </tr>
                    </tbody>
                  </table>
                  <button onClick={() => onSelect(station)}>Select this station</button>
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
        <p className="panel-hint map-legend">
          <span className="legend-dot" style={{ background: SRC_COLORS.BUFR }} /> BUFR{' '}
          <span className="legend-dot" style={{ background: SRC_COLORS.TEMP }} /> TEMP{' '}
          <span className="legend-dot" style={{ background: SRC_FALLBACK }} /> other
        </p>
      </div>
    </div>
  )
}
