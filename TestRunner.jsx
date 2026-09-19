import { useEffect, useRef, useState } from "react";

export default function TestRunner({ code }) {
  const pyodideRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [output, setOutput] = useState("");

  useEffect(() => {
    async function load() {
      // loadPyodide is injected globally by the <script> tag in index.html
      pyodideRef.current = await window.loadPyodide();
      setReady(true);
    }
    load();
  }, []);

  async function runTests() {
    if (!pyodideRef.current) return;
    setOutput("Running…");
    try {
      // Very simple demo: run the candidate's code, then a hardcoded test.
      // Replace this with real per-task test suites.
      await pyodideRef.current.runPythonAsync(code);
      const result = await pyodideRef.current.runPythonAsync(`
try:
    assert True  # TODO: replace with real assertions for this task
    "PASS"
except AssertionError as e:
    f"FAIL: {e}"
`);
      setOutput(String(result));
    } catch (err) {
      setOutput(`ERROR: ${err}`);
    }
  }

  return (
    <div>
      <button className="btn btn-secondary" onClick={runTests} disabled={!ready}>
        {ready ? "Run tests" : "Loading Python sandbox…"}
      </button>
      {output && <div className="test-output">{output}</div>}
    </div>
  );
}
