import { useState, lazy, Suspense } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   React.lazy + Suspense — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature:
     const LazyComponent = lazy(() => import('./Component'))
     <Suspense fallback={<Loading />}><LazyComponent /></Suspense>

   PURPOSE: Code splitting — load component code only when it's needed.
   The JS bundle for the lazy component is downloaded on first render.

   DIAGRAM:
   ┌────────────────────────────────────────────────────────────────┐
   │  Initial bundle: App + routes (small)                         │
   │                                                                │
   │  User clicks "Dashboard":                                     │
   │    1. React sees lazy(Dashboard) for the first time            │
   │    2. Suspense shows fallback ("Loading...")                   │
   │    3. Browser downloads Dashboard chunk (dashboard.js)         │
   │    4. React replaces fallback with <Dashboard />               │
   │                                                                │
   │  Next time: chunk is cached, no loading state                 │
   └────────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. lazy() MUST be called at module level, not inside components.
      Inside a component, it creates a new lazy wrapper every render.
   2. The dynamic import must return a module with a DEFAULT export.
      lazy(() => import('./MyComponent')) expects export default.
   3. Suspense boundary catches the "loading" state. Without it,
      React throws an error.
   4. NESTED Suspense: inner boundary catches first; outer is fallback
      for anything not caught by inner.
   5. Error handling: wrap Suspense in an Error Boundary to catch
      failed imports (network errors, etc.).
   6. You can have multiple lazy components inside one Suspense —
      they all share the same fallback.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  fallback: { padding: 24, textAlign: "center", background: "#fff3e0", borderRadius: 8, color: "#e65100" },
  tab: { display: "inline-block", padding: "8px 16px", cursor: "pointer", borderRadius: "4px 4px 0 0" },
};

/* Since we can't actually do dynamic imports in a single file,
   we simulate lazy loading with a delay to demonstrate the concept */

function simulateLazy(Component, delayMs = 1500) {
  return lazy(() =>
    new Promise((resolve) => {
      setTimeout(() => {
        resolve({ default: Component });
      }, delayMs);
    })
  );
}

/* ─── "Lazy" components (simulated) ─── */

function DashboardContent() {
  return (
    <div style={{ padding: 16, background: "#e3f2fd", borderRadius: 8 }}>
      <h4>Dashboard</h4>
      <p>Revenue: $42,000 | Users: 1,234 | Orders: 567</p>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        {["Jan", "Feb", "Mar", "Apr"].map((m) => (
          <div key={m} style={{ flex: 1, background: "#1a73e8", color: "#fff", padding: 8, borderRadius: 4, textAlign: "center" }}>
            {m}: ${Math.floor(Math.random() * 10000)}
          </div>
        ))}
      </div>
    </div>
  );
}

function SettingsContent() {
  return (
    <div style={{ padding: 16, background: "#e8f5e9", borderRadius: 8 }}>
      <h4>Settings</h4>
      <label style={{ display: "block", margin: "8px 0" }}>
        <input type="checkbox" defaultChecked /> Dark Mode
      </label>
      <label style={{ display: "block", margin: "8px 0" }}>
        <input type="checkbox" /> Notifications
      </label>
      <label style={{ display: "block", margin: "8px 0" }}>
        <input type="checkbox" defaultChecked /> Auto-save
      </label>
    </div>
  );
}

function ProfileContent() {
  return (
    <div style={{ padding: 16, background: "#fce4ec", borderRadius: 8 }}>
      <h4>Profile</h4>
      <p>Name: Alice Johnson</p>
      <p>Email: alice@example.com</p>
      <p>Joined: January 2024</p>
    </div>
  );
}

// Create lazy versions (simulated with delay)
const LazyDashboard = simulateLazy(DashboardContent, 1500);
const LazySettings = simulateLazy(SettingsContent, 1000);
const LazyProfile = simulateLazy(ProfileContent, 800);

/* ─── Example 1: Basic Lazy Loading ─── */

function BasicLazyExample() {
  const [showDashboard, setShowDashboard] = useState(false);

  return (
    <div style={styles.section}>
      <h3>1. Basic Lazy Loading</h3>
      <button style={styles.btn} onClick={() => setShowDashboard(!showDashboard)}>
        {showDashboard ? "Hide" : "Load"} Dashboard
      </button>
      {showDashboard && (
        <Suspense fallback={<div style={styles.fallback}>Loading Dashboard... (simulated 1.5s delay)</div>}>
          <LazyDashboard />
        </Suspense>
      )}
      <div style={styles.code}>{`const LazyDashboard = lazy(() => import('./Dashboard'));

<Suspense fallback={<div>Loading...</div>}>
  <LazyDashboard />
</Suspense>`}</div>
    </div>
  );
}

/* ─── Example 2: Tab Navigation with Lazy ─── */

function TabNavigation() {
  const [tab, setTab] = useState(null);

  const tabs = [
    { id: "dashboard", label: "Dashboard", Component: LazyDashboard },
    { id: "settings", label: "Settings", Component: LazySettings },
    { id: "profile", label: "Profile", Component: LazyProfile },
  ];

  const activeTab = tabs.find((t) => t.id === tab);

  return (
    <div style={styles.section}>
      <h3>2. Tab Navigation (each tab loads independently)</h3>
      <div style={{ borderBottom: "2px solid #eee", marginBottom: 8 }}>
        {tabs.map((t) => (
          <span
            key={t.id}
            style={{ ...styles.tab, background: tab === t.id ? "#1a73e8" : "#f5f5f5", color: tab === t.id ? "#fff" : "#333" }}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </span>
        ))}
      </div>
      {activeTab && (
        <Suspense fallback={<div style={styles.fallback}>Loading {activeTab.label}...</div>}>
          <activeTab.Component />
        </Suspense>
      )}
      {!activeTab && <p style={{ color: "#999" }}>Select a tab to lazy-load its content.</p>}
    </div>
  );
}

/* ─── Example 3: Nested Suspense ─── */

function NestedSuspenseExample() {
  const [show, setShow] = useState(false);

  return (
    <div style={styles.section}>
      <h3>3. Nested Suspense Boundaries</h3>
      <button style={styles.btn} onClick={() => setShow(!show)}>
        {show ? "Hide" : "Show"} All
      </button>
      {show && (
        <Suspense fallback={<div style={{ ...styles.fallback, background: "#e8eaf6" }}>Outer: Loading everything...</div>}>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <div style={{ flex: 1 }}>
              <Suspense fallback={<div style={{ ...styles.fallback, fontSize: 12 }}>Loading Settings...</div>}>
                <LazySettings />
              </Suspense>
            </div>
            <div style={{ flex: 1 }}>
              <Suspense fallback={<div style={{ ...styles.fallback, fontSize: 12 }}>Loading Profile...</div>}>
                <LazyProfile />
              </Suspense>
            </div>
          </div>
        </Suspense>
      )}
      <div style={styles.code}>{`// Inner Suspense catches its own loading state
// Outer Suspense is fallback for anything not caught
<Suspense fallback="Loading all...">     ← outer
  <Suspense fallback="Loading A...">     ← inner for A
    <LazyA />
  </Suspense>
  <Suspense fallback="Loading B...">     ← inner for B
    <LazyB />
  </Suspense>
</Suspense>`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function LazyLoadingExample() {
  return (
    <div style={styles.container}>
      <h2>React.lazy + Suspense</h2>
      <BasicLazyExample />
      <TabNavigation />
      <NestedSuspenseExample />
    </div>
  );
}
