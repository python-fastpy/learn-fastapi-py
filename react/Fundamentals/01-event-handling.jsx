import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   EVENT HANDLING IN REACT
   ═══════════════════════════════════════════════════════════════════════════════

   DIAGRAM — Event Propagation:
   ┌─────────────────────────────────────────────┐
   │  CAPTURE PHASE (top → down)                 │
   │  onClickCapture on <div>  ←── fires FIRST   │
   │       │                                     │
   │       ▼                                     │
   │  BUBBLE PHASE (bottom → up)                 │
   │  onClick on <button>     ←── fires SECOND   │
   │       │                                     │
   │       ▼                                     │
   │  onClick on <div>        ←── fires THIRD    │
   └─────────────────────────────────────────────┘

   GOTCHAS:
   1. onClick={handleClick}   → CORRECT (passes reference)
      onClick={handleClick()} → WRONG (calls immediately during render!)
   2. e.stopPropagation() stops React event bubbling to parent
   3. e.preventDefault() stops browser default (form submit, link navigation)
   4. Events propagate UP by default (bubble). Use onClickCapture for top-down.
   5. All React events are synthetic (SyntheticEvent wrapping native event).
   6. Event handlers receive the event as first argument automatically.
   7. Inline arrow: onClick={() => handleClick(id)} — creates new fn each render.
   8. stopPropagation only stops React tree bubbling; native listeners on
      document.addEventListener still fire.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "1px solid #ccc" },
  log: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontSize: 13, maxHeight: 150, overflowY: "auto", marginTop: 8 },
  outer: { padding: 20, background: "#e3f2fd", borderRadius: 8, cursor: "pointer" },
  inner: { padding: 16, background: "#bbdefb", borderRadius: 6, cursor: "pointer", margin: 8 },
  deepInner: { padding: 12, background: "#90caf9", borderRadius: 4, cursor: "pointer", margin: 8 },
};

export default function EventHandlingExample() {
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev]);
  };

  const clearLogs = () => setLogs([]);

  /* ─── EXAMPLE 1: Passing vs Calling ─── */
  const handleClick = () => addLog("Button clicked!");
  const handleClickWithArg = (name) => addLog(`Hello, ${name}!`);

  /* ─── EXAMPLE 2: Event Object ─── */
  const handleInputChange = (e) => {
    addLog(`Input value: "${e.target.value}" | Type: ${e.type}`);
  };

  /* ─── EXAMPLE 3: Propagation ─── */
  const handleOuter = () => addLog("OUTER div clicked (bubble)");
  const handleInner = () => addLog("INNER div clicked (bubble)");
  const handleDeep = () => addLog("DEEP button clicked");

  /* ─── EXAMPLE 4: stopPropagation ─── */
  const handleDeepStop = (e) => {
    e.stopPropagation(); // Stops bubbling — parent onClick won't fire
    addLog("DEEP clicked — propagation STOPPED");
  };

  /* ─── EXAMPLE 5: Capture Phase ─── */
  const handleOuterCapture = () => addLog("OUTER capture (fires FIRST, top-down)");

  /* ─── EXAMPLE 6: preventDefault ─── */
  const handleFormSubmit = (e) => {
    e.preventDefault(); // Prevents page reload on form submit
    addLog("Form submitted (default prevented — no page reload)");
  };

  const handleLinkClick = (e) => {
    e.preventDefault(); // Prevents navigation
    addLog("Link clicked (navigation prevented)");
  };

  return (
    <div style={styles.container}>
      <h2>Event Handling</h2>
      <button style={styles.btn} onClick={clearLogs}>Clear Logs</button>

      {/* ─── PASSING vs CALLING ─── */}
      <div style={styles.section}>
        <h3>1. Passing vs Calling</h3>
        <pre>{`✓ onClick={handleClick}          → passes reference
✗ onClick={handleClick()}        → calls NOW during render!
✓ onClick={() => handleClick()}  → arrow wraps the call`}</pre>

        {/* CORRECT — passes function reference */}
        <button style={styles.btn} onClick={handleClick}>
          Correct: onClick={"handleClick"}
        </button>

        {/* CORRECT — arrow function for arguments */}
        <button style={styles.btn} onClick={() => handleClickWithArg("React")}>
          With arg: () =&gt; handleClick("React")
        </button>
      </div>

      {/* ─── EVENT OBJECT ─── */}
      <div style={styles.section}>
        <h3>2. Event Object (SyntheticEvent)</h3>
        <p>React wraps native events in SyntheticEvent. Access e.target, e.type, etc.</p>
        <input
          placeholder="Type here..."
          onChange={handleInputChange}
          style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #ccc" }}
        />
      </div>

      {/* ─── PROPAGATION (BUBBLING) ─── */}
      <div style={styles.section}>
        <h3>3. Event Propagation (Bubbling)</h3>
        <p>Click the deepest element — watch events bubble UP.</p>
        <div style={styles.outer} onClick={handleOuter}>
          OUTER (onClick)
          <div style={styles.inner} onClick={handleInner}>
            INNER (onClick)
            <button style={{ ...styles.btn, ...styles.deepInner }} onClick={handleDeep}>
              DEEP (onClick)
            </button>
          </div>
        </div>
      </div>

      {/* ─── STOP PROPAGATION ─── */}
      <div style={styles.section}>
        <h3>4. stopPropagation</h3>
        <p>Click deep button — only its handler fires, parent onClick is blocked.</p>
        <div style={styles.outer} onClick={handleOuter}>
          OUTER
          <div style={styles.inner} onClick={handleInner}>
            INNER
            <button style={{ ...styles.btn, ...styles.deepInner }} onClick={handleDeepStop}>
              DEEP (stops propagation)
            </button>
          </div>
        </div>
      </div>

      {/* ─── CAPTURE PHASE ─── */}
      <div style={styles.section}>
        <h3>5. Capture Phase (onClickCapture)</h3>
        <p>Capture fires TOP → DOWN, before bubble phase.</p>
        <div style={styles.outer} onClickCapture={handleOuterCapture} onClick={handleOuter}>
          OUTER (has both onClickCapture + onClick)
          <button style={{ ...styles.btn, ...styles.inner }} onClick={handleDeep}>
            DEEP button
          </button>
        </div>
        <pre>{`Order: OUTER capture → DEEP click → OUTER bubble`}</pre>
      </div>

      {/* ─── PREVENT DEFAULT ─── */}
      <div style={styles.section}>
        <h3>6. preventDefault</h3>
        <form onSubmit={handleFormSubmit}>
          <button style={styles.btn} type="submit">Submit Form (no reload)</button>
        </form>
        <a href="https://google.com" onClick={handleLinkClick} style={{ color: "#1a73e8" }}>
          Click link (no navigation)
        </a>
      </div>

      {/* ─── LOG OUTPUT ─── */}
      <div style={styles.log}>
        {logs.length === 0 && <span style={{ color: "#999" }}>Click something...</span>}
        {logs.map((log, i) => <div key={i}>{log}</div>)}
      </div>
    </div>
  );
}
