import { useState, useMemo } from "react";

/*
  FILTER LIST
  ────────────
  Flow:
    Full list → user types in search + selects category → filtered list displayed

    ┌─────────────────────────────────────────┐
    │ [Search............]  [Category ▾]      │
    │                                         │
    │  ● React — Frontend — $49               │
    │  ● Node.js — Backend — $39              │
    │  ● Python — Backend — $29               │
    └─────────────────────────────────────────┘

  Key concepts:
    - useMemo to avoid re-filtering on every render (only when inputs change)
    - Multiple filter criteria combined with AND logic
    - Case-insensitive search
*/

const PRODUCTS = [
  { id: 1, name: "React Masterclass", category: "Frontend", price: 49 },
  { id: 2, name: "Vue Deep Dive", category: "Frontend", price: 39 },
  { id: 3, name: "Angular Bootcamp", category: "Frontend", price: 45 },
  { id: 4, name: "Node.js Complete", category: "Backend", price: 39 },
  { id: 5, name: "Django for Pros", category: "Backend", price: 29 },
  { id: 6, name: "FastAPI Guide", category: "Backend", price: 25 },
  { id: 7, name: "AWS Cloud", category: "DevOps", price: 59 },
  { id: 8, name: "Docker & K8s", category: "DevOps", price: 55 },
  { id: 9, name: "SQL Mastery", category: "Database", price: 35 },
  { id: 10, name: "MongoDB Essentials", category: "Database", price: 30 },
];

const CATEGORIES = ["All", ...new Set(PRODUCTS.map((p) => p.category))];

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  controls: { display: "flex", gap: 12, marginBottom: 16 },
  input: { flex: 1, padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4 },
  select: { padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4 },
  card: { padding: 12, border: "1px solid #e0e0e0", borderRadius: 6, marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" },
  name: { fontWeight: "bold" },
  badge: { background: "#e8f0fe", padding: "2px 8px", borderRadius: 12, fontSize: 12, color: "#1a73e8" },
  count: { color: "#666", fontSize: 14, marginTop: 8 },
};

export default function FilterExample() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");

  // useMemo: recalculate only when search or category changes
  const filtered = useMemo(() => {
    return PRODUCTS.filter((p) => {
      const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase());
      const matchesCategory = category === "All" || p.category === category;
      return matchesSearch && matchesCategory; // AND logic
    });
  }, [search, category]);

  return (
    <div style={styles.container}>
      <h3>Course Filter</h3>

      <div style={styles.controls}>
        <input
          style={styles.input}
          placeholder="Search courses..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          style={styles.select}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {filtered.map((p) => (
        <div key={p.id} style={styles.card}>
          <div>
            <div style={styles.name}>{p.name}</div>
            <span style={styles.badge}>{p.category}</span>
          </div>
          <div>${p.price}</div>
        </div>
      ))}

      <div style={styles.count}>{filtered.length} results</div>
    </div>
  );
}
