/** Typed client for the FastAPI backend. */

import type { AnalyzeResponse, ChatRequest, ChatResponse } from './types'

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

/** Upload a NetCDF sounding for analysis. Returns 501 (ApiError) while the backend is stubbed. */
export async function analyze(file: File): Promise<AnalyzeResponse> {
  const form = new FormData()
  form.append('file', file)
  const response = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    body: form,
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
