import { useState, memo, useContext, createContext } from "react";

/* ═══════════════════════════════════════════════════════════════════
   React.memo — Skip re-rendering when props haven't changed (shallow comparison).
   ┌──────────────────────────────────────────────────────────────┐
   │  Parent re-renders                                          │
   │    ├── <NormalChild />     → ALWAYS re-renders              │
   │    └── <memo(MemoChild) /> → re-renders ONLY if props change│
   └──────────────────────────────────────────────────────────────┘
   1. Only checks props — useState/useContext/useReducer still cause re-renders.
   2. Shallow compare: new object/array/function refs defeat memo unless memoized.
   3. Context changes ALWAYS re-render memo'd components consuming that context.
   4. Custom compare returns TRUE to SKIP (opposite of shouldComponentUpdate).
   5. Has overhead — only use for expensive components that re-render with same props.
   ═══════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  child: { padding: 12, border: "1px dashed #ccc", borderRadius: 4, marginTop: 8 },
};

let normalRenders = 0;
let memoRenders = 0;

function NormalChild({ name }) {
  normalRenders++;
  return <div style={styles.child}>Normal: {name} (rendered {normalRenders}x)</div>;
}

const MemoChild = memo(function MemoChild({ name }) {
  memoRenders++;
  return <div style={{ ...styles.child, borderColor: "#34a853" }}>Memo: {name} (rendered {memoRenders}x)</div>;
});

function BasicMemoExample() {
  const [count, setCount] = useState(0);
  const [name] = useState("Alice");

  return (
    <div style={styles.section}>
      <h3>1. Basic memo (props unchanged = skip)</h3>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>Re-render parent ({count})</button>
      <NormalChild name={name} />
      <MemoChild name={name} />
    </div>
  );
}

/* ─── Example 2: Context defeats memo ─── */

const ThemeCtx = createContext("light");

const MemoThemedBox = memo(function MemoThemedBox({ label }) {
  const theme = useContext(ThemeCtx);
  console.log(`MemoThemedBox "${label}" rendered (theme=${theme})`);
  return (
    <div style={{ ...styles.child, background: theme === "dark" ? "#333" : "#fff", color: theme === "dark" ? "#fff" : "#333" }}>
      {label} — theme: {theme}
    </div>
  );
});

function ContextDefeatsMemo() {
  const [theme, setTheme] = useState("light");
  const [count, setCount] = useState(0);

  return (
    <div style={styles.section}>
      <h3>2. Context Changes Defeat memo</h3>
      <button style={styles.btn} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>Toggle Theme</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setCount(count + 1)}>Other re-render ({count})</button>
      <ThemeCtx.Provider value={theme}>
        <MemoThemedBox label="Box A" />
      </ThemeCtx.Provider>
    </div>
  );
}

/* ─── Example 3: Custom Comparison ─── */

const HeavyList = memo(
  function HeavyList({ items, title }) {
    console.log("HeavyList rendered");
    return (
      <div style={styles.child}>
        <strong>{title}</strong>
        <ul>{items.map((item, i) => <li key={i}>{item}</li>)}</ul>
      </div>
    );
  },
  (prevProps, nextProps) => {
    return (
      prevProps.title === nextProps.title &&
      prevProps.items.length === nextProps.items.length
    );
  }
);

function CustomComparisonExample() {
  const [items, setItems] = useState(["Apple", "Banana"]);
  const [, forceRender] = useState(0);

  return (
    <div style={styles.section}>
      <h3>3. Custom Comparison Function</h3>
      <button style={styles.btn} onClick={() => setItems([...items])}>
        New array ref, same content (skipped)
      </button>
      <button style={styles.btn} onClick={() => setItems([...items, "New"])}>
        Add item (re-renders)
      </button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => forceRender((n) => n + 1)}>
        Parent re-render (skipped)
      </button>
      <HeavyList items={items} title="Fruits" />
    </div>
  );
}

/* ─── MAIN ─── */

export default function MemoExample() {
  return (
    <div style={styles.container}>
      <h2>React.memo</h2>
      <BasicMemoExample />
      <ContextDefeatsMemo />
      <CustomComparisonExample />
    </div>
  );
}
