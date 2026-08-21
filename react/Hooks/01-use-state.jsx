import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useState — const [state, setState] = useState(initialValue)

   GOTCHAS:
   1. useState(fn) calls fn only on first render; useState(fn()) calls every render
   2. <Component key={id}/> — key change destroys+recreates with fresh state
   3. setState(myFn) treats it as updater; use setState(() => myFn) to store fns
   4. Object.is comparison: same value = skip re-render (NaN===NaN, 0!==-0)
   5. StrictMode double-invokes initializer+updater in dev only
   6. setState during render processes immediately — usually a code smell
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  good: { background: "#e8f5e9", padding: 8, borderRadius: 6, fontSize: 12, fontFamily: "monospace", whiteSpace: "pre" },
  bad: { background: "#fce4ec", padding: 8, borderRadius: 6, fontSize: 12, fontFamily: "monospace", whiteSpace: "pre" },
};

/* ─── Example 1: Initializer Function ─── */

function createInitialTodos() {
  console.log("createInitialTodos called (should only appear ONCE)");
  const todos = [];
  for (let i = 0; i < 5; i++) {
    todos.push({ id: i, text: `Todo #${i + 1}`, done: false });
  }
  return todos;
}

function InitializerExample() {
  // Passed as FUNCTION REFERENCE — only called on first render
  const [todos, setTodos] = useState(createInitialTodos);
  const [count, setCount] = useState(0);

  return (
    <div style={styles.section}>
      <h3>1. Initializer Function (lazy init)</h3>
      <p>Check console — "createInitialTodos called" appears only ONCE, even across re-renders.</p>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>
        Re-render ({count})
      </button>
      <ul>{todos.map((t) => <li key={t.id}>{t.text}</li>)}</ul>
      <div style={styles.good}>{`// ✓ useState(createInitialTodos)   → called once
// ✗ useState(createInitialTodos()) → called every render!`}</div>
    </div>
  );
}

/* ─── Example 2: Reset with key ─── */

function EditForm({ contactId }) {
  const [name, setName] = useState("Initial for " + contactId);

  return (
    <div>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4 }}
      />
      <span style={{ color: "#999", fontSize: 12, marginLeft: 8 }}>
        (State: "{name}")
      </span>
    </div>
  );
}

function ResetWithKey() {
  const [selectedId, setSelectedId] = useState(1);
  const contacts = [
    { id: 1, name: "Alice" },
    { id: 2, name: "Bob" },
    { id: 3, name: "Charlie" },
  ];

  return (
    <div style={styles.section}>
      <h3>2. Reset State with key Prop</h3>
      <p>Click different contacts — form state resets because key changes.</p>
      {contacts.map((c) => (
        <button
          key={c.id}
          style={{ ...styles.btn, background: selectedId === c.id ? "#1a73e8" : "#ccc", color: selectedId === c.id ? "#fff" : "#000" }}
          onClick={() => setSelectedId(c.id)}
        >
          {c.name}
        </button>
      ))}
      {/* key={selectedId} → React destroys old EditForm, creates new one */}
      <EditForm key={selectedId} contactId={selectedId} />
      <div style={styles.code}>{`// When key changes: destroy old → create new (fresh state)
<EditForm key={selectedId} />`}</div>
    </div>
  );
}

/* ─── Example 3: Storing Functions in State ─── */

function StoringFunctions() {
  // To store a function in state, wrap it:
  const [fn, setFn] = useState(() => () => "Hello!");

  const storeGreet = () => {
    // setState(() => myFn) — the outer arrow prevents React from
    // treating the inner function as an updater
    setFn(() => () => "Greetings!");
  };

  const storeGoodbye = () => {
    setFn(() => () => "Goodbye!");
  };

  return (
    <div style={styles.section}>
      <h3>3. Storing Functions in State</h3>
      <p>Current function returns: <strong>"{fn()}"</strong></p>
      <button style={styles.btn} onClick={storeGreet}>Store "Greetings!"</button>
      <button style={styles.btn} onClick={storeGoodbye}>Store "Goodbye!"</button>
      <div style={styles.bad}>{`// ✗ WRONG — React calls it as updater:
setFn(myFunction)

// React interprets this as: setFn(prevState => myFunction(prevState))`}</div>
      <div style={styles.good}>{`// ✓ RIGHT — wrap in arrow:
setFn(() => myFunction)

// React sees: setFn(() => myFunction), stores myFunction`}</div>
    </div>
  );
}

/* ─── Example 4: Different Value Types ─── */

function ValueTypes() {
  const [text, setText] = useState("hello");       // string
  const [count, setCount] = useState(0);            // number
  const [isOn, setIsOn] = useState(false);          // boolean
  const [items, setItems] = useState(["a", "b"]);   // array
  const [user, setUser] = useState({ name: "Jo" }); // object
  const [empty, setEmpty] = useState(null);          // null

  return (
    <div style={styles.section}>
      <h3>4. All Value Types</h3>
      <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
        <thead>
          <tr><th style={{ textAlign: "left", padding: 4 }}>Type</th><th style={{ textAlign: "left", padding: 4 }}>Value</th><th style={{ padding: 4 }}>Action</th></tr>
        </thead>
        <tbody>
          <tr><td style={{ padding: 4 }}>String</td><td style={{ padding: 4 }}>{text}</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setText(text + "!")}>Add !</button></td></tr>
          <tr><td style={{ padding: 4 }}>Number</td><td style={{ padding: 4 }}>{count}</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setCount(n => n + 1)}>+1</button></td></tr>
          <tr><td style={{ padding: 4 }}>Boolean</td><td style={{ padding: 4 }}>{isOn ? "true" : "false"}</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setIsOn(!isOn)}>Toggle</button></td></tr>
          <tr><td style={{ padding: 4 }}>Array</td><td style={{ padding: 4 }}>[{items.join(", ")}]</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setItems([...items, String.fromCharCode(97 + items.length)])}>Add</button></td></tr>
          <tr><td style={{ padding: 4 }}>Object</td><td style={{ padding: 4 }}>{JSON.stringify(user)}</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setUser({ ...user, age: (user.age || 0) + 1 })}>Age+</button></td></tr>
          <tr><td style={{ padding: 4 }}>Null</td><td style={{ padding: 4 }}>{String(empty)}</td><td style={{ padding: 4 }}><button style={{ ...styles.btn, fontSize: 11, padding: "4px 8px" }} onClick={() => setEmpty(empty ? null : "set!")}>Toggle</button></td></tr>
        </tbody>
      </table>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseStateExample() {
  return (
    <div style={styles.container}>
      <h2>useState Hook</h2>
      <InitializerExample />
      <ResetWithKey />
      <StoringFunctions />
      <ValueTypes />
    </div>
  );
}
