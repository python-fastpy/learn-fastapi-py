import { useState, Suspense, lazy } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   Suspense — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: <Suspense fallback={<Loading />}>children</Suspense>

   PURPOSE: Show a fallback while children are loading (lazy components,
   data fetching with Suspense-compatible libraries).

   DIAGRAM:
   ┌────────────────────────────────────────────────────────────────┐
   │  <Suspense fallback={<Spinner />}>                            │
   │    <LazyComponent />                                          │
   │  </Suspense>                                                  │
   │                                                                │
   │  Timeline:                                                    │
   │  ─── Spinner shown ───|── LazyComponent loads ──|── rendered  │
   │                       ^ import() starts          ^ resolves   │
   └────────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. Suspense only works with:
      - React.lazy() components
      - Suspense-compatible data fetching (Relay, Next.js, etc.)
      - NOT with useEffect + setState fetch patterns
   2. Nested Suspense: the closest boundary catches the suspension.
   3. fallback can be any React element, not just a string.
   4. When a suspended component's sibling re-renders, the fallback
      stays — it doesn't unmount/remount.
   5. If already-visible content suspends, React hides it and shows
      the fallback. Use startTransition to keep old content visible.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  spinner: { display: "inline-block", width: 20, height: 20, border: "3px solid #e0e0e0", borderTop: "3px solid #1a73e8", borderRadius: "50%", animation: "spin 1s linear infinite" },
  fallback: { padding: 24, textAlign: "center", background: "#e3f2fd", borderRadius: 8 },
};

/* ─── Simulate lazy loading ─── */

function simulateLazy(Component, delay = 2000) {
  return lazy(() =>
    new Promise((resolve) => setTimeout(() => resolve({ default: Component }), delay))
  );
}

/* ─── Simulated components ─── */

function Chart() {
  return (
    <div style={{ padding: 16, background: "#e8f5e9", borderRadius: 8 }}>
      <h4>Sales Chart</h4>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 80 }}>
        {[40, 65, 30, 80, 55, 70, 90].map((h, i) => (
          <div key={i} style={{ flex: 1, height: `${h}%`, background: "#34a853", borderRadius: "4px 4px 0 0" }} />
        ))}
      </div>
    </div>
  );
}

function UserList() {
  return (
    <div style={{ padding: 16, background: "#fce4ec", borderRadius: 8 }}>
      <h4>Users</h4>
      {["Alice", "Bob", "Charlie", "Diana"].map((name) => (
        <div key={name} style={{ padding: 4 }}>{name}</div>
      ))}
    </div>
  );
}

function Comments() {
  return (
    <div style={{ padding: 16, background: "#fff3e0", borderRadius: 8 }}>
      <h4>Recent Comments</h4>
      {["Great article!", "Thanks for sharing", "Very helpful"].map((c, i) => (
        <div key={i} style={{ padding: 4, fontSize: 13 }}>{c}</div>
      ))}
    </div>
  );
}

const LazyChart = simulateLazy(Chart, 1500);
const LazyUserList = simulateLazy(UserList, 2500);
const LazyComments = simulateLazy(Comments, 1000);

/* ─── Spinner component ─── */

function Spinner({ text = "Loading..." }) {
  return (
    <div style={styles.fallback}>
      <div style={{ ...styles.spinner, marginBottom: 8 }} />
      <p style={{ color: "#1a73e8", margin: 0 }}>{text}</p>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

/* ─── Example 1: Single Suspense Boundary ─── */

function SingleBoundary() {
  const [show, setShow] = useState(false);

  return (
    <div style={styles.section}>
      <h3>1. Single Suspense Boundary</h3>
      <button style={styles.btn} onClick={() => setShow(!show)}>
        {show ? "Hide" : "Load"} Chart
      </button>
      {show && (
        <Suspense fallback={<Spinner text="Loading Chart..." />}>
          <LazyChart />
        </Suspense>
      )}
    </div>
  );
}

/* ─── Example 2: Nested Suspense ─── */

function NestedSuspense() {
  const [show, setShow] = useState(false);

  return (
    <div style={styles.section}>
      <h3>2. Nested Suspense (independent loading)</h3>
      <button style={styles.btn} onClick={() => setShow(!show)}>
        {show ? "Hide" : "Load"} All
      </button>
      {show && (
        <Suspense fallback={<Spinner text="Loading outer..." />}>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <div style={{ flex: 1 }}>
              <Suspense fallback={<Spinner text="Chart..." />}>
                <LazyChart />
              </Suspense>
            </div>
            <div style={{ flex: 1 }}>
              <Suspense fallback={<Spinner text="Users..." />}>
                <LazyUserList />
              </Suspense>
            </div>
            <div style={{ flex: 1 }}>
              <Suspense fallback={<Spinner text="Comments..." />}>
                <LazyComments />
              </Suspense>
            </div>
          </div>
        </Suspense>
      )}
      <div style={styles.code}>{`// Each section loads independently:
<Suspense fallback="Outer loading...">
  <Suspense fallback="Chart..."><LazyChart /></Suspense>
  <Suspense fallback="Users..."><LazyUsers /></Suspense>
  <Suspense fallback="Comments..."><LazyComments /></Suspense>
</Suspense>
// Comments (1s) appears first, Chart (1.5s) next, Users (2.5s) last`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function SuspenseExample() {
  return (
    <div style={styles.container}>
      <h2>Suspense</h2>
      <SingleBoundary />
      <NestedSuspense />
    </div>
  );
}
