import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   KEYS & LIST RECONCILIATION — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   When React re-renders a list, it needs to match each element in the new
   list to an element in the old list to decide: reuse (update in place),
   create (mount new), or destroy (unmount). `key` is the ONLY signal React
   uses to make that match — without stable keys, it falls back to matching
   by POSITION (index), which breaks the moment the list reorders.

   DIAGRAM — removing the FIRST item from a list of inputs:
   ┌─────────────────────────────┬─────────────────────────────────────────┐
   │ WITH key={index} (BROKEN)    │ WITH key={item.id} (CORRECT)             │
   ├─────────────────────────────┼─────────────────────────────────────────┤
   │ before: [0:"Apple"] [1:"Ban"]│ before: [id1:"Apple"] [id2:"Ban"]        │
   │ delete "Apple" (first item)  │ delete "Apple" (first item)              │
   │ after:  [0:"Ban"]             │ after:  [id2:"Ban"]                      │
   │                               │                                           │
   │ React sees key=0 in BOTH     │ React sees id1 is GONE, id2's key (id2)  │
   │ renders → thinks it's the    │ is UNCHANGED → correctly reuses id2's    │
   │ SAME element → reuses it,    │ DOM node/state, and unmounts id1's node. │
   │ but its DATA changed from    │                                           │
   │ "Apple" to "Ban" WITHOUT     │                                           │
   │ unmounting → any per-item    │                                           │
   │ state (e.g. a typed input    │                                           │
   │ value) STICKS to the wrong   │                                           │
   │ row!                         │                                           │
   └─────────────────────────────┴─────────────────────────────────────────┘

   WHEN key={index} IS ACTUALLY SAFE:
   - The list is static and NEVER reordered, filtered, or has items
     inserted/removed in the middle.
   - List items have no per-item state and no uncontrolled inputs.
   If either of those isn't true, use a stable, unique `id` from your data.

   INTERVIEW: "Why not just use the array index as the key?"
   Because the index describes POSITION, not IDENTITY. React needs
   identity to know "is this the same logical item as before" — position
   changes on every insert/delete/reorder even though the underlying item
   didn't change at all.

   GOTCHAS:
   1. Keys only need to be unique among SIBLINGS, not globally unique
      across the whole app.
   2. Changing a key on purpose is a valid trick to FORCE a full
      remount (reset all internal state) — e.g. `key={resetToken}`.
   3. Keys are NOT passed to your component as a prop — if you need the
      id inside the component too, pass it again explicitly.
   4. `key` must be on the outermost element returned from `.map()`, not
      on some element nested inside it.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  row: { display: "flex", gap: 8, alignItems: "center", marginBottom: 6 },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, flex: 1 },
};

const INITIAL_FRUITS = [
  { id: 1, name: "Apple" },
  { id: 2, name: "Banana" },
  { id: 3, name: "Cherry" },
];

/* ─── Example: toggle between index-as-key (buggy) and id-as-key (correct) ─── */

function FruitList({ fruits, useIndexAsKey }) {
  return (
    <div>
      {fruits.map((fruit, index) => (
        <div key={useIndexAsKey ? index : fruit.id} style={styles.row}>
          <span style={{ width: 70 }}>{fruit.name}</span>
          {/* Uncontrolled input: its value lives in the DOM node itself,
              so it visibly reveals whether React reused the RIGHT node. */}
          <input style={styles.input} placeholder="type a note for this row..." />
        </div>
      ))}
    </div>
  );
}

function KeysDemo() {
  const [fruits, setFruits] = useState(INITIAL_FRUITS);
  const [useIndexAsKey, setUseIndexAsKey] = useState(true);

  const removeFirst = () => setFruits((prev) => prev.slice(1));
  const reset = () => setFruits(INITIAL_FRUITS);

  return (
    <div style={styles.section}>
      <h3>Index Key vs Stable Id Key</h3>
      <p>
        1. Type something into each input's note field.<br />
        2. Click "Remove first row".<br />
        3. With <strong>index as key</strong>, the notes shift up with the wrong
        fruit name. With <strong>id as key</strong>, the removed row's note
        disappears with it and the rest stay correctly attached.
      </p>
      <div style={{ marginBottom: 8 }}>
        <label>
          <input
            type="checkbox"
            checked={useIndexAsKey}
            onChange={(e) => setUseIndexAsKey(e.target.checked)}
          />{" "}
          Use <code>key={"{index}"}</code> (buggy mode)
        </label>
      </div>
      <FruitList fruits={fruits} useIndexAsKey={useIndexAsKey} />
      <button style={styles.btn} onClick={removeFirst} disabled={fruits.length === 0}>
        Remove first row
      </button>
      <button style={{ ...styles.btn, background: "#ccc", color: "#000" }} onClick={reset}>
        Reset
      </button>
      <div style={styles.code}>{`// BROKEN — position becomes identity:
fruits.map((fruit, i) => <Row key={i} .../>)

// CORRECT — a stable id IS the identity, independent of position:
fruits.map((fruit) => <Row key={fruit.id} .../>)`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function KeysAndListReconciliation() {
  return (
    <div style={styles.container}>
      <h2>Keys & List Reconciliation</h2>
      <KeysDemo />
    </div>
  );
}
