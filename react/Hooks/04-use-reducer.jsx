import { useReducer } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useReducer HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: const [state, dispatch] = useReducer(reducer, initialArg, init?)

   DIAGRAM — How it works:
   ┌──────────┐    dispatch({ type, payload })    ┌───────────┐
   │ Component │ ──────────────────────────────▶  │  Reducer   │
   │           │                                  │ (pure fn)  │
   │  state ◀──│────────── returns new state ◀──  │            │
   └──────────┘                                   └───────────┘

   reducer(currentState, action) → newState
   - MUST be pure (no side effects)
   - MUST return new state (not mutate)

   GOTCHAS:
   1. 3rd ARGUMENT (lazy init): useReducer(reducer, arg, initFn)
      - initFn(arg) is called ONLY on first render
      - Useful for expensive initial state computation
      - Same concept as useState(initFn) lazy initialization

   2. Reducer MUST be pure — no API calls, no random, no Date.now().
      Put side effects in event handlers or useEffect.

   3. Action convention: { type: "ACTION_NAME", payload: data }
      But you can use any shape — React doesn't enforce this.

   4. dispatch is STABLE — it never changes between renders.
      Safe to omit from useEffect dependency arrays.

   5. State update uses Object.is — same reference = skip re-render.

   6. Use useReducer over useState when:
      - Next state depends on previous state in complex ways
      - Multiple sub-values are related
      - You want to centralize update logic
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, marginRight: 8 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  item: { display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: "1px solid #eee" },
};

/* ─── Example 1: Simple Counter ─── */

function counterReducer(state, action) {
  switch (action.type) {
    case "INCREMENT": return { count: state.count + 1 };
    case "DECREMENT": return { count: state.count - 1 };
    case "RESET":     return { count: 0 };
    case "SET":       return { count: action.payload };
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function CounterExample() {
  const [state, dispatch] = useReducer(counterReducer, { count: 0 });

  return (
    <div style={styles.section}>
      <h3>1. Simple Counter</h3>
      <p style={{ fontSize: 32, fontFamily: "monospace" }}>{state.count}</p>
      <button style={styles.btn} onClick={() => dispatch({ type: "INCREMENT" })}>+1</button>
      <button style={styles.btn} onClick={() => dispatch({ type: "DECREMENT" })}>-1</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => dispatch({ type: "RESET" })}>Reset</button>
      <button style={styles.btn} onClick={() => dispatch({ type: "SET", payload: 100 })}>Set 100</button>
    </div>
  );
}

/* ─── Example 2: Todo List (complex state) ─── */

let nextTodoId = 3;

function todoReducer(state, action) {
  switch (action.type) {
    case "ADD":
      return [...state, { id: nextTodoId++, text: action.text, done: false }];
    case "TOGGLE":
      return state.map((todo) =>
        todo.id === action.id ? { ...todo, done: !todo.done } : todo
      );
    case "DELETE":
      return state.filter((todo) => todo.id !== action.id);
    case "EDIT":
      return state.map((todo) =>
        todo.id === action.id ? { ...todo, text: action.text } : todo
      );
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function TodoApp() {
  const [todos, dispatch] = useReducer(todoReducer, [
    { id: 1, text: "Learn useReducer", done: false },
    { id: 2, text: "Build a project", done: true },
  ]);
  const [input, setInput] = useReducer((s, v) => v, ""); // simple state with reducer

  const handleAdd = () => {
    if (!input.trim()) return;
    dispatch({ type: "ADD", text: input });
    setInput("");
  };

  return (
    <div style={styles.section}>
      <h3>2. Todo List (complex state transitions)</h3>
      <div style={{ display: "flex", marginBottom: 8 }}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="New todo..."
          onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        />
        <button style={styles.btn} onClick={handleAdd}>Add</button>
      </div>
      {todos.map((todo) => (
        <div key={todo.id} style={styles.item}>
          <input
            type="checkbox"
            checked={todo.done}
            onChange={() => dispatch({ type: "TOGGLE", id: todo.id })}
          />
          <span style={{ flex: 1, textDecoration: todo.done ? "line-through" : "none" }}>
            {todo.text}
          </span>
          <button
            style={{ ...styles.btn, background: "#ea4335", fontSize: 11, padding: "4px 8px" }}
            onClick={() => dispatch({ type: "DELETE", id: todo.id })}
          >
            Delete
          </button>
        </div>
      ))}
      <div style={styles.code}>{`// All state logic centralized in reducer:
dispatch({ type: "ADD", text: "new" });
dispatch({ type: "TOGGLE", id: 1 });
dispatch({ type: "DELETE", id: 1 });`}</div>
    </div>
  );
}

/* ─── Example 3: Lazy Initialization (3rd argument) ─── */

function createInitialState(username) {
  console.log("createInitialState called (should be once)");
  return {
    username,
    preferences: { theme: "light", fontSize: 14, notifications: true },
    loginCount: 0,
  };
}

function lazyReducer(state, action) {
  switch (action.type) {
    case "TOGGLE_THEME":
      return { ...state, preferences: { ...state.preferences, theme: state.preferences.theme === "light" ? "dark" : "light" } };
    case "CHANGE_FONT":
      return { ...state, preferences: { ...state.preferences, fontSize: action.size } };
    case "LOGIN":
      return { ...state, loginCount: state.loginCount + 1 };
    default:
      return state;
  }
}

function LazyInitExample() {
  // 3rd arg: createInitialState receives "Alice" and runs ONLY on first render
  const [state, dispatch] = useReducer(lazyReducer, "Alice", createInitialState);

  return (
    <div style={styles.section}>
      <h3>3. Lazy Initialization (3rd argument)</h3>
      <p><strong>User:</strong> {state.username} | <strong>Theme:</strong> {state.preferences.theme} | <strong>Font:</strong> {state.preferences.fontSize}px | <strong>Logins:</strong> {state.loginCount}</p>
      <button style={styles.btn} onClick={() => dispatch({ type: "TOGGLE_THEME" })}>Toggle Theme</button>
      <button style={styles.btn} onClick={() => dispatch({ type: "CHANGE_FONT", size: state.preferences.fontSize + 2 })}>Font +2</button>
      <button style={styles.btn} onClick={() => dispatch({ type: "LOGIN" })}>Simulate Login</button>
      <div style={styles.code}>{`// 3rd arg = init function, receives 2nd arg as input
const [state, dispatch] = useReducer(
  reducer,        // 1st: reducer function
  "Alice",        // 2nd: arg passed TO init function
  createInitial   // 3rd: init function (lazy, runs once)
);
// createInitial("Alice") → { username: "Alice", ... }`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseReducerExample() {
  return (
    <div style={styles.container}>
      <h2>useReducer Hook</h2>
      <CounterExample />
      <TodoApp />
      <LazyInitExample />
    </div>
  );
}
