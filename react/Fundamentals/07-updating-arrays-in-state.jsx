import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   UPDATING ARRAYS IN STATE
   ═══════════════════════════════════════════════════════════════════════════════

   Arrays in state must be treated as IMMUTABLE — never mutate, always
   return a new array.

   ┌────────────────┬──────────────────────┬──────────────────────────┐
   │ Operation      │ AVOID (mutates)      │ USE (returns new array)  │
   ├────────────────┼──────────────────────┼──────────────────────────┤
   │ Adding         │ push, unshift        │ concat, [...arr, item]   │
   │ Removing       │ pop, shift, splice   │ filter, slice            │
   │ Replacing      │ splice, arr[i] = x   │ map                      │
   │ Sorting        │ sort, reverse        │ [...arr].sort/reverse    │
   │ Inserting      │ splice               │ slice + spread           │
   └────────────────┴──────────────────────┴──────────────────────────┘

   GOTCHAS:
   1. arr.push(x) then setArr(arr) → SAME REFERENCE → no re-render!
   2. arr.sort() and arr.reverse() MUTATE the original. Copy first: [...arr].sort()
   3. slice (no p) returns a copy — safe. splice (with p) mutates — avoid!
   4. When updating objects INSIDE arrays, you need map + spread:
      arr.map(item => item.id === id ? { ...item, done: true } : item)
   5. filter returns a new array even if nothing was removed.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "6px 14px", margin: 2, cursor: "pointer", borderRadius: 4, border: "none", fontSize: 13 },
  add: { background: "#34a853", color: "#fff" },
  del: { background: "#ea4335", color: "#fff" },
  edit: { background: "#fbbc04", color: "#000" },
  primary: { background: "#1a73e8", color: "#fff" },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, marginRight: 8 },
  item: { display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: "1px solid #eee" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

let nextId = 4;

export default function UpdatingArraysInState() {
  const [items, setItems] = useState([
    { id: 1, text: "Learn React", done: false },
    { id: 2, text: "Build a project", done: false },
    { id: 3, text: "Deploy to production", done: true },
  ]);
  const [newText, setNewText] = useState("");

  /* ─── ADD (concat / spread) ─── */
  const handleAdd = () => {
    if (!newText.trim()) return;
    // [...items, newItem] creates a new array with the item appended
    setItems([...items, { id: nextId++, text: newText, done: false }]);
    setNewText("");
  };

  /* ─── ADD AT BEGINNING ─── */
  const handleAddFirst = () => {
    if (!newText.trim()) return;
    // [newItem, ...items] — prepend
    setItems([{ id: nextId++, text: newText, done: false }, ...items]);
    setNewText("");
  };

  /* ─── REMOVE (filter) ─── */
  const handleRemove = (id) => {
    // filter returns a NEW array excluding the item
    setItems(items.filter((item) => item.id !== id));
  };

  /* ─── TOGGLE (map + spread) ─── */
  const handleToggle = (id) => {
    // map returns a new array; spread creates a new object for the changed item
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, done: !item.done } : item
      )
    );
  };

  /* ─── REPLACE TEXT (map + spread) ─── */
  const handleRename = (id) => {
    const newName = prompt("New name:");
    if (!newName) return;
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, text: newName } : item
      )
    );
  };

  /* ─── INSERT AT INDEX (slice + spread) ─── */
  const handleInsertAt = (index) => {
    const text = prompt("Insert text:");
    if (!text) return;
    const newItem = { id: nextId++, text, done: false };
    setItems([
      ...items.slice(0, index),  // everything before
      newItem,                    // new item
      ...items.slice(index),     // everything after
    ]);
  };

  /* ─── REVERSE (copy first!) ─── */
  const handleReverse = () => {
    // MUST copy first — .reverse() mutates the original array!
    setItems([...items].reverse());
  };

  /* ─── SORT (copy first!) ─── */
  const handleSort = () => {
    setItems([...items].sort((a, b) => a.text.localeCompare(b.text)));
  };

  /* ─── MOVE UP ─── */
  const handleMoveUp = (index) => {
    if (index === 0) return;
    const copy = [...items];
    [copy[index - 1], copy[index]] = [copy[index], copy[index - 1]]; // swap
    setItems(copy);
  };

  return (
    <div style={styles.container}>
      <h2>Updating Arrays in State</h2>

      {/* ADD */}
      <div style={styles.section}>
        <h3>Add Items</h3>
        <div style={{ display: "flex" }}>
          <input
            style={styles.input}
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            placeholder="New item..."
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <button style={{ ...styles.btn, ...styles.add }} onClick={handleAdd}>Add End</button>
          <button style={{ ...styles.btn, ...styles.primary }} onClick={handleAddFirst}>Add Start</button>
        </div>
        <div style={styles.code}>{`// Add at end:   [...items, newItem]
// Add at start: [newItem, ...items]`}</div>
      </div>

      {/* LIST */}
      <div style={styles.section}>
        <h3>Todo List</h3>
        {items.map((item, index) => (
          <div key={item.id} style={styles.item}>
            <input type="checkbox" checked={item.done} onChange={() => handleToggle(item.id)} />
            <span style={{ flex: 1, textDecoration: item.done ? "line-through" : "none" }}>
              {item.text}
            </span>
            <button style={{ ...styles.btn, ...styles.edit }} onClick={() => handleRename(item.id)}>Edit</button>
            <button style={{ ...styles.btn, ...styles.del }} onClick={() => handleRemove(item.id)}>Del</button>
            <button style={{ ...styles.btn, ...styles.primary }} onClick={() => handleInsertAt(index)}>Insert↑</button>
            <button style={{ ...styles.btn, background: "#ccc" }} onClick={() => handleMoveUp(index)}>↑</button>
          </div>
        ))}
      </div>

      {/* BULK OPERATIONS */}
      <div style={styles.section}>
        <h3>Bulk Operations (copy-then-mutate)</h3>
        <button style={{ ...styles.btn, ...styles.primary }} onClick={handleReverse}>Reverse</button>
        <button style={{ ...styles.btn, ...styles.primary }} onClick={handleSort}>Sort A→Z</button>
        <div style={styles.code}>{`// WRONG: items.sort()     → mutates original!
// RIGHT: [...items].sort() → copies then sorts

// Remove:  items.filter(i => i.id !== id)
// Update:  items.map(i => i.id === id ? {...i, done:true} : i)
// Insert:  [...items.slice(0,idx), newItem, ...items.slice(idx)]
// Reverse: [...items].reverse()`}</div>
      </div>
    </div>
  );
}
