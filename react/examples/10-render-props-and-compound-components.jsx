import { createContext, useContext, useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   RENDER PROPS & COMPOUND COMPONENTS — REUSE PATTERN COMPARISON
   ═══════════════════════════════════════════════════════════════════════════════

   Four different ways to share logic/behavior between components. All four
   solve overlapping problems — knowing WHEN to reach for each is the
   actual interview question, more than any single implementation.

   ┌─────────────────────┬──────────────────────────────────────────────────┐
   │ Pattern              │ How it shares logic                                 │
   ├─────────────────────┼──────────────────────────────────────────────────┤
   │ HOC                  │ A function wraps a component, injecting extra      │
   │ (see examples/09)    │ props. `withAuth(Profile)` returns a new component. │
   │ Render Props          │ A component accepts a function as a prop (often    │
   │                       │ `render` or `children`) and calls it with internal  │
   │                       │ state, letting the CALLER decide what to render.    │
   │ Compound Components   │ Several components share implicit state via        │
   │                       │ Context, composed together like HTML               │
   │                       │ (`<Tabs><Tabs.List>...`) — flexible markup, no      │
   │                       │ prop drilling between the pieces.                   │
   │ Custom Hooks          │ Extract STATE + LOGIC only (no JSX) into a          │
   │ (see Hooks/11)        │ reusable function — today's default choice for     │
   │                       │ sharing behavior.                                    │
   └─────────────────────┴──────────────────────────────────────────────────┘

   MODERN RECOMMENDATION (what to say in an interview):
   - Sharing pure LOGIC (no markup)?            → Custom Hook
   - Need to let the caller control the MARKUP  → Render Props (or just
     while you supply behavior/state?             pass children a function)
   - Building a flexible, composable UI widget  → Compound Components
     with multiple related pieces (Tabs, Menu)?   (Context internally)
   - Must wrap existing JSX/class components,   → HOC (least common now;
     or intercept `render()` itself?               mostly legacy codebases)

   GOTCHAS:
   1. Render props historically caused "wrapper hell" when nesting several
      — e.g. <DataFetcher><MousePos>{...}</MousePos></DataFetcher>. Hooks
      avoid the nesting because they don't need to render anything.
   2. Compound components MUST be used together — `<Tabs.Panel>` rendered
      outside a parent `<Tabs>` has no Context to read from. Guard with a
      clear error message ("Tabs.Panel must be used inside <Tabs>").
   3. `children` as a function (`{(data) => <div>{data}</div>}`) IS a
      render prop — it doesn't have to be named `render`.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  trackArea: { height: 100, border: "1px dashed #999", position: "relative", background: "#fafafa" },
  tabList: { display: "flex", gap: 4, borderBottom: "1px solid #ddd" },
  tab: { padding: "8px 14px", cursor: "pointer", border: "none", background: "none", borderBottom: "2px solid transparent" },
  tabActive: { borderBottom: "2px solid #1a73e8", color: "#1a73e8", fontWeight: "bold" },
  panel: { padding: 12 },
};

/* ─── Example 1: Render Props — MouseTracker ─── */

function MouseTracker({ render }) {
  const [pos, setPos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPos({ x: Math.round(e.clientX - rect.left), y: Math.round(e.clientY - rect.top) });
  };

  // MouseTracker owns the STATE and BEHAVIOR (tracking mouse position),
  // but has NO opinion on what to render with it — that's the caller's job.
  return <div style={styles.trackArea} onMouseMove={handleMouseMove}>{render(pos)}</div>;
}

function RenderPropsDemo() {
  return (
    <div style={styles.section}>
      <h3>1. Render Props — MouseTracker</h3>
      <p>Move the mouse inside the box — the caller decides how to display the position:</p>
      <MouseTracker render={(pos) => <p>Mouse at ({pos.x}, {pos.y})</p>} />
      <div style={styles.code}>{`<MouseTracker render={(pos) => <p>Mouse at ({pos.x}, {pos.y})</p>} />
// or identically, using children as the function:
<MouseTracker>{(pos) => <p>Mouse at ({pos.x}, {pos.y})</p>}</MouseTracker>`}</div>
    </div>
  );
}

/* ─── Example 2: Compound Components — Tabs ─── */

const TabsContext = createContext(null);

function useTabsContext(componentName) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error(`${componentName} must be used inside <Tabs>`);
  return ctx;
}

function Tabs({ defaultValue, children }) {
  const [active, setActive] = useState(defaultValue);
  // Shared state lives here, in Context — no prop drilling to List/Tab/Panel.
  return <TabsContext.Provider value={{ active, setActive }}>{children}</TabsContext.Provider>;
}

function TabList({ children }) {
  return <div style={styles.tabList}>{children}</div>;
}

function Tab({ value, children }) {
  const { active, setActive } = useTabsContext("Tabs.Tab");
  return (
    <button
      style={{ ...styles.tab, ...(active === value ? styles.tabActive : {}) }}
      onClick={() => setActive(value)}
    >
      {children}
    </button>
  );
}

function TabPanel({ value, children }) {
  const { active } = useTabsContext("Tabs.Panel");
  if (active !== value) return null;
  return <div style={styles.panel}>{children}</div>;
}

// Attach sub-components — this is what enables the `<Tabs.Tab>` syntax.
Tabs.List = TabList;
Tabs.Tab = Tab;
Tabs.Panel = TabPanel;

function CompoundComponentsDemo() {
  return (
    <div style={styles.section}>
      <h3>2. Compound Components — Tabs</h3>
      <p>Pieces communicate through shared Context, composed like plain HTML:</p>
      <Tabs defaultValue="profile">
        <Tabs.List>
          <Tabs.Tab value="profile">Profile</Tabs.Tab>
          <Tabs.Tab value="settings">Settings</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="profile">Profile panel content.</Tabs.Panel>
        <Tabs.Panel value="settings">Settings panel content.</Tabs.Panel>
      </Tabs>
      <div style={styles.code}>{`<Tabs defaultValue="profile">
  <Tabs.List>
    <Tabs.Tab value="profile">Profile</Tabs.Tab>
    <Tabs.Tab value="settings">Settings</Tabs.Tab>
  </Tabs.List>
  <Tabs.Panel value="profile">...</Tabs.Panel>
  <Tabs.Panel value="settings">...</Tabs.Panel>
</Tabs>
// Tabs owns state via Context; Tab/Panel read it — no prop drilling.
// Compare with examples/13-tabs.jsx, which takes the simpler single-
// component approach (fine when you don't need this composition flexibility).`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function RenderPropsAndCompoundComponents() {
  return (
    <div style={styles.container}>
      <h2>Render Props & Compound Components</h2>
      <RenderPropsDemo />
      <CompoundComponentsDemo />
    </div>
  );
}
