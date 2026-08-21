import { useState } from "react";

/*
  NESTED CHECKBOX (Parent ↔ Child)
  ─────────────────────────────────
  Diagram:
    ┌─ [✓] Select All Fruits        ← parent (checked if ALL children checked)
    │   ├─ [✓] Apple                 ← indeterminate if SOME checked
    │   ├─ [✓] Banana
    │   ├─ [ ] Cherry
    │   └─ [✓] Date

  Logic:
    - Click parent → toggles ALL children
    - Click child  → parent auto-updates:
        all checked    → parent checked
        some checked   → parent indeterminate (via ref)
        none checked   → parent unchecked

  Key concept:
    `indeterminate` is NOT a React prop — it's a DOM property.
    We must set it via ref: `ref.current.indeterminate = true`
*/

import { useRef, useEffect } from "react";

const styles = {
  container: { padding: 20, fontFamily: "sans-serif" },
  parent: { fontWeight: "bold", marginBottom: 8, display: "flex", alignItems: "center", gap: 8 },
  child: { marginLeft: 24, marginBottom: 6, display: "flex", alignItems: "center", gap: 8 },
};

const ITEMS = ["Apple", "Banana", "Cherry", "Date"];

export default function NestedCheckbox() {
  const [checked, setChecked] = useState(() =>
    Object.fromEntries(ITEMS.map((item) => [item, false]))
  );

  const parentRef = useRef(null);

  const allChecked = ITEMS.every((item) => checked[item]);
  const someChecked = ITEMS.some((item) => checked[item]);

  // Set indeterminate via DOM ref (can't do it with JSX props)
  useEffect(() => {
    if (parentRef.current) {
      parentRef.current.indeterminate = someChecked && !allChecked;
    }
  }, [someChecked, allChecked]);

  const handleParentToggle = () => {
    // If all or some are checked → uncheck all. If none → check all.
    const newValue = !allChecked;
    setChecked(Object.fromEntries(ITEMS.map((item) => [item, newValue])));
  };

  const handleChildToggle = (item) => {
    setChecked((prev) => ({ ...prev, [item]: !prev[item] }));
  };

  return (
    <div style={styles.container}>
      <h3>Nested Checkbox</h3>

      {/* Parent checkbox */}
      <div style={styles.parent}>
        <input
          type="checkbox"
          ref={parentRef}
          checked={allChecked}
          onChange={handleParentToggle}
        />
        <span>Select All Fruits</span>
      </div>

      {/* Child checkboxes */}
      {ITEMS.map((item) => (
        <div key={item} style={styles.child}>
          <input
            type="checkbox"
            checked={checked[item]}
            onChange={() => handleChildToggle(item)}
          />
          <span>{item}</span>
        </div>
      ))}
    </div>
  );
}
