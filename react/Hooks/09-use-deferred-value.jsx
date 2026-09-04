import { useState, useDeferredValue, useMemo, memo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useDeferredValue HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: const deferredValue = useDeferredValue(value)

   PURPOSE: Show stale content while fresh content loads in the background.
   React treats the deferred update as lower priority — it can be
   INTERRUPTED by urgent updates (typing, clicking).

   DIAGRAM — How it works:
   ┌──────────────────────────────────────────────────────────────────┐
   │  User types "ab"                                                │
   │                                                                  │
   │  Render 1 (URGENT):   input="ab", deferredInput="a" (stale)    │
   │    → Input updates instantly, list still shows "a" results      │
   │                                                                  │
   │  Render 2 (DEFERRED): input="ab", deferredInput="ab" (caught up)│
   │    → List re-renders with "ab" results in BACKGROUND            │
   │    → If user types "abc" before this finishes, React INTERRUPTS │
   │      and restarts with "abc" instead                            │
   └──────────────────────────────────────────────────────────────────┘

   vs DEBOUNCE/THROTTLE:
   ┌────────────────────┬──────────────────────────────────────┐
   │ debounce/throttle   │ Fixed delay regardless of device    │
   │ useDeferredValue    │ ADAPTIVE — fast device = no delay   │
   │                     │ Interruptible — doesn't block input │
   └────────────────────┴──────────────────────────────────────┘

   GOTCHAS:
   1. useDeferredValue is ONLY useful when combined with memo() or useMemo()
      that uses the deferred value. Without memoization, the component
      re-renders with both old and new values simultaneously.
   2. The deferred render is INTERRUPTIBLE — if a new urgent update comes in
      (e.g., another keystroke), React abandons the deferred render and
      starts over with the new value.
   3. There's no fixed delay — React adapts to the device speed.
      On fast devices, the deferred update appears almost instantly.
   4. useDeferredValue defers the VALUE, not the render.
      The component still re-renders, but with the stale value first.
   5. You can show stale content with CSS (e.g., opacity) to indicate loading.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  input: { padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box", fontSize: 16 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

/* ─── Expensive list component (intentionally slow) ─── */

const SlowList = memo(function SlowList({ text }) {
  const items = useMemo(() => {
    const result = [];
    for (let i = 0; i < 500; i++) {
      if (`Item ${i}`.toLowerCase().includes(text.toLowerCase()) || text === "") {
        result.push(`Item ${i}`);
      }
    }
    // Simulate expensive rendering
    const start = performance.now();
    while (performance.now() - start < 100) { /* busy wait ~100ms */ }
    return result;
  }, [text]);

  return (
    <div style={{ maxHeight: 200, overflowY: "auto", marginTop: 8 }}>
      {items.slice(0, 50).map((item) => (
        <div key={item} style={{ padding: "2px 0", fontSize: 13 }}>{item}</div>
      ))}
      {items.length > 50 && <p style={{ color: "#999", fontSize: 12 }}>...{items.length - 50} more</p>}
      <p style={{ color: "#999", fontSize: 11 }}>Showing {Math.min(items.length, 50)} of {items.length}</p>
    </div>
  );
});

/* ─── Example 1: Without useDeferredValue (laggy typing) ─── */

function WithoutDeferred() {
  const [text, setText] = useState("");

  return (
    <div style={styles.section}>
      <h3>1. WITHOUT useDeferredValue (laggy)</h3>
      <p>Type and notice the input lag — list computation blocks the UI.</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type to filter (will lag)..."
        style={styles.input}
      />
      <SlowList text={text} />
    </div>
  );
}

/* ─── Example 2: With useDeferredValue (smooth typing) ─── */

function WithDeferred() {
  const [text, setText] = useState("");
  const deferredText = useDeferredValue(text);
  const isStale = text !== deferredText;

  return (
    <div style={styles.section}>
      <h3>2. WITH useDeferredValue (smooth!)</h3>
      <p>Type quickly — input stays responsive. List updates in background.</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type to filter (stays responsive)..."
        style={styles.input}
      />
      <div style={{ display: "flex", gap: 8, fontSize: 12, marginTop: 4 }}>
        <span>Input: "{text}"</span>
        <span>Deferred: "{deferredText}"</span>
        {isStale && <span style={{ color: "#ea4335", fontWeight: "bold" }}>STALE (updating...)</span>}
      </div>
      <div style={{ opacity: isStale ? 0.5 : 1, transition: "opacity 0.2s" }}>
        <SlowList text={deferredText} />
      </div>
      <div style={styles.code}>{`const deferredText = useDeferredValue(text);
const isStale = text !== deferredText;

// Show stale content with visual indicator:
<div style={{ opacity: isStale ? 0.5 : 1 }}>
  <SlowList text={deferredText} />
</div>`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseDeferredValueExample() {
  return (
    <div style={styles.container}>
      <h2>useDeferredValue Hook</h2>
      <div style={styles.code}>{`// vs debounce: fixed delay, not adaptive, not interruptible
// vs throttle: fixed rate, not adaptive
// useDeferredValue: adapts to device, interruptible, no fixed timing`}</div>
      <WithoutDeferred />
      <WithDeferred />
    </div>
  );
}
