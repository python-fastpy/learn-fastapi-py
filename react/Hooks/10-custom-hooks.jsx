import { useState, useEffect, useRef } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   CUSTOM HOOKS — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   A custom hook is a JavaScript function whose name starts with "use"
   and that may call other hooks.

   WHY:
   - Extract reusable stateful logic from components
   - Share behavior without sharing state (each call gets its own state)
   - Keep components focused on rendering

   RULES:
   1. Name MUST start with "use" (useCounter, useFetch, useLocalStorage)
   2. Can call other hooks (useState, useEffect, etc.)
   3. Follow the Rules of Hooks (top level only, not in conditions)
   4. Each component that uses the hook gets its OWN copy of state

   GOTCHAS:
   1. Custom hooks share LOGIC, not STATE. Two components calling
      useCounter() get completely independent counter states.
   2. A hook's state changes cause the CALLING component to re-render.
   3. You can pass values between hooks:
      const id = useSelectedId();
      const data = useFetch(`/api/${id}`);
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4 },
};

/* ═══════════════ Hook 1: useCounter ═══════════════ */

function useCounter(initialValue = 0, step = 1) {
  const [count, setCount] = useState(initialValue);
  return {
    count,
    increment: () => setCount((c) => c + step),
    decrement: () => setCount((c) => c - step),
    reset: () => setCount(initialValue),
    set: setCount,
  };
}

function CounterDemo() {
  const counter1 = useCounter(0, 1);
  const counter2 = useCounter(100, 5);

  return (
    <div style={styles.section}>
      <h3>1. useCounter (independent state per call)</h3>
      <div style={{ display: "flex", gap: 16 }}>
        <div>
          <p>Counter 1 (step=1): <strong>{counter1.count}</strong></p>
          <button style={styles.btn} onClick={counter1.increment}>+1</button>
          <button style={styles.btn} onClick={counter1.decrement}>-1</button>
        </div>
        <div>
          <p>Counter 2 (step=5): <strong>{counter2.count}</strong></p>
          <button style={styles.btn} onClick={counter2.increment}>+5</button>
          <button style={styles.btn} onClick={counter2.decrement}>-5</button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════ Hook 2: useDocumentTitle ═══════════════ */

function useDocumentTitle(title) {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = title;
    return () => { document.title = prevTitle; };
  }, [title]);
}

function TitleDemo() {
  const [name, setName] = useState("React");
  useDocumentTitle(`Hello, ${name}!`);

  return (
    <div style={styles.section}>
      <h3>2. useDocumentTitle</h3>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Change page title..."
        style={{ ...styles.input, width: "100%", boxSizing: "border-box" }}
      />
      <p style={{ fontSize: 12, color: "#999" }}>Check your browser tab title.</p>
    </div>
  );
}

/* ═══════════════ Hook 3: useLocalStorage ═══════════════ */

function useLocalStorage(key, initialValue) {
  const [value, setValue] = useState(() => {
    try {
      const saved = localStorage.getItem(key);
      return saved !== null ? JSON.parse(saved) : initialValue;
    } catch {
      return initialValue;
    }
  });

  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);

  return [value, setValue];
}

function LocalStorageDemo() {
  const [theme, setTheme] = useLocalStorage("demo-theme", "light");
  const [count, setCount] = useLocalStorage("demo-count", 0);

  return (
    <div style={styles.section}>
      <h3>3. useLocalStorage (persists across reloads)</h3>
      <p>Theme: <strong>{theme}</strong> | Count: <strong>{count}</strong></p>
      <button style={styles.btn} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>Toggle Theme</button>
      <button style={styles.btn} onClick={() => setCount((c) => c + 1)}>+1</button>
      <p style={{ fontSize: 12, color: "#999" }}>Refresh the page — values persist!</p>
    </div>
  );
}

/* ═══════════════ Hook 4: useToggle ═══════════════ */

function useToggle(initialValue = false) {
  const [value, setValue] = useState(initialValue);
  const toggle = () => setValue((v) => !v);
  const setTrue = () => setValue(true);
  const setFalse = () => setValue(false);
  return { value, toggle, setTrue, setFalse };
}

function ToggleDemo() {
  const modal = useToggle(false);
  const dark = useToggle(false);

  return (
    <div style={styles.section}>
      <h3>4. useToggle</h3>
      <button style={styles.btn} onClick={modal.toggle}>
        Modal: {modal.value ? "Open" : "Closed"}
      </button>
      <button style={{ ...styles.btn, background: dark.value ? "#333" : "#ccc", color: dark.value ? "#fff" : "#000" }} onClick={dark.toggle}>
        Dark: {dark.value ? "On" : "Off"}
      </button>
      {modal.value && (
        <div style={{ marginTop: 8, padding: 16, background: "#e3f2fd", borderRadius: 8 }}>
          Modal content! <button style={styles.btn} onClick={modal.setFalse}>Close</button>
        </div>
      )}
    </div>
  );
}

/* ═══════════════ Hook 5: useClickOutside ═══════════════ */

function useClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      handler(event);
    };
    document.addEventListener("mousedown", listener);
    return () => document.removeEventListener("mousedown", listener);
  }, [ref, handler]);
}

function ClickOutsideDemo() {
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef(null);

  useClickOutside(dropdownRef, () => setOpen(false));

  return (
    <div style={styles.section}>
      <h3>5. useClickOutside</h3>
      <div style={{ position: "relative", display: "inline-block" }}>
        <button style={styles.btn} onClick={() => setOpen(!open)}>
          {open ? "Close" : "Open"} Dropdown
        </button>
        {open && (
          <div ref={dropdownRef} style={{ position: "absolute", top: "100%", left: 0, background: "#fff", border: "1px solid #ccc", borderRadius: 4, boxShadow: "0 4px 12px rgba(0,0,0,0.1)", zIndex: 10, padding: 8, minWidth: 150 }}>
            <div style={{ padding: "4px 8px", cursor: "pointer" }}>Option 1</div>
            <div style={{ padding: "4px 8px", cursor: "pointer" }}>Option 2</div>
            <div style={{ padding: "4px 8px", cursor: "pointer" }}>Option 3</div>
          </div>
        )}
      </div>
      <span style={{ fontSize: 12, color: "#999", marginLeft: 8 }}>Click outside dropdown to close</span>
    </div>
  );
}

/* ─── MAIN ─── */

export default function CustomHooksExample() {
  return (
    <div style={styles.container}>
      <h2>Custom Hooks</h2>
      <CounterDemo />
      <TitleDemo />
      <LocalStorageDemo />
      <ToggleDemo />
      <ClickOutsideDemo />
    </div>
  );
}
