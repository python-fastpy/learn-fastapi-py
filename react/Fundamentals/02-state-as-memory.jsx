import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   STATE — A COMPONENT'S MEMORY
   ═══════════════════════════════════════════════════════════════════════════════

   WHY local variables DON'T work:
   ┌──────────────────────────────────────────────┐
   │  let index = 0;  // declared inside component│
   │                                              │
   │  Problem 1: Local variables DON'T PERSIST    │
   │  between renders. React calls the function   │
   │  again → variable resets to 0.               │
   │                                              │
   │  Problem 2: Changing local variable DOESN'T  │
   │  TRIGGER a re-render. React doesn't know     │
   │  anything changed.                           │
   └──────────────────────────────────────────────┘

   useState solves BOTH:
   ┌──────────────────────────────────────────────┐
   │  const [index, setIndex] = useState(0);      │
   │                                              │
   │  ✓ Persists data between renders             │
   │  ✓ setIndex triggers re-render               │
   └──────────────────────────────────────────────┘

   GOTCHAS:
   1. useState returns [currentValue, setterFunction] — always destructure.
   2. Call hooks at TOP LEVEL only (not in if/else, loops, nested functions).
   3. Each component INSTANCE has its own isolated state. Two <Counter/>s
      on the page have completely independent state.
   4. State is preserved as long as the component is rendered at the same
      position in the tree. Change position or key → state resets.
   5. React batches state updates within event handlers — you won't see
      intermediate renders.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  img: { width: 200, height: 200, objectFit: "cover", borderRadius: 8, display: "block", margin: "8px 0" },
  code: { background: "#f5f5f5", padding: "2px 6px", borderRadius: 4, fontFamily: "monospace", fontSize: 13 },
};

const sculptures = [
  { name: "Humpback Whale", artist: "Unknown", description: "A majestic whale sculpture carved from driftwood." },
  { name: "The Thinker", artist: "Rodin", description: "A bronze sculpture of a man in deep thought." },
  { name: "David", artist: "Michelangelo", description: "A Renaissance masterpiece depicting the Biblical hero." },
  { name: "Venus de Milo", artist: "Alexandros", description: "An ancient Greek statue representing Aphrodite." },
];

/* ─── WRONG WAY: Local Variable (for demonstration) ─── */

function BrokenGallery() {
  let index = 0; // Resets to 0 every render!

  function handleNext() {
    index = index + 1; // Changes variable but doesn't trigger re-render
    console.log("index is now:", index); // Shows updated value in console...
    // ...but UI never updates because React doesn't know anything changed
  }

  return (
    <div style={styles.section}>
      <h3>BROKEN: Local Variable</h3>
      <p>Click Next — console shows index changing, but UI stays at 0.</p>
      <p><strong>{sculptures[index].name}</strong> by {sculptures[index].artist}</p>
      <button style={styles.btn} onClick={handleNext}>Next</button>
      <pre style={{ fontSize: 12, color: "#999" }}>{`let index = 0;
index = index + 1;  // ← no re-render!`}</pre>
    </div>
  );
}

/* ─── CORRECT WAY: useState ─── */

function WorkingGallery() {
  const [index, setIndex] = useState(0);
  const [showMore, setShowMore] = useState(false);

  const sculpture = sculptures[index];
  const hasNext = index < sculptures.length - 1;
  const hasPrev = index > 0;

  return (
    <div style={styles.section}>
      <h3>CORRECT: useState</h3>
      <p>
        <strong>{sculpture.name}</strong> by {sculpture.artist}
        <span style={{ color: "#999" }}> ({index + 1}/{sculptures.length})</span>
      </p>

      <button style={styles.btn} onClick={() => setIndex(index - 1)} disabled={!hasPrev}>Prev</button>
      <button style={styles.btn} onClick={() => setIndex(index + 1)} disabled={!hasNext}>Next</button>
      <button style={{ ...styles.btn, background: "#34a853" }} onClick={() => setShowMore(!showMore)}>
        {showMore ? "Hide" : "Show"} Details
      </button>

      {showMore && <p>{sculpture.description}</p>}
    </div>
  );
}

/* ─── ISOLATED STATE DEMO ─── */

function Counter({ label }) {
  const [count, setCount] = useState(0);
  return (
    <div style={{ display: "inline-block", padding: 12, margin: 8, border: "1px solid #ddd", borderRadius: 8 }}>
      <strong>{label}</strong>
      <div style={{ fontSize: 24, margin: "8px 0" }}>{count}</div>
      <button style={styles.btn} onClick={() => setCount(count + 1)}>+1</button>
    </div>
  );
}

/* ─── MAIN ─── */

export default function StateAsMemory() {
  return (
    <div style={styles.container}>
      <h2>State — Component Memory</h2>

      <BrokenGallery />
      <WorkingGallery />

      {/* Each Counter has its OWN state — clicking one doesn't affect the other */}
      <div style={styles.section}>
        <h3>Isolated State</h3>
        <p>Each component instance has its own state. Clicking one counter doesn't affect the other.</p>
        <Counter label="Counter A" />
        <Counter label="Counter B" />
      </div>
    </div>
  );
}
