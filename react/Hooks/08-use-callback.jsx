import { useState, useCallback, memo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useCallback HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: const memoizedFn = useCallback(fn, [deps])

   PURPOSE: Cache a FUNCTION DEFINITION between renders.
   Equivalent to: useMemo(() => fn, [deps])

   WHY IT EXISTS:
   ┌──────────────────────────────────────────────────────────────┐
   │ function Parent() {                                         │
   │   const handleClick = () => { ... };                        │
   │   // ^ NEW function object every render!                    │
   │   //   If Child is wrapped in memo(), it re-renders anyway  │
   │   //   because handleClick is a new reference.              │
   │   return <Child onClick={handleClick} />;                   │
   │ }                                                           │
   │                                                              │
   │ FIX:                                                        │
   │ const handleClick = useCallback(() => { ... }, [deps]);     │
   │ // Same reference between renders → memo(Child) can skip    │
   └──────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. useCallback alone does NOTHING for performance.
      It only helps when the cached function is passed to a memo()'d child
      or used in a useEffect/useMemo dependency array.
   2. useCallback(fn, deps) === useMemo(() => fn, deps)
   3. If deps change, you get a NEW function (cache invalidated).
   4. Don't useCallback everything — it adds overhead for the cache.
      Only use it when you have a memo()'d child that receives the fn.
   5. Functions inside useCallback still close over the render's state/props.
      Use updater functions (setCount(c => c+1)) to avoid stale closures.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  childBox: { padding: 12, border: "1px dashed #ccc", borderRadius: 4, marginTop: 8 },
};

/* ─── Without useCallback: memo is defeated ─── */

const ChildWithoutCallback = memo(function ChildWithoutCallback({ onClick, label }) {
  console.log(`ChildWithoutCallback "${label}" rendered`);
  return (
    <div style={styles.childBox}>
      <span>{label}</span>
      <button style={{ ...styles.btn, fontSize: 12, padding: "4px 10px", marginLeft: 8 }} onClick={onClick}>
        Click
      </button>
      <span style={{ color: "#ea4335", fontSize: 11 }}> (renders every time — check console)</span>
    </div>
  );
});

function WithoutCallbackExample() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  // NEW function every render → defeats memo() on the child
  const handleClick = () => setCount((c) => c + 1);

  return (
    <div style={styles.section}>
      <h3>1. WITHOUT useCallback (memo defeated)</h3>
      <p>Count: {count}</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type to re-render parent..."
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box" }}
      />
      <ChildWithoutCallback onClick={handleClick} label="No useCallback" />
      <div style={styles.code}>{`// Parent re-renders → new handleClick → Child re-renders
const handleClick = () => setCount(c => c + 1);
// memo(Child) can't help — onClick is a new reference!`}</div>
    </div>
  );
}

/* ─── With useCallback: memo works ─── */

const ChildWithCallback = memo(function ChildWithCallback({ onClick, label }) {
  console.log(`ChildWithCallback "${label}" rendered`);
  return (
    <div style={styles.childBox}>
      <span>{label}</span>
      <button style={{ ...styles.btn, fontSize: 12, padding: "4px 10px", marginLeft: 8, background: "#34a853" }} onClick={onClick}>
        Click
      </button>
      <span style={{ color: "#34a853", fontSize: 11 }}> (only renders when deps change)</span>
    </div>
  );
});

function WithCallbackExample() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  // useCallback: same function reference between renders
  // (when deps don't change)
  const handleClick = useCallback(() => {
    setCount((c) => c + 1); // updater function avoids stale closure
  }, []); // no deps → stable forever

  return (
    <div style={styles.section}>
      <h3>2. WITH useCallback (memo works!)</h3>
      <p>Count: {count}</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type — Child won't re-render!"
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box" }}
      />
      <ChildWithCallback onClick={handleClick} label="With useCallback" />
      <div style={styles.code}>{`// Same reference between renders → memo(Child) skips re-render
const handleClick = useCallback(() => {
  setCount(c => c + 1);  // updater avoids stale closure
}, []);  // stable reference`}</div>
    </div>
  );
}

/* ─── Example 3: Multiple Callbacks with Deps ─── */

const ActionButton = memo(function ActionButton({ onAction, label, color }) {
  console.log(`ActionButton "${label}" rendered`);
  return (
    <button style={{ ...styles.btn, background: color }} onClick={onAction}>
      {label}
    </button>
  );
});

function MultiCallbackExample() {
  const [count, setCount] = useState(0);
  const [step, setStep] = useState(1);

  // This callback depends on `step` — recreated when step changes
  const increment = useCallback(() => {
    setCount((c) => c + step);
  }, [step]); // depends on step

  // This callback has no deps — stable forever
  const reset = useCallback(() => {
    setCount(0);
  }, []);

  return (
    <div style={styles.section}>
      <h3>3. Callbacks with Dependencies</h3>
      <p style={{ fontSize: 24, fontFamily: "monospace" }}>{count}</p>
      <div style={{ marginBottom: 8 }}>
        <label>Step size: </label>
        <select value={step} onChange={(e) => setStep(Number(e.target.value))} style={{ padding: 4, borderRadius: 4 }}>
          <option value={1}>1</option>
          <option value={5}>5</option>
          <option value={10}>10</option>
        </select>
        <span style={{ fontSize: 12, color: "#999", marginLeft: 8 }}>
          (changing step re-creates increment callback)
        </span>
      </div>
      <ActionButton onAction={increment} label={`+${step}`} color="#34a853" />
      <ActionButton onAction={reset} label="Reset" color="#ea4335" />
      <div style={styles.code}>{`// increment depends on step → new fn when step changes
const increment = useCallback(() => {
  setCount(c => c + step);
}, [step]);

// reset has no deps → same fn forever
const reset = useCallback(() => setCount(0), []);`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseCallbackExample() {
  return (
    <div style={styles.container}>
      <h2>useCallback Hook</h2>
      <WithoutCallbackExample />
      <WithCallbackExample />
      <MultiCallbackExample />
    </div>
  );
}
