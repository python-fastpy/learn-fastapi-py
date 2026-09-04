import { useState, useRef } from "react";

/*
  CONTROLLED vs UNCONTROLLED COMPONENTS
  ──────────────────────────────────────

  ┌──────────────────────────────┬──────────────────────────────┐
  │       CONTROLLED             │       UNCONTROLLED           │
  ├──────────────────────────────┼──────────────────────────────┤
  │ React state owns the value  │ DOM owns the value           │
  │ value={state}               │ defaultValue="initial"       │
  │ onChange updates state       │ Read via ref when needed     │
  │ Re-renders on every change   │ No re-render on typing       │
  │ Can validate/transform live  │ Validate only on submit      │
  │ Predictable, testable        │ Less code, more "form-like"  │
  └──────────────────────────────┴──────────────────────────────┘

  When to use which:
    Controlled  → form validation, conditional logic, formatting as-you-type
    Uncontrolled → simple forms, file inputs, integration with non-React code

  Rule of thumb:
    If you need to REACT to each keystroke → controlled
    If you only need the value on SUBMIT  → uncontrolled is fine
*/

const styles = {
  container: { padding: 20, fontFamily: "sans-serif" },
  section: { marginBottom: 32, padding: 16, border: "1px solid #ddd", borderRadius: 8 },
  label: { display: "block", marginBottom: 6, fontWeight: "bold" },
  input: { padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box", marginBottom: 8 },
  btn: { padding: "8px 16px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", marginTop: 8 },
  output: { marginTop: 8, padding: 8, background: "#f5f5f5", borderRadius: 4, fontSize: 13 },
  badge: { display: "inline-block", padding: "2px 8px", borderRadius: 12, fontSize: 12, fontWeight: "bold", marginBottom: 8 },
};

// ─── CONTROLLED Component ────────────────────────────────────────────────────

function ControlledForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  // We can validate / transform on every keystroke
  const isEmailValid = email === "" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const handleSubmit = (e) => {
    e.preventDefault();
    alert(`Controlled Submit:\nName: ${name}\nEmail: ${email}`);
  };

  return (
    <div style={styles.section}>
      <span style={{ ...styles.badge, background: "#e8f0fe", color: "#1a73e8" }}>
        CONTROLLED
      </span>
      <p>React state = source of truth. Each keystroke → setState → re-render.</p>

      <form onSubmit={handleSubmit}>
        <label style={styles.label}>Name</label>
        <input
          style={styles.input}
          value={name}           // ← React controls the value
          onChange={(e) => setName(e.target.value)}  // ← every keystroke updates state
        />

        <label style={styles.label}>Email</label>
        <input
          style={{
            ...styles.input,
            borderColor: isEmailValid ? "#ccc" : "red",
          }}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        {!isEmailValid && (
          <div style={{ color: "red", fontSize: 12 }}>Invalid email format</div>
        )}

        <button style={styles.btn} type="submit">Submit</button>
      </form>

      {/* Live preview — possible because state updates on every keystroke */}
      <div style={styles.output}>
        <strong>Live state:</strong> name="{name}", email="{email}"
      </div>
    </div>
  );
}

// ─── UNCONTROLLED Component ──────────────────────────────────────────────────

function UncontrolledForm() {
  const nameRef = useRef(null);
  const emailRef = useRef(null);
  const [submitted, setSubmitted] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Read values from DOM refs only on submit
    setSubmitted({
      name: nameRef.current.value,
      email: emailRef.current.value,
    });
    alert(
      `Uncontrolled Submit:\nName: ${nameRef.current.value}\nEmail: ${emailRef.current.value}`
    );
  };

  return (
    <div style={styles.section}>
      <span style={{ ...styles.badge, background: "#fce4ec", color: "#c62828" }}>
        UNCONTROLLED
      </span>
      <p>DOM = source of truth. React doesn't know the value until you read the ref.</p>

      <form onSubmit={handleSubmit}>
        <label style={styles.label}>Name</label>
        <input
          style={styles.input}
          ref={nameRef}                    // ← ref instead of value
          defaultValue="John"              // ← initial value (not controlled)
        />

        <label style={styles.label}>Email</label>
        <input
          style={styles.input}
          ref={emailRef}
          defaultValue="john@test.com"
        />

        <button style={styles.btn} type="submit">Submit</button>
      </form>

      {/* No live preview — React has no access to current value until submit */}
      <div style={styles.output}>
        <strong>Last submitted:</strong>{" "}
        {submitted
          ? `name="${submitted.name}", email="${submitted.email}"`
          : "Not submitted yet — type freely, no re-renders happening!"}
      </div>
    </div>
  );
}

// ─── Main ────────────────────────────────────────────────────────────────────

export default function ControlledVsUncontrolled() {
  return (
    <div style={styles.container}>
      <h3>Controlled vs Uncontrolled</h3>
      <ControlledForm />
      <UncontrolledForm />
    </div>
  );
}
