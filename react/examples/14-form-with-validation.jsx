import { useState } from "react";

/*
  FORM WITH VALIDATION
  ────────────────────
  Validation types:
    1. Real-time (on change) — validate as user types
    2. On blur              — validate when field loses focus
    3. On submit            — validate all fields at once

  This example uses ON BLUR + ON SUBMIT (most common real-world pattern).

  Flow:
    ┌───────────────────────────────────┐
    │  User types in field              │
    │          │                        │
    │          ▼                        │
    │  User leaves field (blur)         │
    │          │                        │
    │          ▼                        │
    │  validateField(name, value)       │
    │     │              │              │
    │     ▼              ▼              │
    │  errors[name]=msg  errors[name]=''│
    │     │              │              │
    │     ▼              ▼              │
    │  Show error        Clear error    │
    │                                   │
    │  On submit → validateAll()        │
    │     │              │              │
    │     ▼              ▼              │
    │  Has errors?   No errors?         │
    │  Show all      Submit form        │
    └───────────────────────────────────┘

  Key concepts:
    - Separate `errors` state object (mirrors form fields)
    - `touched` tracks which fields user has interacted with
    - Validation only shows errors for touched fields (better UX)
    - Validation rules: required, minLength, email regex, password match
*/

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 400 },
  field: { marginBottom: 16 },
  label: { display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 },
  input: { width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" },
  inputError: { borderColor: "#ea4335" },
  error: { color: "#ea4335", fontSize: 12, marginTop: 4 },
  btn: { padding: "10px 24px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 14, width: "100%" },
  btnDisabled: { opacity: 0.5, cursor: "not-allowed" },
  success: { padding: 16, background: "#e8f5e9", borderRadius: 8, textAlign: "center", color: "#2e7d32" },
  hint: { color: "#999", fontSize: 12, marginTop: 2 },
};

// ─── Validation Rules ────────────────────────────────────────────────────────

function validateField(name, value, form) {
  switch (name) {
    case "name":
      if (!value.trim()) return "Name is required";
      if (value.trim().length < 2) return "Name must be at least 2 characters";
      return "";

    case "email":
      if (!value.trim()) return "Email is required";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Invalid email format";
      return "";

    case "password":
      if (!value) return "Password is required";
      if (value.length < 8) return "Password must be at least 8 characters";
      if (!/[A-Z]/.test(value)) return "Must contain at least one uppercase letter";
      if (!/[0-9]/.test(value)) return "Must contain at least one number";
      return "";

    case "confirmPassword":
      if (!value) return "Please confirm your password";
      if (value !== form.password) return "Passwords do not match";
      return "";

    case "age":
      if (!value) return "Age is required";
      if (isNaN(value) || Number(value) < 18) return "Must be 18 or older";
      if (Number(value) > 120) return "Invalid age";
      return "";

    default:
      return "";
  }
}

function validateAll(form) {
  const errors = {};
  Object.keys(form).forEach((key) => {
    const error = validateField(key, form[key], form);
    if (error) errors[key] = error;
  });
  return errors;
}

// ─── Component ───────────────────────────────────────────────────────────────

const INITIAL = { name: "", email: "", password: "", confirmPassword: "", age: "" };

export default function FormWithValidation() {
  const [form, setForm] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));

    // If field was already touched, validate on change too (real-time after first blur)
    if (touched[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: validateField(name, value, { ...form, [name]: value }),
      }));
    }
  };

  // Validate on blur (first touch)
  const handleBlur = (e) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({
      ...prev,
      [name]: validateField(name, value, form),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Mark all fields as touched
    const allTouched = Object.fromEntries(Object.keys(form).map((k) => [k, true]));
    setTouched(allTouched);

    // Validate everything
    const allErrors = validateAll(form);
    setErrors(allErrors);

    // If no errors, submit
    if (Object.keys(allErrors).length === 0) {
      setIsSubmitted(true);
      console.log("Form submitted:", form);
    }
  };

  // Helper to determine if field should show error
  const showError = (name) => touched[name] && errors[name];

  if (isSubmitted) {
    return (
      <div style={styles.container}>
        <div style={styles.success}>
          <h3>Registration Successful!</h3>
          <p>Welcome, {form.name}!</p>
          <button
            style={{ ...styles.btn, width: "auto", marginTop: 8 }}
            onClick={() => { setIsSubmitted(false); setForm(INITIAL); setErrors({}); setTouched({}); }}
          >
            Register Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h3>Registration Form (with Validation)</h3>

      <form onSubmit={handleSubmit} noValidate>
        {/* Name */}
        <div style={styles.field}>
          <label style={styles.label}>Name *</label>
          <input
            style={{ ...styles.input, ...(showError("name") ? styles.inputError : {}) }}
            name="name"
            value={form.name}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="Your name"
          />
          {showError("name") && <div style={styles.error}>{errors.name}</div>}
        </div>

        {/* Email */}
        <div style={styles.field}>
          <label style={styles.label}>Email *</label>
          <input
            style={{ ...styles.input, ...(showError("email") ? styles.inputError : {}) }}
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="you@example.com"
          />
          {showError("email") && <div style={styles.error}>{errors.email}</div>}
        </div>

        {/* Password */}
        <div style={styles.field}>
          <label style={styles.label}>Password *</label>
          <input
            style={{ ...styles.input, ...(showError("password") ? styles.inputError : {}) }}
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            onBlur={handleBlur}
          />
          <div style={styles.hint}>Min 8 chars, 1 uppercase, 1 number</div>
          {showError("password") && <div style={styles.error}>{errors.password}</div>}
        </div>

        {/* Confirm Password */}
        <div style={styles.field}>
          <label style={styles.label}>Confirm Password *</label>
          <input
            style={{ ...styles.input, ...(showError("confirmPassword") ? styles.inputError : {}) }}
            name="confirmPassword"
            type="password"
            value={form.confirmPassword}
            onChange={handleChange}
            onBlur={handleBlur}
          />
          {showError("confirmPassword") && <div style={styles.error}>{errors.confirmPassword}</div>}
        </div>

        {/* Age */}
        <div style={styles.field}>
          <label style={styles.label}>Age *</label>
          <input
            style={{ ...styles.input, ...(showError("age") ? styles.inputError : {}) }}
            name="age"
            type="number"
            value={form.age}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="18+"
          />
          {showError("age") && <div style={styles.error}>{errors.age}</div>}
        </div>

        <button style={styles.btn} type="submit">Register</button>
      </form>
    </div>
  );
}
