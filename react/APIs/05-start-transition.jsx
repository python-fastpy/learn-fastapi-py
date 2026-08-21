import { useState, startTransition, useTransition, memo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   startTransition — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: startTransition(() => { setState(...) })
   Hook:      const [isPending, startTransition] = useTransition()

   PURPOSE: Mark a state update as NON-URGENT so it doesn't block urgent
   updates (typing, clicking). React can interrupt transition renders.

   DIAGRAM:
   ┌──────────────────────────────────────────────────────────────┐
   │  Without startTransition:                                    │
   │    keystroke → setState("ab") → expensive render BLOCKS UI   │
   │                                                              │
   │  With startTransition:                                       │
   │    keystroke → urgent: setInput("ab")  → renders immediately │
   │             → transition: setFilter("ab") → renders in BG    │
   │                 (can be interrupted by next keystroke)        │
   └──────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. The function passed to startTransition must be SYNCHRONOUS.
      You can't do: startTransition(async () => { await fetch() })
   2. startTransition doesn't delay the setState — it marks it as
      interruptible. On fast devices, there may be no visible difference.
   3. Only wraps setState calls — not the computation itself.
   4. useTransition returns [isPending, startTransition]:
      - isPending is true while the transition render is in progress
      - Useful for showing loading indicators
   5. Can't use startTransition for controlled inputs (value={state})
      because the input would freeze. Split into two states instead:
      urgent (input display) + transition (filter/computation).
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  input: { padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box", fontSize: 16 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

/* ─── Slow list (intentionally expensive) ─── */

const SlowList = memo(function SlowList({ filter }) {
  const items = [];
  for (let i = 0; i < 2000; i++) {
    const text = `Item ${i}`;
    if (filter === "" || text.toLowerCase().includes(filter.toLowerCase())) {
      items.push(text);
    }
  }
  // Simulate slow rendering
  const start = performance.now();
  while (performance.now() - start < 50) {}

  return (
    <div style={{ maxHeight: 150, overflowY: "auto", marginTop: 8 }}>
      {items.slice(0, 30).map((item) => (
        <div key={item} style={{ padding: "2px 0", fontSize: 13 }}>{item}</div>
      ))}
      {items.length > 30 && <p style={{ color: "#999", fontSize: 12 }}>...{items.length - 30} more</p>}
    </div>
  );
});

/* ─── Example 1: Without startTransition (laggy) ─── */

function WithoutTransition() {
  const [input, setInput] = useState("");

  const handleChange = (e) => {
    // Both updates are urgent — the expensive list render blocks input
    setInput(e.target.value);
  };

  return (
    <div style={styles.section}>
      <h3>1. WITHOUT startTransition (laggy typing)</h3>
      <input
        value={input}
        onChange={handleChange}
        placeholder="Type to filter..."
        style={styles.input}
      />
      <SlowList filter={input} />
    </div>
  );
}

/* ─── Example 2: With useTransition (smooth) ─── */

function WithTransition() {
  const [input, setInput] = useState("");
  const [filter, setFilter] = useState("");
  const [isPending, startT] = useTransition();

  const handleChange = (e) => {
    const value = e.target.value;
    setInput(value); // URGENT: update input immediately

    startT(() => {
      setFilter(value); // TRANSITION: update filter in background
    });
  };

  return (
    <div style={styles.section}>
      <h3>2. WITH useTransition (smooth typing!)</h3>
      <input
        value={input}
        onChange={handleChange}
        placeholder="Type to filter (stays responsive)..."
        style={styles.input}
      />
      {isPending && (
        <div style={{ color: "#e65100", fontSize: 12, marginTop: 4 }}>
          Updating list...
        </div>
      )}
      <div style={{ opacity: isPending ? 0.6 : 1, transition: "opacity 0.2s" }}>
        <SlowList filter={filter} />
      </div>
      <div style={styles.code}>{`const [isPending, startTransition] = useTransition();

const handleChange = (e) => {
  setInput(e.target.value);         // URGENT
  startTransition(() => {
    setFilter(e.target.value);      // NON-URGENT (interruptible)
  });
};`}</div>
    </div>
  );
}

/* ─── Example 3: Tab Switching ─── */

function Tab1() { return <div style={{ padding: 16, background: "#e3f2fd", borderRadius: 8 }}><h4>Home</h4><p>Welcome!</p></div>; }
function Tab2() {
  // Simulate slow render
  const start = performance.now();
  while (performance.now() - start < 200) {}
  return <div style={{ padding: 16, background: "#e8f5e9", borderRadius: 8 }}><h4>Analytics</h4><p>Lots of charts here (slow to render).</p></div>;
}
function Tab3() { return <div style={{ padding: 16, background: "#fce4ec", borderRadius: 8 }}><h4>Settings</h4><p>Toggle things.</p></div>; }

function TabSwitching() {
  const [tab, setTab] = useState("home");
  const [isPending, startT] = useTransition();

  const switchTab = (newTab) => {
    startT(() => {
      setTab(newTab);
    });
  };

  const tabs = { home: <Tab1 />, analytics: <Tab2 />, settings: <Tab3 /> };

  return (
    <div style={styles.section}>
      <h3>3. Tab Switching with Transition</h3>
      <div style={{ display: "flex", gap: 4 }}>
        {Object.keys(tabs).map((t) => (
          <button
            key={t}
            style={{ ...styles.btn, background: tab === t ? "#1a73e8" : "#ccc", color: tab === t ? "#fff" : "#000" }}
            onClick={() => switchTab(t)}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
            {isPending && tab !== t && " ⟳"}
          </button>
        ))}
      </div>
      <div style={{ opacity: isPending ? 0.5 : 1, transition: "opacity 0.15s", marginTop: 8 }}>
        {tabs[tab]}
      </div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function StartTransitionExample() {
  return (
    <div style={styles.container}>
      <h2>startTransition</h2>
      <WithoutTransition />
      <WithTransition />
      <TabSwitching />
    </div>
  );
}
