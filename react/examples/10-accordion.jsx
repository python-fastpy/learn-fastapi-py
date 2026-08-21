import { useState } from "react";

/*
  ACCORDION
  ─────────
  Two patterns shown:
    1. Single open — only one panel open at a time
    2. Multi open  — any combination of panels can be open

  Diagram (single open):
    ┌──────────────────────────────┐
    │ ▶ Section 1                  │  ← collapsed
    ├──────────────────────────────┤
    │ ▼ Section 2                  │  ← expanded
    │   Content for section 2...   │
    ├──────────────────────────────┤
    │ ▶ Section 3                  │  ← collapsed
    └──────────────────────────────┘

  State:
    Single open → activeIndex (number | null)
    Multi open  → openSet (Set of indices)

  Key concept:
    "Lifting state up" — parent owns which panel is open,
    child panels just receive isOpen and onToggle props.
*/

const SECTIONS = [
  {
    title: "What is React?",
    content:
      "React is a JavaScript library for building user interfaces. It lets you compose complex UIs from small, isolated pieces of code called components.",
  },
  {
    title: "What are hooks?",
    content:
      "Hooks are functions that let you use state and other React features in function components. useState, useEffect, useContext are the most common hooks.",
  },
  {
    title: "What is JSX?",
    content:
      "JSX is a syntax extension for JavaScript that looks like HTML. It gets compiled to React.createElement() calls. JSX is optional but widely used.",
  },
  {
    title: "What is Virtual DOM?",
    content:
      "The Virtual DOM is a lightweight copy of the real DOM. React uses it to batch and minimize actual DOM updates, improving performance.",
  },
];

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  accordion: { border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" },
  header: {
    padding: "12px 16px",
    background: "#f5f5f5",
    cursor: "pointer",
    userSelect: "none",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #ddd",
    fontWeight: "bold",
  },
  headerActive: { background: "#e8f0fe" },
  body: { padding: "12px 16px", borderBottom: "1px solid #ddd", lineHeight: 1.6 },
  arrow: { transition: "transform 0.2s", fontSize: 12 },
  arrowOpen: { transform: "rotate(90deg)" },
  toggle: { marginBottom: 16, display: "flex", gap: 8 },
  btn: { padding: "6px 14px", border: "1px solid #ccc", borderRadius: 4, cursor: "pointer", background: "#fff" },
  btnActive: { background: "#1a73e8", color: "#fff", borderColor: "#1a73e8" },
};

// ─── AccordionItem (dumb component — no state) ───────────────────────────────

function AccordionItem({ title, content, isOpen, onToggle }) {
  return (
    <div>
      <div
        style={{ ...styles.header, ...(isOpen ? styles.headerActive : {}) }}
        onClick={onToggle}
      >
        <span>{title}</span>
        <span style={{ ...styles.arrow, ...(isOpen ? styles.arrowOpen : {}) }}>
          ▶
        </span>
      </div>
      {isOpen && <div style={styles.body}>{content}</div>}
    </div>
  );
}

// ─── Main ────────────────────────────────────────────────────────────────────

export default function AccordionExample() {
  const [mode, setMode] = useState("single"); // "single" | "multi"
  const [activeIndex, setActiveIndex] = useState(null); // for single mode
  const [openSet, setOpenSet] = useState(new Set()); // for multi mode

  const handleToggle = (index) => {
    if (mode === "single") {
      // Click same → close. Click different → open that one.
      setActiveIndex((prev) => (prev === index ? null : index));
    } else {
      // Toggle this index in the Set
      setOpenSet((prev) => {
        const next = new Set(prev);
        next.has(index) ? next.delete(index) : next.add(index);
        return next;
      });
    }
  };

  const isOpen = (index) =>
    mode === "single" ? activeIndex === index : openSet.has(index);

  return (
    <div style={styles.container}>
      <h3>Accordion</h3>

      {/* Mode toggle */}
      <div style={styles.toggle}>
        <button
          style={{ ...styles.btn, ...(mode === "single" ? styles.btnActive : {}) }}
          onClick={() => setMode("single")}
        >
          Single Open
        </button>
        <button
          style={{ ...styles.btn, ...(mode === "multi" ? styles.btnActive : {}) }}
          onClick={() => setMode("multi")}
        >
          Multi Open
        </button>
      </div>

      <div style={styles.accordion}>
        {SECTIONS.map((section, index) => (
          <AccordionItem
            key={index}
            title={section.title}
            content={section.content}
            isOpen={isOpen(index)}
            onToggle={() => handleToggle(index)}
          />
        ))}
      </div>
    </div>
  );
}
