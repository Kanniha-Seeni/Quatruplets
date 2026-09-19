import { useState } from "react";
import CodeEditor from "./components/CodeEditor.jsx";
import Copilot from "./components/Copilot.jsx";
import TestRunner from "./components/TestRunner.jsx";

const STARTER_CODE = `# Feature task: write a function that fetches a user by id.
# Try asking the copilot for help writing the database query.

def get_user(user_id):
    pass
`;

export default function App() {
  const [code, setCode] = useState(STARTER_CODE);
  const [sessionId, setSessionId] = useState(null);

  async function submitFinal() {
    try {
      const res = await fetch("http://localhost:8000/api/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, final_code: code }),
      });
      const data = await res.json();
      alert(JSON.stringify(data, null, 2));
    } catch (err) {
      alert(`Could not reach backend: ${err.message}`);
    }
  }

  return (
    <div className="app-shell">
      <div className="editor-column">
        <div className="editor-topbar">
          <div className="editor-title">
            <span className="accent-dot">●</span>Canary — feature task
          </div>
          <button className="btn btn-primary" onClick={submitFinal}>
            Submit
          </button>
        </div>
        <div className="editor-wrapper">
          <CodeEditor code={code} onChange={setCode} />
        </div>
        <div className="test-bar">
          <TestRunner code={code} />
        </div>
      </div>
      <Copilot code={code} sessionId={sessionId} setSessionId={setSessionId} />
    </div>
  );
}
