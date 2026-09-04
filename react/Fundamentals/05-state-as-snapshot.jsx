import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   STATE AS A SNAPSHOT
   ═══════════════════════════════════════════════════════════════════════════════

   CORE CONCEPT:
   State is FIXED for the duration of one render. Setting state doesn't
   change the variable in the current code — it schedules a NEW render
   with the new value.

   DIAGRAM — What happens when you click:
   ┌─────────────────────────────────────────────────────┐
   │  Render #1: count = 0                               │
   │                                                     │
   │  function handleClick() {                           │
   │    setCount(0 + 1);  // schedules render with 1     │
   │    setCount(0 + 1);  // STILL 0 + 1 = 1 (snapshot!) │
   │    setCount(0 + 1);  // STILL 0 + 1 = 1             │
   │    console.log(count); // logs 0, NOT 1             │
   │  }                                                  │
   │                                                     │
   │  Result: count becomes 1 (not 3)                    │
   └─────────────────────────────────────────────────────┘

   GOTCHAS:
   1. setState does NOT change the variable in currently executing code.
      It only affects the NEXT render.
   2. Multiple setState(value) calls in same handler → all use same snapshot.
      Result: only last value wins (and they're all the same here).
   3. setTimeout/setInterval closures CAPTURE the snapshot value.
      Even if state changes later, the callback uses the OLD value.
   4. This is NOT a bug — it's a feature. Each render has its own
      "snapshot" of state, props, and event handlers.
   5. This is why updater functions (n => n+1) exist — they read the
      PENDING state, not the snapshot.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  result: { fontSize: 32, fontWeight: "bold", margin: "12px 0", fontFamily: "monospace" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 13, whiteSpace: "pre" },
  warning: { background: "#fff3e0", padding: 12, borderRadius: 6, fontSize: 13, marginTop: 8 },
};

/* ─── Example 1: Multiple setState with same snapshot ─── */

function SnapshotCounter() {
  const [count, setCount] = useState(0);

  const handleClick = () => {
    // All three use the SAME snapshot value of count
    setCount(count + 1); // 0 + 1 = 1
    setCount(count + 1); // 0 + 1 = 1 (still using snapshot!)
    setCount(count + 1); // 0 + 1 = 1 (still!)
    // Result: count becomes 1, NOT 3
  };

  return (
    <div style={styles.section}>
      <h3>1. Multiple setState — Same Snapshot</h3>
      <div style={styles.result}>{count}</div>
      <button style={styles.btn} onClick={handleClick}>+1 three times (result: +1 only)</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setCount(0)}>Reset</button>
      <div style={styles.code}>{`setCount(count + 1); // ${count} + 1 = ${count + 1}
setCount(count + 1); // ${count} + 1 = ${count + 1} (same snapshot!)
setCount(count + 1); // ${count} + 1 = ${count + 1} (same!)`}</div>
    </div>
  );
}

/* ─── Example 2: setTimeout captures snapshot ─── */

function SnapshotTimeout() {
  const [count, setCount] = useState(0);
  const [alerts, setAlerts] = useState([]);

  const handleClick = () => {
    setCount(count + 5);

    // This setTimeout captures count = 0 (the snapshot at this render)
    // Even though setCount(count+5) was called above, count is still 0 HERE
    setTimeout(() => {
      // This alert will show the OLD value (snapshot), not the new one
      setAlerts((prev) => [...prev, `Alert saw count = ${count} (snapshot)`]);
    }, 3000);
  };

  return (
    <div style={styles.section}>
      <h3>2. setTimeout Captures Snapshot</h3>
      <div style={styles.result}>{count}</div>
      <button style={styles.btn} onClick={handleClick}>+5 and alert after 3s</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => { setCount(0); setAlerts([]); }}>Reset</button>
      <div style={styles.warning}>
        Click the button → count jumps to 5 immediately.
        But the alert 3s later shows the OLD value ({count}) because
        setTimeout captured the snapshot.
      </div>
      {alerts.map((a, i) => <div key={i} style={{ color: "#ea4335", fontSize: 13 }}>{a}</div>)}
    </div>
  );
}

/* ─── Example 3: Form message snapshot ─── */

function MessageForm() {
  const [to, setTo] = useState("Alice");
  const [message, setMessage] = useState("Hello");
  const [sent, setSent] = useState([]);

  const handleSend = () => {
    // Captures CURRENT snapshot values
    const capturedTo = to;
    const capturedMsg = message;

    setTimeout(() => {
      // Even if user changed the form, we use the SNAPSHOT values
      setSent((prev) => [...prev, `Sent "${capturedMsg}" to ${capturedTo}`]);
    }, 2000);
  };

  return (
    <div style={styles.section}>
      <h3>3. Form Snapshot (change fields after clicking Send)</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <select value={to} onChange={(e) => setTo(e.target.value)} style={{ padding: 6, borderRadius: 4 }}>
          <option>Alice</option>
          <option>Bob</option>
          <option>Charlie</option>
        </select>
        <input value={message} onChange={(e) => setMessage(e.target.value)} style={{ flex: 1, padding: 6, borderRadius: 4, border: "1px solid #ccc" }} />
        <button style={styles.btn} onClick={handleSend}>Send (2s delay)</button>
      </div>
      <div style={styles.warning}>
        Click Send, then QUICKLY change the recipient and message.
        After 2s, the sent message shows the ORIGINAL values — the snapshot at click time.
      </div>
      {sent.map((s, i) => <div key={i} style={{ color: "#34a853", fontSize: 13 }}>✓ {s}</div>)}
    </div>
  );
}

/* ─── MAIN ─── */

export default function StateAsSnapshot() {
  return (
    <div style={styles.container}>
      <h2>State as a Snapshot</h2>
      <div style={styles.code}>{`// State is FIXED within a render
// Think of it as: React "takes a photo" of state when rendering
// All code in that render sees the SAME state value`}</div>
      <SnapshotCounter />
      <SnapshotTimeout />
      <MessageForm />
    </div>
  );
}
