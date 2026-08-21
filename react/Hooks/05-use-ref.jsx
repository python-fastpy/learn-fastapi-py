import { useState, useRef, useEffect, forwardRef } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useRef HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: const ref = useRef(initialValue)
   Returns: { current: initialValue }

   TWO MAIN USES:
   ┌───────────────────────────────────────────────────────────────┐
   │ 1. PERSIST values between renders WITHOUT triggering re-render│
   │    - Timer IDs, previous values, instance counters            │
   │    - Like a class instance variable                           │
   │                                                               │
   │ 2. ACCESS DOM elements directly                               │
   │    - <input ref={inputRef} /> → inputRef.current = DOM node   │
   │    - Focus, scroll, measure, animate                          │
   └───────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. Changing ref.current does NOT trigger a re-render.
      React doesn't "know" when you change it.
   2. Don't READ or WRITE ref.current during render.
      Do it in event handlers or effects.
   3. ref.current is mutable — unlike state, you can mutate freely.
   4. On first render, DOM refs are null (DOM doesn't exist yet).
      Access them in useEffect or event handlers.
   5. forwardRef is needed to pass refs to custom components
      (React won't forward ref prop automatically).
   6. useRef(value) creates the object ONCE. On re-renders, it
      returns the SAME object (same reference).
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4 },
};

/* ─── Example 1: Stopwatch (ref for interval ID) ─── */

function Stopwatch() {
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef(null); // Stores interval ID between renders

  const start = () => {
    if (running) return;
    setRunning(true);
    const startTime = Date.now() - elapsed;
    intervalRef.current = setInterval(() => {
      setElapsed(Date.now() - startTime);
    }, 10);
  };

  const stop = () => {
    setRunning(false);
    clearInterval(intervalRef.current); // Access the stored interval ID
  };

  const reset = () => {
    stop();
    setElapsed(0);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => clearInterval(intervalRef.current);
  }, []);

  const format = (ms) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const centis = Math.floor((ms % 1000) / 10);
    return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}.${String(centis).padStart(2, "0")}`;
  };

  return (
    <div style={styles.section}>
      <h3>1. Stopwatch (ref stores interval ID)</h3>
      <p style={{ fontSize: 36, fontFamily: "monospace", margin: "8px 0" }}>{format(elapsed)}</p>
      <button style={styles.btn} onClick={start} disabled={running}>Start</button>
      <button style={{ ...styles.btn, background: "#ea4335" }} onClick={stop} disabled={!running}>Stop</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={reset}>Reset</button>
      <div style={styles.code}>{`// ref persists the interval ID without causing re-renders
const intervalRef = useRef(null);
intervalRef.current = setInterval(fn, 10);
clearInterval(intervalRef.current);`}</div>
    </div>
  );
}

/* ─── Example 2: DOM Access (focus, scroll) ─── */

function DOMAccess() {
  const inputRef = useRef(null);
  const divRef = useRef(null);

  const focusInput = () => {
    inputRef.current.focus();
  };

  const scrollToBottom = () => {
    divRef.current.scrollTop = divRef.current.scrollHeight;
  };

  return (
    <div style={styles.section}>
      <h3>2. DOM Access (focus, scroll)</h3>
      <input ref={inputRef} style={styles.input} placeholder="Click Focus to focus me" />
      <button style={styles.btn} onClick={focusInput}>Focus Input</button>

      <div ref={divRef} style={{ height: 80, overflowY: "auto", border: "1px solid #ccc", borderRadius: 4, padding: 8, marginTop: 8 }}>
        {Array.from({ length: 20 }, (_, i) => <p key={i} style={{ margin: 2 }}>Line {i + 1}</p>)}
      </div>
      <button style={styles.btn} onClick={scrollToBottom}>Scroll to Bottom</button>
      <div style={styles.code}>{`<input ref={inputRef} />
inputRef.current.focus();       // DOM method
divRef.current.scrollTop = ...;  // DOM property`}</div>
    </div>
  );
}

/* ─── Example 3: Render Count (ref doesn't cause re-render) ─── */

function RenderCounter() {
  const [text, setText] = useState("");
  const renderCount = useRef(0);

  // This runs every render but changing ref.current doesn't trigger another
  renderCount.current++;

  return (
    <div style={styles.section}>
      <h3>3. Render Count (ref vs state)</h3>
      <p>This component has rendered <strong>{renderCount.current}</strong> times.</p>
      <p>Changing ref.current doesn't trigger re-render. The count updates only because typing causes a state-driven re-render.</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type to trigger renders..."
        style={{ ...styles.input, width: "100%", boxSizing: "border-box" }}
      />
    </div>
  );
}

/* ─── Example 4: Previous Value ─── */

function usePrevious(value) {
  const prev = useRef();
  useEffect(() => {
    prev.current = value;
  }, [value]);
  return prev.current;
}

function PreviousValue() {
  const [count, setCount] = useState(0);
  const prevCount = usePrevious(count);

  return (
    <div style={styles.section}>
      <h3>4. Previous Value (custom hook with ref)</h3>
      <p>Current: <strong>{count}</strong> | Previous: <strong>{prevCount ?? "none"}</strong></p>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>+1</button>
      <button style={styles.btn} onClick={() => setCount(count - 1)}>-1</button>
      <div style={styles.code}>{`function usePrevious(value) {
  const prev = useRef();
  useEffect(() => { prev.current = value; }, [value]);
  return prev.current; // returns PREVIOUS value (effect hasn't run yet)
}`}</div>
    </div>
  );
}

/* ─── Example 5: forwardRef (pass ref to child component) ─── */

const FancyInput = forwardRef(function FancyInput(props, ref) {
  return (
    <input
      ref={ref}
      style={{ ...styles.input, border: "2px solid #1a73e8", background: "#e3f2fd" }}
      placeholder={props.placeholder}
    />
  );
});

function ForwardRefExample() {
  const fancyRef = useRef(null);

  return (
    <div style={styles.section}>
      <h3>5. forwardRef (exposing DOM to parent)</h3>
      <FancyInput ref={fancyRef} placeholder="I'm a FancyInput" />
      <button style={styles.btn} onClick={() => fancyRef.current.focus()}>Focus FancyInput</button>
      <div style={styles.code}>{`// Without forwardRef, ref on a custom component doesn't work
const FancyInput = forwardRef((props, ref) => {
  return <input ref={ref} {...props} />;
});
// Now parent can: <FancyInput ref={myRef} />`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseRefExample() {
  return (
    <div style={styles.container}>
      <h2>useRef Hook</h2>
      <Stopwatch />
      <DOMAccess />
      <RenderCounter />
      <PreviousValue />
      <ForwardRefExample />
    </div>
  );
}
