import { useState, useRef, useEffect } from "react";

/*
  INPUT SUGGESTION (Autocomplete)
  ────────────────────────────────
  Flow:
    User types → filter suggestions → show dropdown → click item → fill input

    ┌──────────────────────────┐
    │  [inp___________]        │  ← controlled input
    │  ┌────────────────────┐  │
    │  │ India              │  │  ← filtered suggestions list
    │  │ Indonesia          │  │
    │  │ Ireland            │  │
    │  └────────────────────┘  │
    └──────────────────────────┘

  Key concepts:
    - Filter on every keystroke (case-insensitive)
    - Click outside closes dropdown (useEffect + document listener)
    - Keyboard: Enter to select highlighted, Escape to close
*/

const COUNTRIES = [
  "India", "Indonesia", "Ireland", "Italy", "Iceland",
  "United States", "United Kingdom", "Ukraine",
  "Brazil", "Bangladesh", "Belgium",
  "Canada", "China", "Colombia",
  "France", "Finland",
  "Germany", "Greece",
  "Japan", "Jordan",
];

const styles = {
  wrapper: { position: "relative", width: 300, fontFamily: "sans-serif", padding: 20 },
  input: { width: "100%", padding: "8px 12px", fontSize: 14, border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" },
  dropdown: { position: "absolute", top: "100%", left: 20, right: 20, maxHeight: 200, overflowY: "auto", border: "1px solid #ddd", borderTop: "none", background: "#fff", borderRadius: "0 0 4px 4px", zIndex: 10 },
  item: { padding: "8px 12px", cursor: "pointer" },
  itemHighlight: { padding: "8px 12px", cursor: "pointer", background: "#e8f0fe" },
  noMatch: { padding: "8px 12px", color: "#999", fontStyle: "italic" },
};

export default function InputSuggestion() {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const wrapperRef = useRef(null);

  // Filter suggestions based on current input
  const suggestions = query.trim()
    ? COUNTRIES.filter((c) => c.toLowerCase().includes(query.toLowerCase()))
    : [];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (value) => {
    setQuery(value);
    setIsOpen(false);
    setHighlightIndex(-1);
  };

  const handleKeyDown = (e) => {
    if (!isOpen) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && highlightIndex >= 0) {
      handleSelect(suggestions[highlightIndex]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div ref={wrapperRef} style={styles.wrapper}>
      <h3>Country Search</h3>
      <input
        style={styles.input}
        value={query}
        placeholder="Type a country..."
        onChange={(e) => {
          setQuery(e.target.value);
          setIsOpen(true);
          setHighlightIndex(-1);
        }}
        onFocus={() => query && setIsOpen(true)}
        onKeyDown={handleKeyDown}
      />

      {isOpen && query.trim() && (
        <div style={styles.dropdown}>
          {suggestions.length > 0 ? (
            suggestions.map((item, idx) => (
              <div
                key={item}
                style={idx === highlightIndex ? styles.itemHighlight : styles.item}
                onMouseEnter={() => setHighlightIndex(idx)}
                onClick={() => handleSelect(item)}
              >
                {item}
              </div>
            ))
          ) : (
            <div style={styles.noMatch}>No matches</div>
          )}
        </div>
      )}
    </div>
  );
}
