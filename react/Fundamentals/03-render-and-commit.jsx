import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   RENDER AND COMMIT
   ═══════════════════════════════════════════════════════════════════════════════

   React renders in 3 steps:

   ┌──────────────┐    ┌───────────────────┐    ┌──────────────────┐
   │  1. TRIGGER   │ →  │  2. RENDER         │ →  │  3. COMMIT        │
   │               │    │                   │    │                  │
   │ • Initial     │    │ • React calls     │    │ • Initial: React │
   │   mount       │    │   your component  │    │   uses           │
   │ • State       │    │   function        │    │   appendChild()  │
   │   update      │    │ • Returns JSX     │    │ • Update: React  │
   │   (setState)  │    │ • Reconciliation  │    │   applies ONLY   │
   │               │    │   (diff old/new)  │    │   the MINIMAL    │
   │               │    │                   │    │   DOM changes    │
   └──────────────┘    └───────────────────┘    └──────────────────┘

   GOTCHAS:
   1. "Rendering" in React means CALLING your component function — NOT
      updating the DOM. DOM update happens in the COMMIT phase.
   2. React only updates DOM nodes that CHANGED between renders.
      If nothing changed, React skips the commit entirely.
   3. After commit, browser paints the screen (Browser Paint, not React).
   4. On initial render, React creates ALL DOM nodes with appendChild().
   5. On re-render, React calculates the MINIMUM set of DOM operations
      needed (this is reconciliation / diffing).
   6. React does NOT re-render the entire tree — only the component whose
      state changed + its children.
   7. StrictMode double-renders in dev to catch impure render functions.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  diagram: { background: "#f5f5f5", padding: 16, borderRadius: 6, fontFamily: "monospace", fontSize: 13, whiteSpace: "pre", overflowX: "auto" },
  highlight: { background: "#fff3e0", padding: "2px 4px", borderRadius: 2 },
};

/* ─── Example: Clock (React only updates the time text node) ─── */

function Clock() {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  const updateTime = () => setTime(new Date().toLocaleTimeString());

  return (
    <div style={styles.section}>
      <h3>Clock — Minimal DOM Update</h3>
      <p>
        When you click "Update", React re-renders the whole component function,
        but only commits the <span style={styles.highlight}>time text node</span> to the DOM.
        The h3, p, and button elements are NOT touched.
      </p>
      <div style={{ fontSize: 32, fontFamily: "monospace", margin: "12px 0" }}>{time}</div>
      <button style={styles.btn} onClick={updateTime}>Update Time</button>
      <p style={{ fontSize: 12, color: "#999" }}>
        Open DevTools → Elements → watch for purple flash (DOM mutation). Only the time changes.
      </p>
    </div>
  );
}

/* ─── Example: Demonstrating when React skips commit ─── */

function SameValueDemo() {
  const [count, setCount] = useState(0);

  return (
    <div style={styles.section}>
      <h3>Setting Same Value — React Skips Commit</h3>
      <p>Count: {count}</p>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>Increment</button>
      <button style={{ ...styles.btn, background: "#ea4335" }} onClick={() => setCount(count)}>
        Set Same Value
      </button>
      <p style={{ fontSize: 12, color: "#999" }}>
        "Set Same Value" triggers a render, but React sees the value hasn't changed
        (Object.is comparison), so it bails out — no commit to DOM.
      </p>
    </div>
  );
}

/* ─── Example: Render counter to visualize re-renders ─── */

let renderCount = 0;

function RenderTracker() {
  renderCount++;
  const [text, setText] = useState("");
  const [color, setColor] = useState("black");

  return (
    <div style={styles.section}>
      <h3>Render Tracker</h3>
      <p>This component has rendered <strong>{renderCount}</strong> times.</p>
      <p>Every keystroke triggers: setState → render → diff → commit only changed text.</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type to trigger renders..."
        style={{ padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box" }}
      />
      <div style={{ marginTop: 8 }}>
        <button style={styles.btn} onClick={() => setColor("red")}>Red</button>
        <button style={styles.btn} onClick={() => setColor("blue")}>Blue</button>
        <button style={styles.btn} onClick={() => setColor("green")}>Green</button>
      </div>
      <p style={{ color, fontSize: 18, fontWeight: "bold" }}>Text: {text}</p>
    </div>
  );
}

/* ─── MAIN ─── */

export default function RenderAndCommit() {
  return (
    <div style={styles.container}>
      <h2>Render and Commit</h2>

      {/* 3-step diagram */}
      <div style={styles.diagram}>{`STEP 1: TRIGGER          STEP 2: RENDER           STEP 3: COMMIT
─────────────────       ──────────────────       ──────────────────
• createRoot()          • React calls your       • Initial: appendChild()
  .render(<App/>)         component function       for every DOM node
  (initial mount)       • JSX → React elements   • Re-render: apply ONLY
• setState(newVal)      • Diff old vs new tree     the changed nodes
  (re-render)           • Pure! No side effects   • If nothing changed
                                                   → skip commit entirely`}</div>

      <Clock />
      <SameValueDemo />
      <RenderTracker />
    </div>
  );
}
