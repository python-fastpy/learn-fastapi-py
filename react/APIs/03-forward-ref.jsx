import { useState, useRef, forwardRef, useImperativeHandle } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   forwardRef — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: forwardRef((props, ref) => JSX)

   PURPOSE: Let a parent component pass a ref through to a child's DOM node.
   Without forwardRef, refs on custom components are undefined.

   DIAGRAM:
   ┌──────────────────────────────────────────────────────────────┐
   │  WITHOUT forwardRef:                                         │
   │  <MyInput ref={r} />  → ref.current = undefined             │
   │                                                              │
   │  WITH forwardRef:                                            │
   │  const MyInput = forwardRef((props, ref) =>                 │
   │    <input ref={ref} />                                      │
   │  )                                                           │
   │  <MyInput ref={r} />  → ref.current = <input> DOM node     │
   └──────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. ref is NOT a prop — you can't access props.ref in a regular component.
      forwardRef provides it as a second argument.
   2. You need forwardRef even if the child has only one element — React
      won't forward ref automatically to custom components.
   3. Combine with useImperativeHandle to expose a limited API instead
      of the raw DOM node (e.g., { scrollToTop(), focus() }).
   4. Works with memo: memo(forwardRef(...)) — order matters.
   5. React 19+: ref becomes a regular prop — forwardRef is being phased
      out but still works. Migration: just accept ref in props.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  input: { padding: "8px 12px", border: "2px solid #1a73e8", borderRadius: 4, width: "100%", boxSizing: "border-box" },
};

/* ─── Example 1: Basic forwardRef ─── */

const FancyInput = forwardRef(function FancyInput({ placeholder, label }, ref) {
  return (
    <div style={{ marginTop: 8 }}>
      {label && <label style={{ display: "block", fontSize: 12, marginBottom: 4, color: "#666" }}>{label}</label>}
      <input ref={ref} style={styles.input} placeholder={placeholder} />
    </div>
  );
});

function BasicForwardRef() {
  const inputRef = useRef(null);

  return (
    <div style={styles.section}>
      <h3>1. Basic forwardRef</h3>
      <FancyInput ref={inputRef} placeholder="Type here..." label="Name" />
      <button style={styles.btn} onClick={() => inputRef.current.focus()}>Focus Input</button>
      <button style={styles.btn} onClick={() => inputRef.current.select()}>Select All</button>
      <div style={styles.code}>{`// forwardRef wraps the component to receive ref:
const FancyInput = forwardRef((props, ref) => {
  return <input ref={ref} {...props} />;
});

// Parent can now access the DOM node:
const inputRef = useRef(null);
<FancyInput ref={inputRef} />
inputRef.current.focus(); // works!`}</div>
    </div>
  );
}

/* ─── Example 2: forwardRef + useImperativeHandle ─── */

const ScrollableList = forwardRef(function ScrollableList({ items }, ref) {
  const listRef = useRef(null);

  useImperativeHandle(ref, () => ({
    scrollToTop: () => { listRef.current.scrollTop = 0; },
    scrollToBottom: () => { listRef.current.scrollTop = listRef.current.scrollHeight; },
    scrollToIndex: (index) => {
      const child = listRef.current.children[index];
      if (child) child.scrollIntoView({ behavior: "smooth", block: "center" });
    },
  }));

  return (
    <div ref={listRef} style={{ height: 120, overflowY: "auto", border: "1px solid #ccc", borderRadius: 4, padding: 8, marginTop: 8 }}>
      {items.map((item, i) => (
        <div key={i} style={{ padding: "6px 8px", borderBottom: "1px solid #eee" }}>
          {i}. {item}
        </div>
      ))}
    </div>
  );
});

function ImperativeExample() {
  const listRef = useRef(null);
  const items = Array.from({ length: 30 }, (_, i) => `Item ${i}`);

  return (
    <div style={styles.section}>
      <h3>2. forwardRef + useImperativeHandle</h3>
      <ScrollableList ref={listRef} items={items} />
      <button style={styles.btn} onClick={() => listRef.current.scrollToTop()}>Scroll Top</button>
      <button style={styles.btn} onClick={() => listRef.current.scrollToBottom()}>Scroll Bottom</button>
      <button style={styles.btn} onClick={() => listRef.current.scrollToIndex(15)}>Go to #15</button>
      <div style={styles.code}>{`// Expose custom API instead of raw DOM:
useImperativeHandle(ref, () => ({
  scrollToTop: () => { ... },
  scrollToIndex: (i) => { ... },
}));`}</div>
    </div>
  );
}

/* ─── Example 3: Multi-ref forwarding ─── */

const FormField = forwardRef(function FormField({ label, type = "text" }, ref) {
  return (
    <div style={{ marginBottom: 8 }}>
      <label style={{ display: "block", fontSize: 12, color: "#666", marginBottom: 2 }}>{label}</label>
      <input ref={ref} type={type} style={{ ...styles.input, border: "1px solid #ccc" }} />
    </div>
  );
});

function MultiRefForm() {
  const nameRef = useRef(null);
  const emailRef = useRef(null);
  const [result, setResult] = useState("");

  const handleSubmit = () => {
    setResult(`Name: ${nameRef.current.value}, Email: ${emailRef.current.value}`);
  };

  return (
    <div style={styles.section}>
      <h3>3. Multiple forwardRef Fields</h3>
      <FormField ref={nameRef} label="Full Name" />
      <FormField ref={emailRef} label="Email" type="email" />
      <button style={styles.btn} onClick={() => nameRef.current.focus()}>Focus Name</button>
      <button style={styles.btn} onClick={() => emailRef.current.focus()}>Focus Email</button>
      <button style={{ ...styles.btn, background: "#34a853" }} onClick={handleSubmit}>Submit</button>
      {result && <p style={{ marginTop: 8 }}>{result}</p>}
      <div style={styles.code}>{`// Each forwardRef field gets its own ref:
const nameRef = useRef(null);
const emailRef = useRef(null);

<FormField ref={nameRef} label="Name" />
<FormField ref={emailRef} label="Email" />

// Access each independently:
nameRef.current.focus();
emailRef.current.value;`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function ForwardRefExample() {
  return (
    <div style={styles.container}>
      <h2>forwardRef</h2>
      <BasicForwardRef />
      <ImperativeExample />
      <MultiRefForm />
    </div>
  );
}
