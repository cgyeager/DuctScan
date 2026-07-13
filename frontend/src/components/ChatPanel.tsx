/**
 * Chat panel for the future RAG/agentic LLM layer.
 *
 * The UI plumbing is real; the backend returns 501 until the LLM layer exists.
 * TODO(llm): once /chat is implemented, consider streaming responses and
 * passing analysis context (current AnalyzeResponse) with each request.
 */

import { useState } from 'react'
import { chat } from '../api/client'
import type { ChatMessage } from '../api/types'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSend() {
    const message = input.trim()
    if (!message || busy) return
    const history = messages
    setMessages([...history, { role: 'user', content: message }])
    setInput('')
    setBusy(true)
    setError(null)
    try {
      const response = await chat({ message, history })
      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }])
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel">
      <h2>
        Ask about this sounding <span className="panel-hint">(LLM layer — coming later)</span>
      </h2>
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="panel-hint">
            Future feature: chat with an LLM grounded in the analysis results.
          </p>
        )}
        {messages.map((m, i) => (
          <p key={i} className={`chat-message chat-${m.role}`}>
            <strong>{m.role === 'user' ? 'You' : 'Assistant'}:</strong> {m.content}
          </p>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      <div className="upload-row">
        <input
          type="text"
          value={input}
          placeholder="e.g. Why is this duct classified as elevated?"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} disabled={!input.trim() || busy}>
          {busy ? 'Sending…' : 'Send'}
        </button>
      </div>
    </section>
  )
}
