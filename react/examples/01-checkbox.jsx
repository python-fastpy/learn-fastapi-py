import { useState } from "react";

/*
  CHECKBOX EXAMPLE
  ─────────────────
  Flow:
    User clicks checkbox → onChange fires → setState toggles boolean → re-render

  Key concept:
    Checkbox is a CONTROLLED component — React state is the single source of truth.
    The `checked` prop always reflects state, `onChange` updates state.
*/

const styles = {
  container: { padding: 20, fontFamily: "sans-serif" },
  item: { display: "flex", alignItems: "center", gap: 8, marginBottom: 8 },
  label: { cursor: "pointer", userSelect: "none" },
  summary: { marginTop: 16, padding: 12, background: "#f0f0f0", borderRadius: 6 },
};

const FRUITS = ["Apple", "Banana", "Cherry", "Date", "Elderberry"];

export default function CheckboxExample() {
  // Object tracks each fruit's checked state: { Apple: false, Banana: true, ... }
  const [selected, setSelected] = useState({});

  const handleToggle = (fruit) => {
    setSelected((prev) => ({
      ...prev,
      [fruit]: !prev[fruit], // toggle: true ↔ false
    }));
  };

  const selectedFruits = Object.keys(selected).filter((k) => selected[k]);

  return (
    <div style={styles.container}>
      <h3>Pick your fruits</h3>

      {FRUITS.map((fruit) => (
        <div key={fruit} style={styles.item}>
          <input
            type="checkbox"
            id={fruit}
            checked={!!selected[fruit]} // !! converts undefined → false
            onChange={() => handleToggle(fruit)}
          />
          <label htmlFor={fruit} style={styles.label}>
            {fruit}
          </label>
        </div>
      ))}

      <div style={styles.summary}>
        <strong>Selected:</strong>{" "}
        {selectedFruits.length > 0 ? selectedFruits.join(", ") : "None"}
      </div>
    </div>
  );
}
