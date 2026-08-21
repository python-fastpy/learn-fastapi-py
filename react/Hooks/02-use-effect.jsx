import { useState, useEffect, useRef } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useEffect HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: useEffect(setup, dependencies?)

   LIFECYCLE DIAGRAM:
   ┌──────────────────────────────────────────────────────────────┐
   │  Mount    → setup() runs                                    │
   │  Update   → cleanup() from PREVIOUS render, then setup()    │
   │  Unmount  → cleanup() runs                                  │
   └──────────────────────────────────────────────────────────────┘

   DEPENDENCY ARRAY:
   ┌─────────────────────────┬──────────────────────────────────────┐
   │ useEffect(fn)           │ Runs after EVERY render              │
   │ useEffect(fn, [])       │ Runs ONLY on mount                   │
   │ useEffect(fn, [a, b])   │ Runs when a or b changes (Object.is) │
   └─────────────────────────┴──────────────────────────────────────┘

   GOTCHAS:
   1. CLEANUP runs BEFORE the next effect, and on unmount.
   2. RACE CONDITION FIX: use `ignore` flag in async fetching:
        useEffect(() => {
          let ignore = false;
          fetchData().then(data => { if (!ignore) setData(data); });
          return () => { ignore = true; };
        }, [id]);
   3. Effects run AFTER paint (non-blocking). Use useLayoutEffect for
      before-paint (blocking, rare).
   4. setInterval with stale closure: use updater function:
        setCount(c => c + 1)  // ✓ always reads latest
        setCount(count + 1)   // ✗ captures snapshot
   5. StrictMode double-fires effects in dev (mount → unmount → mount)
      to help catch missing cleanups.
   6. Objects/arrays as deps re-trigger every render (new reference).
      Move them inside the effect or memoize.
   7. Don't use effects for things that can be computed during render
      (use useMemo or derive from state/props instead).
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  log: { background: "#f5f5f5", padding: 8, borderRadius: 6, fontSize: 12, maxHeight: 120, overflowY: "auto", marginTop: 8 },
};

/* ─── Example 1: Basic Effect with Cleanup ─── */

function DocumentTitle() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    document.title = `Count: ${count}`;
    // Cleanup: restore title when component unmounts
    return () => {
      document.title = "React App";
    };
  }, [count]); // Only re-run when count changes

  return (
    <div style={styles.section}>
      <h3>1. Document Title (basic effect + cleanup)</h3>
      <p>Check the browser tab title — it updates with count.</p>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>Count: {count}</button>
      <div style={styles.code}>{`useEffect(() => {
  document.title = \`Count: \${count}\`;
  return () => { document.title = "React App"; }; // cleanup
}, [count]); // dependency: re-run when count changes`}</div>
    </div>
  );
}

/* ─── Example 2: Event Listener (setup + cleanup) ─── */

function WindowSize() {
  const [size, setSize] = useState({ w: window.innerWidth, h: window.innerHeight });

  useEffect(() => {
    const handleResize = () => {
      setSize({ w: window.innerWidth, h: window.innerHeight });
    };

    window.addEventListener("resize", handleResize);

    // CLEANUP: remove listener to prevent memory leak
    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []); // [] = only on mount/unmount

  return (
    <div style={styles.section}>
      <h3>2. Window Resize (event listener cleanup)</h3>
      <p>Window: {size.w} x {size.h}px — resize browser to see updates.</p>
      <div style={styles.code}>{`useEffect(() => {
  window.addEventListener("resize", handler);
  return () => window.removeEventListener("resize", handler);
}, []); // mount-only: empty deps`}</div>
    </div>
  );
}

/* ─── Example 3: Race Condition Fix with ignore flag ─── */

function fakeFetch(userId) {
  return new Promise((resolve) => {
    const delay = Math.random() * 2000 + 500;
    setTimeout(() => resolve({ id: userId, name: `User ${userId}`, loadTime: `${Math.round(delay)}ms` }), delay);
  });
}

function UserProfile() {
  const [userId, setUserId] = useState(1);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let ignore = false; // Race condition guard
    setLoading(true);

    fakeFetch(userId).then((data) => {
      if (!ignore) {
        // Only update if this effect hasn't been cleaned up
        // (i.e., userId hasn't changed while we were fetching)
        setUser(data);
        setLoading(false);
      }
    });

    return () => {
      // If userId changes before fetch completes, this cleanup runs,
      // setting ignore = true so the stale response is discarded
      ignore = true;
    };
  }, [userId]);

  return (
    <div style={styles.section}>
      <h3>3. Race Condition Fix (ignore flag)</h3>
      <p>Click users rapidly — stale responses are ignored.</p>
      {[1, 2, 3, 4, 5].map((id) => (
        <button
          key={id}
          style={{ ...styles.btn, background: userId === id ? "#1a73e8" : "#ccc", color: userId === id ? "#fff" : "#000" }}
          onClick={() => setUserId(id)}
        >
          User {id}
        </button>
      ))}
      <div style={{ marginTop: 8 }}>
        {loading ? "Loading..." : user ? `${user.name} (loaded in ${user.loadTime})` : "No user"}
      </div>
      <div style={styles.code}>{`useEffect(() => {
  let ignore = false;  // ← guard flag
  fetch(url).then(data => {
    if (!ignore) setData(data);  // only if still relevant
  });
  return () => { ignore = true; }; // cleanup: discard stale
}, [userId]);`}</div>
    </div>
  );
}

/* ─── Example 4: setInterval with Updater ─── */

function IntervalCounter() {
  const [count, setCount] = useState(0);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;

    const id = setInterval(() => {
      // MUST use updater function! count from closure is stale (snapshot)
      setCount((c) => c + 1);
      // setCount(count + 1) ← WRONG: always adds 1 to the snapshot value
    }, 1000);

    return () => clearInterval(id);
  }, [running]); // only restart when running changes

  return (
    <div style={styles.section}>
      <h3>4. setInterval — Updater vs Stale Closure</h3>
      <p style={{ fontSize: 28, fontFamily: "monospace" }}>{count}</p>
      <button style={styles.btn} onClick={() => setRunning(!running)}>
        {running ? "Stop" : "Start"}
      </button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setCount(0)}>Reset</button>
      <div style={styles.code}>{`// ✗ setCount(count + 1)    → always 0+1=1 (stale closure)
// ✓ setCount(c => c + 1)  → reads latest pending state`}</div>
    </div>
  );
}

/* ─── Example 5: Effect Lifecycle Logger ─── */

function EffectLogger({ value }) {
  const [logs, setLogs] = useState([]);
  const mountCount = useRef(0);

  useEffect(() => {
    mountCount.current++;
    const msg = `[${mountCount.current}] Setup — value="${value}"`;
    setLogs((prev) => [...prev, msg]);

    return () => {
      setLogs((prev) => [...prev, `[${mountCount.current}] Cleanup — value="${value}"`]);
    };
  }, [value]);

  return (
    <div style={styles.log}>
      {logs.map((l, i) => <div key={i}>{l}</div>)}
    </div>
  );
}

function EffectLifecycle() {
  const [text, setText] = useState("hello");

  return (
    <div style={styles.section}>
      <h3>5. Effect Lifecycle Logger</h3>
      <p>Type to see cleanup → setup cycle:</p>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4 }}
      />
      <EffectLogger value={text} />
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseEffectExample() {
  return (
    <div style={styles.container}>
      <h2>useEffect Hook</h2>
      <DocumentTitle />
      <WindowSize />
      <UserProfile />
      <IntervalCounter />
      <EffectLifecycle />
    </div>
  );
}
