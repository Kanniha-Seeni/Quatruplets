import { useState } from "react";

const BACKEND_URL = "http://localhost:8000";

export default function Copilot({ code, sessionId, setSessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/api/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, code, message: userMsg.text }),
      });

      if (!res.ok) {
        // Surface the backend's actual error instead of failing silently.
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Backend returned ${res.status}`);
      }

      const data = await res.json();
      if (!sessionId) setSessionId(data.session_id);
      setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `⚠️ ${err.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="copilot-panel">
      <div className="copilot-header">AI Copilot</div>
      <div className="copilot-messages">
        {messages.length === 0 && (
          <div className="copilot-empty">
            Ask the copilot for help with the task on the left.
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`bubble ${m.role === "user" ? "bubble-user" : "bubble-assistant"} ${
              m.isError ? "bubble-error" : ""
            }`}
          >
            <div className="bubble-label">{m.role === "user" ? "You" : "Copilot"}</div>
            <div className="bubble-text">{m.text}</div>
          </div>
        ))}
        {loading && <div className="bubble bubble-assistant bubble-loading">Copilot is thinking…</div>}
      </div>
      <div className="copilot-input-row">
        <input
          className="copilot-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask your AI copilot..."
        />
        <button className="btn btn-primary" onClick={send}>Send</button>
      </div>
    </div>
  );
}
