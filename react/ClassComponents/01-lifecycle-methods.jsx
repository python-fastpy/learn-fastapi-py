import { Component, useEffect, useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   CLASS COMPONENT LIFECYCLE METHODS — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Before Hooks (React 16.8), all stateful logic lived in class components,
   split across named lifecycle methods tied to three phases:

   PHASE DIAGRAM:
   ┌──────────────────────────────────────────────────────────────────────┐
   │  MOUNTING                                                             │
   │    constructor()                                                      │
   │    static getDerivedStateFromProps(props, state)                      │
   │    render()                                                           │
   │    componentDidMount()          ← side effects, subscriptions, fetch  │
   │                                                                        │
   │  UPDATING (on new props/state)                                        │
   │    static getDerivedStateFromProps(props, state)                      │
   │    shouldComponentUpdate(nextProps, nextState)  ← return false to skip│
   │    render()                                                           │
   │    componentDidUpdate(prevProps, prevState)     ← react to changes    │
   │                                                                        │
   │  UNMOUNTING                                                           │
   │    componentWillUnmount()       ← cleanup: timers, listeners, subs    │
   └──────────────────────────────────────────────────────────────────────┘

   HOOKS EQUIVALENT MAPPING (the #1 "explain the difference" interview Q):
   ┌────────────────────────────────┬──────────────────────────────────────┐
   │ Class lifecycle method          │ Hook equivalent                       │
   ├────────────────────────────────┼──────────────────────────────────────┤
   │ constructor                     │ useState initial value                │
   │ componentDidMount               │ useEffect(fn, [])                     │
   │ componentDidUpdate              │ useEffect(fn, [deps])                 │
   │ componentDidMount + DidUpdate   │ useEffect(fn) — no deps array         │
   │   combined (runs every render)  │                                       │
   │ componentWillUnmount            │ the cleanup fn returned from useEffect│
   │ shouldComponentUpdate           │ React.memo() / useMemo() / useCallback│
   │ getDerivedStateFromProps        │ derive the value directly during      │
   │                                  │ render (no effect needed) — or reset  │
   │                                  │ state via a `key` prop change         │
   │ componentDidCatch (+ getDerived-│ NO hook equivalent — Error Boundaries │
   │   StateFromError)               │ must still be class components        │
   └────────────────────────────────┴──────────────────────────────────────┘

   INTERVIEW: "Why did hooks replace lifecycle methods?"
   Lifecycle methods group code by WHEN it runs (mount/update/unmount),
   forcing related logic (e.g. subscribe + unsubscribe) into two different
   methods far apart in the file. Hooks group code by WHAT it does — one
   useEffect colocates the setup AND its matching cleanup.

   GOTCHAS:
   1. componentDidUpdate runs after EVERY update unless you manually diff
      props/state and bail early — easy to cause infinite loops if you
      call setState unconditionally inside it.
   2. shouldComponentUpdate does a manual comparison; PureComponent does
      this automatically via a shallow prop/state comparison (like memo()).
   3. getDerivedStateFromProps is a static method — no access to `this`,
      called on EVERY render (mount and update), must return an object or
      null. Rarely needed; usually a smell that state shouldn't be state.
   4. componentWillMount / componentWillUpdate / componentWillReceiveProps
      are legacy/deprecated (unsafe with async rendering) — don't use them.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  log: { background: "#f5f5f5", padding: 8, borderRadius: 6, fontSize: 12, maxHeight: 140, overflowY: "auto", marginTop: 8 },
};

/* ─── Example 1: Class component logging every lifecycle method ─── */

class LifecycleLogger extends Component {
  constructor(props) {
    super(props);
    this.state = { renderCount: 0 };
    props.onLog("constructor()");
  }

  static getDerivedStateFromProps(props, state) {
    // Runs on EVERY render (mount + update). Return null if nothing to derive.
    return null;
  }

  componentDidMount() {
    this.props.onLog("componentDidMount() — subscribe / fetch here");
  }

  shouldComponentUpdate(nextProps, nextState) {
    this.props.onLog(`shouldComponentUpdate() — nextValue="${nextProps.value}"`);
    return true; // return false here to skip render + componentDidUpdate
  }

  componentDidUpdate(prevProps) {
    this.props.onLog(`componentDidUpdate() — value changed "${prevProps.value}" → "${this.props.value}"`);
  }

  componentWillUnmount() {
    this.props.onLog("componentWillUnmount() — cleanup timers/listeners here");
  }

  render() {
    this.props.onLog("render()");
    return (
      <div style={{ padding: 8, background: "#eef", borderRadius: 4 }}>
        Rendering with value: <strong>{this.props.value}</strong>
      </div>
    );
  }
}

function LifecycleDemo() {
  const [mounted, setMounted] = useState(true);
  const [value, setValue] = useState("initial");
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => setLogs((prev) => [...prev, msg]);

  return (
    <div style={styles.section}>
      <h3>1. Lifecycle Method Order (mount → update → unmount)</h3>
      <button style={styles.btn} onClick={() => setMounted((m) => !m)}>
        {mounted ? "Unmount" : "Mount"}
      </button>
      <button
        style={styles.btn}
        onClick={() => setValue((v) => (v === "initial" ? "updated" : "initial"))}
        disabled={!mounted}
      >
        Trigger Update
      </button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setLogs([])}>
        Clear Log
      </button>
      {mounted && <LifecycleLogger value={value} onLog={addLog} />}
      <div style={styles.log}>
        {logs.map((l, i) => <div key={i}>{i + 1}. {l}</div>)}
      </div>
    </div>
  );
}

/* ─── Example 2: The hooks equivalent, side by side ─── */

function HooksEquivalent() {
  const [mounted, setMounted] = useState(true);
  const [value, setValue] = useState("initial");
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => setLogs((prev) => [...prev, msg]);

  function Logger({ value }) {
    // componentDidMount + componentDidUpdate, combined via the deps array
    useEffect(() => {
      addLog(`useEffect setup — value="${value}"`);
      // componentWillUnmount, via the returned cleanup function
      return () => addLog(`useEffect cleanup — value="${value}"`);
    }, [value]);

    return (
      <div style={{ padding: 8, background: "#efe", borderRadius: 4 }}>
        Rendering with value: <strong>{value}</strong>
      </div>
    );
  }

  return (
    <div style={styles.section}>
      <h3>2. Same Behavior with Hooks (compare the log shape above)</h3>
      <button style={styles.btn} onClick={() => setMounted((m) => !m)}>
        {mounted ? "Unmount" : "Mount"}
      </button>
      <button
        style={styles.btn}
        onClick={() => setValue((v) => (v === "initial" ? "updated" : "initial"))}
        disabled={!mounted}
      >
        Trigger Update
      </button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={() => setLogs([])}>
        Clear Log
      </button>
      {mounted && <Logger value={value} />}
      <div style={styles.log}>
        {logs.map((l, i) => <div key={i}>{i + 1}. {l}</div>)}
      </div>
      <div style={styles.code}>{`useEffect(() => {
  // componentDidMount (first run) + componentDidUpdate (later runs)
  return () => { /* componentWillUnmount */ };
}, [value]); // shouldComponentUpdate's job is done by the deps array`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function LifecycleMethods() {
  return (
    <div style={styles.container}>
      <h2>Class Component Lifecycle Methods</h2>
      <LifecycleDemo />
      <HooksEquivalent />
    </div>
  );
}
