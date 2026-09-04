import { useState } from "react";

/*
  BASIC FORM (Controlled)
  ───────────────────────
  Handles multiple input types:
    - text, email, password
    - textarea
    - select (dropdown)
    - radio buttons
    - checkbox
    - number / range

  Key concepts:
    - Single state object for all fields
    - Generic handleChange using computed property names: [e.target.name]
    - Checkbox uses e.target.checked instead of e.target.value
    - Form data logged on submit, form resets to initial state
*/

const INITIAL_STATE = {
  name: "",
  email: "",
  password: "",
  bio: "",
  role: "developer",
  gender: "",
  newsletter: false,
  experience: 1,
};

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 450 },
  field: { marginBottom: 14 },
  label: { display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 14 },
  input: { width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" },
  textarea: { width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box", minHeight: 80, resize: "vertical" },
  select: { width: "100%", padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4 },
  radioGroup: { display: "flex", gap: 16, marginTop: 4 },
  radioLabel: { display: "flex", alignItems: "center", gap: 4, cursor: "pointer" },
  checkLabel: { display: "flex", alignItems: "center", gap: 8, cursor: "pointer" },
  btn: { padding: "10px 24px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 14, marginRight: 8 },
  resetBtn: { padding: "10px 24px", background: "#ccc", color: "#000", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 14 },
  output: { marginTop: 16, padding: 12, background: "#f5f5f5", borderRadius: 6, fontSize: 13, whiteSpace: "pre-wrap" },
};

export default function FormExample() {
  const [form, setForm] = useState(INITIAL_STATE);
  const [submitted, setSubmitted] = useState(null);

  // Generic change handler — works for text, select, radio, number
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(form);
    console.log("Form data:", form);
  };

  const handleReset = () => {
    setForm(INITIAL_STATE);
    setSubmitted(null);
  };

  return (
    <div style={styles.container}>
      <h3>Basic Form</h3>

      <form onSubmit={handleSubmit}>
        {/* Text */}
        <div style={styles.field}>
          <label style={styles.label}>Name</label>
          <input style={styles.input} name="name" value={form.name} onChange={handleChange} placeholder="Enter name" />
        </div>

        {/* Email */}
        <div style={styles.field}>
          <label style={styles.label}>Email</label>
          <input style={styles.input} name="email" type="email" value={form.email} onChange={handleChange} placeholder="Enter email" />
        </div>

        {/* Password */}
        <div style={styles.field}>
          <label style={styles.label}>Password</label>
          <input style={styles.input} name="password" type="password" value={form.password} onChange={handleChange} />
        </div>

        {/* Textarea */}
        <div style={styles.field}>
          <label style={styles.label}>Bio</label>
          <textarea style={styles.textarea} name="bio" value={form.bio} onChange={handleChange} placeholder="Tell us about yourself" />
        </div>

        {/* Select */}
        <div style={styles.field}>
          <label style={styles.label}>Role</label>
          <select style={styles.select} name="role" value={form.role} onChange={handleChange}>
            <option value="developer">Developer</option>
            <option value="designer">Designer</option>
            <option value="manager">Manager</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Radio */}
        <div style={styles.field}>
          <label style={styles.label}>Gender</label>
          <div style={styles.radioGroup}>
            {["Male", "Female", "Other"].map((g) => (
              <label key={g} style={styles.radioLabel}>
                <input type="radio" name="gender" value={g.toLowerCase()} checked={form.gender === g.toLowerCase()} onChange={handleChange} />
                {g}
              </label>
            ))}
          </div>
        </div>

        {/* Checkbox */}
        <div style={styles.field}>
          <label style={styles.checkLabel}>
            <input type="checkbox" name="newsletter" checked={form.newsletter} onChange={handleChange} />
            Subscribe to newsletter
          </label>
        </div>

        {/* Range */}
        <div style={styles.field}>
          <label style={styles.label}>Experience: {form.experience} years</label>
          <input type="range" name="experience" min="0" max="20" value={form.experience} onChange={handleChange} style={{ width: "100%" }} />
        </div>

        <button style={styles.btn} type="submit">Submit</button>
        <button style={styles.resetBtn} type="button" onClick={handleReset}>Reset</button>
      </form>

      {submitted && (
        <div style={styles.output}>
          <strong>Submitted data:</strong>
          {"\n"}{JSON.stringify(submitted, null, 2)}
        </div>
      )}
    </div>
  );
}
