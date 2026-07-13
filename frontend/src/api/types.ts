/**
 * TypeScript mirrors of the backend pydantic models
 * (backend/app/schemas/models.py). Keep the two in sync.
 */

export interface Sounding {
  station_id: string
  launch_time: string | null
  latitude: number | null
  longitude: number | null
  pressure_hpa: number[]
  height_m: number[]
  temperature_k: number[]
  vapor_pressure_hpa: number[]
}

export interface MProfile {
  height_m: number[]
  m_units: number[]
}

export type DuctType = 'surface' | 'elevated'

export interface Duct {
  type: DuctType
  base_height_m: number
  top_height_m: number
  thickness_m: number
  strength_dm: number
}

export interface AnalyzeResponse {
  sounding: Sounding
  m_profile: MProfile
  ducts: Duct[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  history: ChatMessage[]
}

export interface ChatResponse {
  reply: string
}
