import { useState, useEffect, useCallback, useRef } from "react";

/*
  DEBOUNCE
  ────────
  What: Delays execution until user STOPS typing for N milliseconds.
  Use case: Search input — don't fire API call on every keystroke.

  Timeline:
    User types:  h  e  l  l  o
    Time:        0  100ms  200ms  300ms  400ms
                 |  |      |      |      |
                 ✗  ✗      ✗      ✗      ✓ ← fires after 500ms pause
                 (each keystroke resets the timer)

  Debounce vs Throttle:
    Debounce: "Wait until user STOPS, then fire once"
    Throttle: "Fire at most once every N ms, even while user keeps going"

  Implementation:
    1. Custom hook approach (useDebounce) — debounces a VALUE
    2. Callback approach (useDebouncedCallback) — debounces a FUNCTION
*/

// ─── Approach 1: Debounce a value ────────────────────────────────────────────

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Set a timer to update debounced value after delay
    const timer = setTimeout(() => setDebouncedValue(value), delay);

    // If value changes again before delay, cancel previous timer
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// ─── Approach 2: Debounce a callback ─────────────────────────────────────────

function useDebouncedCallback(callback, delay) {
  const timerRef = useRef(null);

  // useCallback so the returned function is stable across renders
  const debouncedFn = useCallback(
    (...args) => {
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => callback(...args), delay);
    },
    [callback, delay]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => clearTimeout(timerRef.current);
  }, []);

  return debouncedFn;
}

// ─── Demo Component ──────────────────────────────────────────────────────────

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 400 },
  input: { width: "100%", padding: "8px 12px", fontSize: 14, border: "1px solid #ccc", borderRadius: 4, marginBottom: 8, boxSizing: "border-box" },
  log: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontSize: 13, maxHeight: 200, overflowY: "auto" },
  entry: { padding: "4px 0", borderBottom: "1px solid #eee" },
};

export default function DebounceExample() {
  const [text, setText] = useState("");
  const [logs, setLogs] = useState([]);

  // Approach 1: debounced value
  const debouncedText = useDebounce(text, 500);

  // When debouncedText changes, simulate an API call
  useEffect(() => {
    if (debouncedText) {
      const time = new Date().toLocaleTimeString();
      setLogs((prev) => [`[${time}] API called with: "${debouncedText}"`, ...prev]);
    }
  }, [debouncedText]);

  // Approach 2: debounced callback (alternative)
  // const debouncedSearch = useDebouncedCallback((query) => {
  //   console.log('Search:', query);
  // }, 500);

  return (
    <div style={styles.container}>
      <h3>Debounce Demo</h3>
      <p>Type fast — API call fires 500ms after you stop typing.</p>

      <input
        style={styles.input}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Search..."
      />

      <div>Current: "{text}"</div>
      <div>Debounced: "{debouncedText}"</div>

      <h4>API Call Log</h4>
      <div style={styles.log}>
        {logs.length === 0 && <div style={{ color: "#999" }}>No calls yet...</div>}
        {logs.map((log, i) => (
          <div key={i} style={styles.entry}>{log}</div>
        ))}
      </div>
    </div>
  );
}
