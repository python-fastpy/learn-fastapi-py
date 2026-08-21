import { useState, useMemo } from "react";

/*
  SORTABLE TABLE
  ──────────────
  Flow:
    Click column header → toggle sort direction → re-sort data → re-render

    ┌──────────────┬──────────┬───────┐
    │ Name ▲       │ Age ▼    │ City  │   ← click header to sort
    ├──────────────┼──────────┼───────┤
    │ Alice        │ 25       │ NYC   │
    │ Bob          │ 30       │ LA    │
    └──────────────┴──────────┴───────┘

  Key concepts:
    - Sort state: { key: 'name', direction: 'asc' | 'desc' }
    - Click same column → toggle direction
    - Click different column → sort ascending by new column
    - useMemo to avoid re-sorting on every render
    - localeCompare for string sorting, subtraction for numbers
*/

const DATA = [
  { id: 1, name: "Alice Johnson", age: 28, city: "New York", salary: 85000 },
  { id: 2, name: "Bob Smith", age: 34, city: "Los Angeles", salary: 92000 },
  { id: 3, name: "Charlie Brown", age: 22, city: "Chicago", salary: 65000 },
  { id: 4, name: "Diana Prince", age: 30, city: "Houston", salary: 78000 },
  { id: 5, name: "Eve Adams", age: 26, city: "Phoenix", salary: 71000 },
  { id: 6, name: "Frank Miller", age: 40, city: "Seattle", salary: 105000 },
  { id: 7, name: "Grace Lee", age: 29, city: "Denver", salary: 88000 },
];

const COLUMNS = [
  { key: "name", label: "Name", type: "string" },
  { key: "age", label: "Age", type: "number" },
  { key: "city", label: "City", type: "string" },
  { key: "salary", label: "Salary", type: "number" },
];

const styles = {
  container: { padding: 20, fontFamily: "sans-serif" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: { padding: "10px 14px", background: "#f5f5f5", borderBottom: "2px solid #ddd", cursor: "pointer", userSelect: "none", textAlign: "left" },
  td: { padding: "10px 14px", borderBottom: "1px solid #eee" },
  arrow: { marginLeft: 6, fontSize: 12 },
};

export default function SortableTable() {
  const [sortConfig, setSortConfig] = useState({ key: "name", direction: "asc" });

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      // Same column? Toggle. Different column? Default to asc.
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const sortedData = useMemo(() => {
    const { key, direction } = sortConfig;
    const col = COLUMNS.find((c) => c.key === key);
    const modifier = direction === "asc" ? 1 : -1;

    return [...DATA].sort((a, b) => {
      if (col.type === "string") {
        return a[key].localeCompare(b[key]) * modifier;
      }
      return (a[key] - b[key]) * modifier;
    });
  }, [sortConfig]);

  const getSortArrow = (key) => {
    if (sortConfig.key !== key) return "";
    return sortConfig.direction === "asc" ? " ▲" : " ▼";
  };

  return (
    <div style={styles.container}>
      <h3>Employee Table (Sortable)</h3>
      <table style={styles.table}>
        <thead>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                style={styles.th}
                onClick={() => handleSort(col.key)}
              >
                {col.label}
                <span style={styles.arrow}>{getSortArrow(col.key)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row) => (
            <tr key={row.id}>
              <td style={styles.td}>{row.name}</td>
              <td style={styles.td}>{row.age}</td>
              <td style={styles.td}>{row.city}</td>
              <td style={styles.td}>${row.salary.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
