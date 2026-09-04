import { useState, useContext, createContext, useMemo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useContext + createContext — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   PURPOSE: Share data through the component tree without prop drilling.

   DIAGRAM:
   ┌────────────────────────────────────────────────────────────┐
   │  <ThemeContext.Provider value="dark">                     │
   │    │                                                      │
   │    ├── <Header />      → useContext(ThemeContext) = "dark" │
   │    │    └── <Logo />   → useContext(ThemeContext) = "dark" │
   │    │                                                      │
   │    ├── <ThemeContext.Provider value="light">    ← override │
   │    │    └── <Sidebar /> → useContext(ThemeContext) = "light"│
   │    │                                                      │
   │    └── <Footer />      → useContext(ThemeContext) = "dark" │
   └────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. DEFAULT VALUE: createContext(defaultValue) — used ONLY when there is
      NO Provider above the component in the tree.
   2. useContext ALWAYS finds the NEAREST Provider above it.
   3. EVERY component using useContext re-renders when the provider value
      changes — even if it only uses part of the context.
   4. OPTIMIZATION: Wrap context value in useMemo to prevent unnecessary
      re-renders when the parent re-renders without changing context data.
   5. You can nest multiple contexts (ThemeContext + UserContext).
   6. Context + useReducer is a lightweight Redux alternative.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

/* ═══════════════════ Example 1: Basic Theme Context ═══════════════════ */

const ThemeContext = createContext("light"); // default used when NO Provider

function ThemedButton() {
  const theme = useContext(ThemeContext);
  return (
    <button
      style={{
        ...styles.btn,
        background: theme === "dark" ? "#333" : "#fff",
        color: theme === "dark" ? "#fff" : "#333",
        border: "1px solid #999",
      }}
    >
      I'm {theme} themed
    </button>
  );
}

function ThemedPanel({ children }) {
  const theme = useContext(ThemeContext);
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 8,
        background: theme === "dark" ? "#1e1e1e" : "#f5f5f5",
        color: theme === "dark" ? "#e0e0e0" : "#333",
        margin: "8px 0",
      }}
    >
      <p>Panel theme: {theme}</p>
      {children}
    </div>
  );
}

function BasicThemeExample() {
  const [theme, setTheme] = useState("light");

  return (
    <div style={styles.section}>
      <h3>1. Basic Theme Context</h3>
      <button
        style={{ ...styles.btn, background: "#1a73e8", color: "#fff" }}
        onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      >
        Toggle: {theme}
      </button>

      <ThemeContext.Provider value={theme}>
        <ThemedPanel>
          <ThemedButton />

          {/* Nested Provider OVERRIDES for its subtree */}
          <ThemeContext.Provider value={theme === "light" ? "dark" : "light"}>
            <ThemedPanel>
              <p>Nested provider: opposite theme!</p>
              <ThemedButton />
            </ThemedPanel>
          </ThemeContext.Provider>
        </ThemedPanel>
      </ThemeContext.Provider>
    </div>
  );
}

/* ═══════════════════ Example 2: Multiple Contexts ═══════════════════ */

const UserContext = createContext(null);
const LangContext = createContext("en");

function Greeting() {
  const user = useContext(UserContext);
  const lang = useContext(LangContext);

  const greetings = { en: "Hello", es: "Hola", fr: "Bonjour", de: "Hallo" };

  return (
    <p>
      {greetings[lang] || "Hello"}, <strong>{user ? user.name : "Guest"}</strong>!
      (Language: {lang})
    </p>
  );
}

function MultiContextExample() {
  const [user, setUser] = useState({ name: "Alice" });
  const [lang, setLang] = useState("en");

  return (
    <div style={styles.section}>
      <h3>2. Multiple Contexts</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <select value={lang} onChange={(e) => setLang(e.target.value)} style={{ padding: 6, borderRadius: 4 }}>
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
        </select>
        <input
          value={user.name}
          onChange={(e) => setUser({ name: e.target.value })}
          style={{ padding: 6, borderRadius: 4, border: "1px solid #ccc" }}
        />
      </div>

      <UserContext.Provider value={user}>
        <LangContext.Provider value={lang}>
          <Greeting />
        </LangContext.Provider>
      </UserContext.Provider>
    </div>
  );
}

/* ═══════════════════ Example 3: Context + State (Mini Store) ═══════════════════ */

const CounterContext = createContext(null);

function CounterProvider({ children }) {
  const [count, setCount] = useState(0);

  // useMemo prevents re-creating the value object on every render
  // Without this, every child using this context re-renders on ANY
  // parent re-render, even if count didn't change
  const value = useMemo(() => ({
    count,
    increment: () => setCount((c) => c + 1),
    decrement: () => setCount((c) => c - 1),
    reset: () => setCount(0),
  }), [count]); // Only recreate when count changes

  return (
    <CounterContext.Provider value={value}>
      {children}
    </CounterContext.Provider>
  );
}

function CounterDisplay() {
  const { count } = useContext(CounterContext);
  return <p style={{ fontSize: 32, fontFamily: "monospace", margin: "8px 0" }}>{count}</p>;
}

function CounterControls() {
  const { increment, decrement, reset } = useContext(CounterContext);
  return (
    <div>
      <button style={{ ...styles.btn, background: "#34a853", color: "#fff" }} onClick={increment}>+1</button>
      <button style={{ ...styles.btn, background: "#ea4335", color: "#fff" }} onClick={decrement}>-1</button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={reset}>Reset</button>
    </div>
  );
}

function ContextStoreExample() {
  return (
    <div style={styles.section}>
      <h3>3. Context as Mini Store (useMemo optimization)</h3>
      <CounterProvider>
        <CounterDisplay />
        <CounterControls />
      </CounterProvider>
      <div style={styles.code}>{`// Wrap value in useMemo to avoid unnecessary re-renders:
const value = useMemo(() => ({
  count,
  increment: () => setCount(c => c + 1),
}), [count]); // only new object when count changes`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseContextExample() {
  return (
    <div style={styles.container}>
      <h2>useContext + createContext</h2>
      <BasicThemeExample />
      <MultiContextExample />
      <ContextStoreExample />
    </div>
  );
}
