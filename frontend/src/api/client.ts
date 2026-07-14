/** Typed client for the FastAPI backend. */

import type { AnalyzeRequest, AnalyzeResponse, ChatRequest, ChatResponse, Station } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

/** Error carrying the HTTP status and the backend's `detail` message. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function parseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText
    try {

      const body = (await response.json()) as { detail?: string }
      if (body.detail) detail = body.detail

    } catch {
      // non-JSON error body; keep statusText
    }
    throw new ApiError(response.status, detail)
  }
  return (await response.json()) as T
}

/** List radiosonde stations available for a cycle (proxied from U. Wyoming). */
export async function getStations(datetime?: string): Promise<Station[]> {
  const query = datetime ? `?datetime=${encodeURIComponent(datetime)}` : ''
  const response = await fetch(`${BASE_URL}/api/stations${query}`)
  return parseOrThrow<Station[]>(response)
}

/** Fetch + analyze one Wyoming sounding. Returns 501 (ApiError) while the backend is stubbed. */
export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return parseOrThrow<AnalyzeResponse>(response)
}

/** Send a chat turn to the (future) LLM layer. Returns 501 (ApiError) while stubbed. */
export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return parseOrThrow<ChatResponse>(response)
}
