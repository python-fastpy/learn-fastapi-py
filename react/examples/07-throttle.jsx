import { useState, useCallback, useRef, useEffect } from "react";

/*
  THROTTLE
  ────────
  What: Limits execution to at most once every N milliseconds.
  Use case: Scroll/resize handlers, button spam prevention.

  Timeline comparison:
    Events:    ● ● ● ● ● ● ● ● ●        (rapid clicks/scrolls)
    Debounce:                        ●    (fires once at end, after silence)
    Throttle:  ●     ●     ●     ●        (fires every N ms, steady pace)

  How throttle works:
    1. First call → execute immediately
    2. Subsequent calls within cooldown → ignored
    3. After cooldown expires → next call executes

    Time:  0ms    200ms    400ms    600ms    800ms
    Call:  ✓ fire  ✗ skip   ✗ skip   ✓ fire   ✗ skip
           |←── 500ms cooldown ──→|
*/

function useThrottle(callback, delay) {
  const lastRun = useRef(0);
  const timerRef = useRef(null);

  const throttledFn = useCallback(
    (...args) => {
      const now = Date.now();
      const timeSinceLastRun = now - lastRun.current;

      if (timeSinceLastRun >= delay) {
        // Enough time passed — execute now
        lastRun.current = now;
        callback(...args);
      } else {
        // Schedule trailing call so last invocation isn't lost
        clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
          lastRun.current = Date.now();
          callback(...args);
        }, delay - timeSinceLastRun);
      }
    },
    [callback, delay]
  );

  useEffect(() => {
    return () => clearTimeout(timerRef.current);
  }, []);

  return throttledFn;
}

// ─── Demo ────────────────────────────────────────────────────────────────────

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  btn: { padding: "10px 20px", fontSize: 14, cursor: "pointer", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 4, marginRight: 8 },
  scrollBox: { height: 200, overflowY: "scroll", border: "1px solid #ddd", borderRadius: 4, marginTop: 12 },
  scrollContent: { height: 1000, background: "linear-gradient(to bottom, #e8f0fe, #fff)" },
  log: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontSize: 13, maxHeight: 200, overflowY: "auto", marginTop: 12 },
  entry: { padding: "4px 0", borderBottom: "1px solid #eee" },
  counts: { display: "flex", gap: 20, marginTop: 12 },
  stat: { background: "#f0f0f0", padding: "8px 16px", borderRadius: 6 },
};

export default function ThrottleExample() {
  const [logs, setLogs] = useState([]);
  const [rawCount, setRawCount] = useState(0);
  const [throttledCount, setThrottledCount] = useState(0);

  const handleClick = useThrottle(() => {
    const time = new Date().toLocaleTimeString();
    setThrottledCount((c) => c + 1);
    setLogs((prev) => [`[${time}] Throttled handler fired`, ...prev]);
  }, 1000); // max once per second

  const onClick = () => {
    setRawCount((c) => c + 1);
    handleClick();
  };

  // Scroll throttle demo
  const handleScroll = useThrottle(() => {
    const time = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${time}] Scroll handler fired`, ...prev]);
  }, 500);

  return (
    <div style={styles.container}>
      <h3>Throttle Demo</h3>

      <p>Click rapidly — handler fires at most once per second.</p>
      <button style={styles.btn} onClick={onClick}>Click me fast!</button>

      <div style={styles.counts}>
        <div style={styles.stat}>Raw clicks: {rawCount}</div>
        <div style={styles.stat}>Throttled fires: {throttledCount}</div>
      </div>

      <p style={{ marginTop: 16 }}>Scroll below — handler fires at most every 500ms.</p>
      <div style={styles.scrollBox} onScroll={handleScroll}>
        <div style={styles.scrollContent} />
      </div>

      <h4>Event Log</h4>
      <div style={styles.log}>
        {logs.length === 0 && <div style={{ color: "#999" }}>No events yet...</div>}
        {logs.map((log, i) => (
          <div key={i} style={styles.entry}>{log}</div>
        ))}
      </div>
    </div>
  );
}
