import { useState, useMemo, memo } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useMemo HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: const cached = useMemo(() => computeValue(a, b), [a, b])

   PURPOSE: Cache the RESULT of an expensive computation between renders.
   Only re-computes when dependencies change (Object.is comparison).

   DIAGRAM:
   ┌──────────────────────────────────────────────────────────┐
   │ Render 1: deps = [a, b]                                 │
   │   → runs computation, caches result                     │
   │                                                          │
   │ Render 2: deps = [a, b]  (same)                         │
   │   → SKIPS computation, returns cached result             │
   │                                                          │
   │ Render 3: deps = [a, c]  (changed!)                     │
   │   → re-runs computation, caches new result              │
   └──────────────────────────────────────────────────────────┘

   WHEN TO USE:
   1. Expensive calculations (filtering large arrays, sorting, etc.)
   2. Referential equality for object/array deps of other hooks
   3. Skipping re-renders of memo'd children (pass memoized object props)

   GOTCHAS:
   1. useMemo caches VALUES. useCallback caches FUNCTIONS.
      useMemo(() => fn) === useCallback(fn)
   2. Don't use useMemo for everything — it has overhead too.
      Only use when computation is genuinely expensive (>1ms).
   3. React MAY throw away the cache (e.g., scrolled offscreen).
      Your code MUST work without useMemo — it's an optimization, not
      a guarantee.
   4. Deps are compared with Object.is. Objects/arrays in deps
      that are re-created each render will defeat the cache.
   5. The function passed to useMemo runs DURING render (synchronous).
      No side effects allowed.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  input: { padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  perf: { background: "#fff3e0", padding: 8, borderRadius: 6, fontSize: 12, marginTop: 8 },
};

/* ─── Example 1: Expensive Calculation ─── */

function slowIsEven(num) {
  const start = performance.now();
  // Artificially slow — simulates heavy computation
  for (let i = 0; i < 50_000_000; i++) { /* busy wait */ }
  const elapsed = performance.now() - start;
  console.log(`slowIsEven(${num}) took ${elapsed.toFixed(0)}ms`);
  return num % 2 === 0;
}

function ExpensiveCalc() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState("");

  // WITHOUT useMemo: slowIsEven runs on EVERY render (even typing!)
  // WITH useMemo: only runs when `count` changes
  const isEven = useMemo(() => slowIsEven(count), [count]);

  return (
    <div style={styles.section}>
      <h3>1. Expensive Calculation</h3>
      <p>Count: {count} — {isEven ? "Even" : "Odd"}</p>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>+1 (recalculates)</button>
      <div style={{ marginTop: 8 }}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type here (no recalculation)"
          style={{ ...styles.input, width: "100%" }}
        />
      </div>
      <div style={styles.perf}>
        Without useMemo: typing would be laggy because slowIsEven runs on every keystroke.
        With useMemo: only runs when count changes.
      </div>
    </div>
  );
}

/* ─── Example 2: Filtering a Large List ─── */

const allItems = Array.from({ length: 1000 }, (_, i) => ({
  id: i,
  name: `Item ${i}`,
  category: ["Electronics", "Books", "Clothing", "Food"][i % 4],
}));

function FilteredList() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [highlight, setHighlight] = useState(false);

  // Only re-filters when search or category changes, not when highlight toggles
  const filtered = useMemo(() => {
    console.log("Filtering... (should NOT run when toggling highlight)");
    return allItems.filter((item) => {
      const matchSearch = item.name.toLowerCase().includes(search.toLowerCase());
      const matchCategory = category === "All" || item.category === category;
      return matchSearch && matchCategory;
    });
  }, [search, category]); // highlight is NOT a dependency

  return (
    <div style={styles.section}>
      <h3>2. Filtered List (1000 items)</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search..."
          style={styles.input}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)} style={{ padding: 6, borderRadius: 4 }}>
          <option>All</option>
          <option>Electronics</option>
          <option>Books</option>
          <option>Clothing</option>
          <option>Food</option>
        </select>
        <button style={{ ...styles.btn, background: highlight ? "#34a853" : "#ccc", color: highlight ? "#fff" : "#000" }} onClick={() => setHighlight(!highlight)}>
          Highlight
        </button>
      </div>
      <p>{filtered.length} results</p>
      <div style={{ maxHeight: 120, overflowY: "auto" }}>
        {filtered.slice(0, 20).map((item) => (
          <div key={item.id} style={{ padding: 4, background: highlight ? "#fff9c4" : "transparent" }}>
            {item.name} — {item.category}
          </div>
        ))}
        {filtered.length > 20 && <p style={{ color: "#999" }}>...and {filtered.length - 20} more</p>}
      </div>
    </div>
  );
}

/* ─── Example 3: Memoized Props for memo'd Children ─── */

const ExpensiveChild = memo(function ExpensiveChild({ data }) {
  console.log("ExpensiveChild rendered");
  return (
    <div style={{ padding: 8, border: "1px dashed #ccc", borderRadius: 4, marginTop: 8 }}>
      Items: {data.length} | First: {data[0]?.label || "none"}
    </div>
  );
});

function MemoizedPropsExample() {
  const [count, setCount] = useState(0);
  const [filter, setFilter] = useState("");

  // Without useMemo: { items: ... } creates new object each render
  // → memo(ExpensiveChild) re-renders anyway (new reference!)
  const data = useMemo(
    () => [
      { id: 1, label: `Filtered: ${filter || "all"}` },
      { id: 2, label: "Item B" },
    ],
    [filter] // only recreate when filter changes
  );

  return (
    <div style={styles.section}>
      <h3>3. Memoized Object Props</h3>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>
        Parent re-render ({count})
      </button>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Change filter (re-renders child)"
        style={{ ...styles.input, marginLeft: 8 }}
      />
      <ExpensiveChild data={data} />
      <div style={styles.code}>{`// Without useMemo: new object each render defeats memo()
const data = { items: [...] }; // ← new ref every time!

// With useMemo: same reference when deps unchanged
const data = useMemo(() => ({ items: [...] }), [dep]);`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseMemoExample() {
  return (
    <div style={styles.container}>
      <h2>useMemo Hook</h2>
      <ExpensiveCalc />
      <FilteredList />
      <MemoizedPropsExample />
    </div>
  );
}
