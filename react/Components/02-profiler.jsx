import { Profiler, useState, useMemo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   Profiler — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature:
     <Profiler id="name" onRender={callback}>
       <ComponentTree />
     </Profiler>

   PURPOSE: Measure rendering performance of a React subtree.
   The onRender callback fires every time the profiled tree commits an update.

   onRender CALLBACK PARAMS:
   ┌────────────────────┬──────────────────────────────────────────┐
   │ id                 │ The "id" prop of the Profiler           │
   │ phase              │ "mount" | "update" | "nested-update"    │
   │ actualDuration     │ Time spent rendering the committed tree │
   │ baseDuration       │ Time for full re-render without memo    │
   │ startTime          │ Timestamp when React began rendering    │
   │ commitTime         │ Timestamp when React committed          │
   └────────────────────┴──────────────────────────────────────────┘

   GOTCHAS:
   1. Profiler adds overhead — don't use in production unless needed.
      Use React DevTools Profiler for development instead.
   2. actualDuration includes children's render time too.
   3. baseDuration is the WORST CASE — time if nothing was memoized.
   4. Phase "nested-update" means a state update happened during render
      (e.g., from a setState-during-render pattern).
   5. You can nest Profilers to measure different subtrees independently.
   6. Profiler is stripped from production builds by default.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  log: { background: "#f5f5f5", padding: 8, borderRadius: 6, fontSize: 11, fontFamily: "monospace", maxHeight: 150, overflowY: "auto", marginTop: 8 },
  metric: { display: "inline-block", padding: "4px 8px", margin: 2, background: "#e3f2fd", borderRadius: 4, fontSize: 12 },
};

/* ─── Example 1: Basic Profiler ─── */

function ExpensiveList({ count }) {
  const items = useMemo(() => {
    const result = [];
    for (let i = 0; i < count; i++) {
      result.push(`Item ${i + 1}`);
    }
    return result;
  }, [count]);

  return (
    <ul style={{ maxHeight: 100, overflowY: "auto", margin: 0 }}>
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  );
}

function BasicProfiler() {
  const [count, setCount] = useState(50);
  const [logs, setLogs] = useState([]);

  const handleRender = (id, phase, actualDuration, baseDuration, startTime, commitTime) => {
    const entry = `[${id}] phase=${phase} actual=${actualDuration.toFixed(1)}ms base=${baseDuration.toFixed(1)}ms`;
    setLogs((prev) => [entry, ...prev.slice(0, 9)]);
  };

  return (
    <div style={styles.section}>
      <h3>1. Basic Profiler</h3>
      <div>
        <button style={styles.btn} onClick={() => setCount(50)}>50 items</button>
        <button style={styles.btn} onClick={() => setCount(200)}>200 items</button>
        <button style={styles.btn} onClick={() => setCount(500)}>500 items</button>
      </div>

      <Profiler id="ExpensiveList" onRender={handleRender}>
        <ExpensiveList count={count} />
      </Profiler>

      <div style={styles.log}>
        <strong>Profiler Logs:</strong>
        {logs.map((log, i) => <div key={i}>{log}</div>)}
        {logs.length === 0 && <div style={{ color: "#999" }}>Interact to see render metrics...</div>}
      </div>

      <div style={styles.code}>{`// onRender callback params:
function onRender(
  id,              // "ExpensiveList"
  phase,           // "mount" | "update"
  actualDuration,  // ms spent rendering THIS commit
  baseDuration,    // ms for full re-render (no memo)
  startTime,       // when rendering began
  commitTime       // when committed to DOM
) { ... }`}</div>
    </div>
  );
}

/* ─── Example 2: Nested Profilers ─── */

function Header() {
  return <div style={{ padding: 8, background: "#e3f2fd", borderRadius: 4 }}>Header</div>;
}

function Sidebar() {
  const items = Array.from({ length: 20 }, (_, i) => `Nav ${i + 1}`);
  return (
    <div style={{ padding: 8, background: "#e8f5e9", borderRadius: 4, maxHeight: 80, overflowY: "auto" }}>
      {items.map((item) => <div key={item} style={{ fontSize: 12 }}>{item}</div>)}
    </div>
  );
}

function Content({ items }) {
  return (
    <div style={{ padding: 8, background: "#fff3e0", borderRadius: 4, maxHeight: 80, overflowY: "auto" }}>
      {items.map((item, i) => <div key={i} style={{ fontSize: 12 }}>{item}</div>)}
    </div>
  );
}

function NestedProfiler() {
  const [contentItems, setContentItems] = useState(["Post 1", "Post 2", "Post 3"]);
  const [metrics, setMetrics] = useState({});

  const handleRender = (id, phase, actualDuration) => {
    setMetrics((prev) => ({
      ...prev,
      [id]: { phase, duration: actualDuration.toFixed(1) },
    }));
  };

  return (
    <div style={styles.section}>
      <h3>2. Nested Profilers (independent measurements)</h3>
      <button style={styles.btn} onClick={() => setContentItems((prev) => [...prev, `Post ${prev.length + 1}`])}>
        Add Post
      </button>

      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <div style={{ flex: 1 }}>
          <Profiler id="Header" onRender={handleRender}><Header /></Profiler>
        </div>
        <div style={{ flex: 1 }}>
          <Profiler id="Sidebar" onRender={handleRender}><Sidebar /></Profiler>
        </div>
        <div style={{ flex: 2 }}>
          <Profiler id="Content" onRender={handleRender}><Content items={contentItems} /></Profiler>
        </div>
      </div>

      <div style={{ marginTop: 8 }}>
        {Object.entries(metrics).map(([id, m]) => (
          <span key={id} style={styles.metric}>
            {id}: {m.duration}ms ({m.phase})
          </span>
        ))}
      </div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function ProfilerExample() {
  return (
    <div style={styles.container}>
      <h2>Profiler</h2>
      <BasicProfiler />
      <NestedProfiler />
    </div>
  );
}
