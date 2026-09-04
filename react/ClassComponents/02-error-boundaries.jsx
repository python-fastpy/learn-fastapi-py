import { Component, useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   ERROR BOUNDARIES — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   An Error Boundary is a component that catches JavaScript errors thrown
   during rendering anywhere in its child tree, logs them, and displays a
   fallback UI instead of unmounting the whole app.

   Requires TWO class-only lifecycle methods — there is still no hook
   equivalent as of React 19:
   ┌──────────────────────────────────────────┬──────────────────────────────┐
   │ static getDerivedStateFromError(error)     │ Update state to show fallback │
   │ componentDidCatch(error, info)             │ Side effect: log to a service │
   └──────────────────────────────────────────┴──────────────────────────────┘

   WHAT ERROR BOUNDARIES CATCH vs DON'T CATCH:
   ┌────────────────────────────────────────┬─────────────────────────────┐
   │ CATCHES                                  │ DOES NOT CATCH               │
   ├────────────────────────────────────────┼─────────────────────────────┤
   │ Errors thrown during render              │ Event handler errors (use    │
   │ Errors in lifecycle methods               │   a plain try/catch there)   │
   │ Errors in constructors of the tree below  │ Errors in async code         │
   │                                           │   (setTimeout, fetch .then)  │
   │                                           │ Errors in the boundary       │
   │                                           │   itself (a parent boundary  │
   │                                           │   must catch those)          │
   │                                           │ SSR errors                   │
   └────────────────────────────────────────┴─────────────────────────────┘

   INTERVIEW: "Why can't this be a hook?"
   Hooks only run for the component that calls them — they can't intercept
   an exception thrown while React is rendering a DIFFERENT component
   further down the tree. Catching child-tree render errors requires React
   itself to call a lifecycle method on the nearest class ancestor when it
   catches the throw — there's no hook-based way to register that today.
   (The community `react-error-boundary` package just wraps this same class
   pattern behind a nicer functional-looking API.)

   GOTCHAS:
   1. One boundary can wrap many components — but a single boundary that
      wraps your ENTIRE app means one crashed widget takes down everything.
      Prefer several granular boundaries around independent UI regions.
   2. getDerivedStateFromError must be a pure function — no side effects,
      no setState calls, just return the new state.
   3. componentDidCatch is where you actually log to Sentry/similar — it
      receives a `componentStack` string in the second argument.
   4. After catching, you must give the user a way to retry/reset — the
      boundary itself doesn't auto-recover.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  fallback: { padding: 12, background: "#fdecea", color: "#611a15", borderRadius: 6, border: "1px solid #f5c6cb" },
};

/* ─── Example 1: A reusable ErrorBoundary class ─── */

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Pure — just compute the next state, no side effects here.
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // Side effect: this is where you'd send the error to a logging service.
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={styles.fallback}>
          <strong>Something went wrong:</strong> {this.state.error.message}
          <div>
            <button style={styles.btn} onClick={this.handleReset}>Reset</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ─── Example 2: A component that throws past a threshold ─── */

function BuggyCounter({ crashAt }) {
  const [count, setCount] = useState(0);

  if (count >= crashAt) {
    // Thrown during render — this is exactly what an Error Boundary catches.
    throw new Error(`Count reached ${count} (crash threshold: ${crashAt})`);
  }

  return (
    <div>
      <p style={{ fontSize: 24, fontFamily: "monospace" }}>{count}</p>
      <button style={styles.btn} onClick={() => setCount((c) => c + 1)}>
        Increment (crashes at {crashAt})
      </button>
    </div>
  );
}

function ErrorBoundaryDemo() {
  const [resetKey, setResetKey] = useState(0);

  return (
    <div style={styles.section}>
      <h3>1. Error Boundary Catching a Render Error</h3>
      <p>Click increment until it crashes — the fallback UI replaces only this subtree.</p>
      {/* key forces a fresh BuggyCounter (and clears its state) after reset */}
      <ErrorBoundary key={resetKey} onReset={() => setResetKey((k) => k + 1)}>
        <BuggyCounter crashAt={5} />
      </ErrorBoundary>
      <div style={styles.code}>{`class ErrorBoundary extends Component {
  static getDerivedStateFromError(error) {
    return { hasError: true, error }; // pure — update state to show fallback
  }
  componentDidCatch(error, info) {
    logToService(error, info.componentStack); // side effect — logging
  }
  render() {
    return this.state.hasError ? <Fallback/> : this.props.children;
  }
}`}</div>
    </div>
  );
}

/* ─── Example 3: What a boundary does NOT catch ─── */

function NotCaughtDemo() {
  const [clicked, setClicked] = useState(false);

  const handleClick = () => {
    try {
      throw new Error("Event handler error — must be try/catch'd manually");
    } catch (err) {
      setClicked(err.message);
    }
  };

  return (
    <div style={styles.section}>
      <h3>2. What Error Boundaries DON'T Catch</h3>
      <p>Errors thrown inside event handlers never reach a boundary — they must be handled locally:</p>
      <button style={styles.btn} onClick={handleClick}>Trigger event-handler error</button>
      {clicked && <div style={styles.fallback}>{clicked}</div>}
      <div style={styles.code}>{`// A throw here would NOT be caught by any ancestor ErrorBoundary:
<button onClick={() => { throw new Error("boom"); }} />

// Event handlers, async code (fetch/.then/setTimeout), and errors
// inside the boundary itself all need their own try/catch.`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function ErrorBoundaries() {
  return (
    <div style={styles.container}>
      <h2>Error Boundaries</h2>
      <ErrorBoundaryDemo />
      <NotCaughtDemo />
    </div>
  );
}
