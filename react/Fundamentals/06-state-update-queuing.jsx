import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   STATE UPDATE QUEUING
   ═══════════════════════════════════════════════════════════════════════════════

   React QUEUES all setState calls within an event handler and processes
   them after the handler finishes. Two types of updates:

   TYPE 1: REPLACE — setState(value)
     Adds "replace with value" to the queue. Ignores pending state.

   TYPE 2: UPDATER — setState(n => n + 1)
     Adds a function to the queue. Receives pending state as argument.

   QUEUE PROCESSING TABLE:
   ┌──────────────────────┬─────────────┬──────────┐
   │ Queued Update        │ n (pending) │ Returns  │
   ├──────────────────────┼─────────────┼──────────┤
   │ "replace with 5"     │ (ignored)   │ 5        │
   │ n => n + 1           │ prev result │ prev + 1 │
   └──────────────────────┴─────────────┴──────────┘

   THE 4 CRITICAL CASES (starting from count = 0):

   CASE 1: setCount(0+1), setCount(0+1), setCount(0+1)
     Queue: [replace 1, replace 1, replace 1]
     Processing: 0 → 1 → 1 → 1
     RESULT: 1 (all used snapshot value 0)

   CASE 2: setCount(n=>n+1), setCount(n=>n+1), setCount(n=>n+1)
     Queue: [fn, fn, fn]
     Processing: 0 →(0+1=1) →(1+1=2) →(2+1=3)
     RESULT: 3 (each updater reads pending state)

   CASE 3: setCount(n=>n+1), setCount(n=>n+1), setCount(45)
     Queue: [fn, fn, replace 45]
     Processing: 0 →(0+1=1) →(1+1=2) → 45
     RESULT: 45 (final replace overwrites everything)

   CASE 4: setCount(n=>n+1), setCount(n=>n+1), setCount(0+1)
     Queue: [fn, fn, replace 1]
     Processing: 0 →(0+1=1) →(1+1=2) → 1
     RESULT: 1 (replace uses snapshot value 0+1=1)

   GOTCHAS:
   1. Use UPDATER (n => n+1) when next state depends on previous.
   2. REPLACE (setState(value)) always uses the snapshot, not pending.
   3. A replace after updaters OVERWRITES all updater results.
   4. React batches ALL updates in an event handler — only ONE re-render.
   5. By convention, name updater arg with first letter: `a` for age,
      `n` for number, `prev` for generic.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  result: { fontSize: 48, fontWeight: "bold", margin: "12px 0", fontFamily: "monospace", textAlign: "center" },
  queue: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  step: { padding: "4px 0", borderBottom: "1px solid #e0e0e0" },
  expected: { textAlign: "center", fontSize: 14, fontWeight: "bold", marginTop: 8 },
};

function CaseDemo({ title, description, onClickHandler, expectedResult, queueSteps }) {
  const [count, setCount] = useState(0);

  return (
    <div style={styles.section}>
      <h3>{title}</h3>
      <p style={{ fontSize: 13 }}>{description}</p>
      <div style={styles.result}>{count}</div>
      <div style={{ textAlign: "center" }}>
        <button style={styles.btn} onClick={() => onClickHandler(count, setCount)}>
          Run Queue
        </button>
        <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setCount(0)}>
          Reset
        </button>
      </div>
      <div style={styles.expected}>Expected result: {expectedResult}</div>
      <div style={styles.queue}>
        <strong>Queue processing (from count={count}):</strong>
        {"\n"}{queueSteps(count)}
      </div>
    </div>
  );
}

export default function StateUpdateQueuing() {
  return (
    <div style={styles.container}>
      <h2>State Update Queuing</h2>

      {/* CASE 1: Replace x3 */}
      <CaseDemo
        title="Case 1: Replace × 3"
        description="setCount(count+1) three times — all use snapshot value"
        onClickHandler={(count, setCount) => {
          setCount(count + 1); // replace with (snapshot + 1)
          setCount(count + 1); // replace with (snapshot + 1) — same!
          setCount(count + 1); // replace with (snapshot + 1) — same!
        }}
        expectedResult="1 (from 0), then 2, 3..."
        queueSteps={(c) => `  replace ${c + 1} → result: ${c + 1}
  replace ${c + 1} → result: ${c + 1}  (overwrites)
  replace ${c + 1} → result: ${c + 1}  (overwrites)
  FINAL: ${c + 1}`}
      />

      {/* CASE 2: Updater x3 */}
      <CaseDemo
        title="Case 2: Updater × 3"
        description="setCount(n => n+1) three times — each reads pending state"
        onClickHandler={(_count, setCount) => {
          setCount((n) => n + 1); // 0→1 (or pending→pending+1)
          setCount((n) => n + 1); // 1→2
          setCount((n) => n + 1); // 2→3
        }}
        expectedResult="+3 each click"
        queueSteps={(c) => `  n => n+1: pending=${c} → returns ${c + 1}
  n => n+1: pending=${c + 1} → returns ${c + 2}
  n => n+1: pending=${c + 2} → returns ${c + 3}
  FINAL: ${c + 3}`}
      />

      {/* CASE 3: Updater + Updater + Replace */}
      <CaseDemo
        title="Case 3: Updater + Updater + Replace(45)"
        description="Updaters calculate, then replace overwrites everything"
        onClickHandler={(count, setCount) => {
          setCount((n) => n + 1);
          setCount((n) => n + 1);
          setCount(45); // replace — ignores all pending work!
        }}
        expectedResult="45 (replace always wins)"
        queueSteps={(c) => `  n => n+1: pending=${c} → returns ${c + 1}
  n => n+1: pending=${c + 1} → returns ${c + 2}
  replace 45 → result: 45  (OVERWRITES everything)
  FINAL: 45`}
      />

      {/* CASE 4: Updater + Updater + Replace(snapshot+1) */}
      <CaseDemo
        title="Case 4: Updater + Updater + Replace(count+1)"
        description="Replace uses SNAPSHOT value (0+1=1), not pending"
        onClickHandler={(count, setCount) => {
          setCount((n) => n + 1);
          setCount((n) => n + 1);
          setCount(count + 1); // count is snapshot (0), so this is replace(1)
        }}
        expectedResult="1 (from 0) — replace uses snapshot, not pending"
        queueSteps={(c) => `  n => n+1: pending=${c} → returns ${c + 1}
  n => n+1: pending=${c + 1} → returns ${c + 2}
  replace ${c + 1} → result: ${c + 1}  (snapshot: ${c}+1)
  FINAL: ${c + 1}`}
      />

      {/* Rule of Thumb */}
      <div style={{ ...styles.section, background: "#e8f5e9" }}>
        <h3>Rule of Thumb</h3>
        <div style={styles.queue}>{`// Next state depends on current state? → Use UPDATER
setCount(n => n + 1);  // ✓ reads pending state

// Setting a completely new value? → Use REPLACE
setCount(42);          // ✓ just replaces

// NEVER mix updaters + replace in same batch
// unless you understand the queue processing order`}</div>
      </div>
    </div>
  );
}
