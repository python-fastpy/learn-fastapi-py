import { useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   UPDATING OBJECTS IN STATE
   ═══════════════════════════════════════════════════════════════════════════════

   RULE: State is READ-ONLY. Never mutate — always create NEW objects.

   ┌──────────────────────────────────────────────────────────┐
   │  WRONG (mutation):                                      │
   │  person.name = "New";  // mutates existing object       │
   │  setPerson(person);    // same reference → no re-render! │
   │                                                          │
   │  RIGHT (new object):                                    │
   │  setPerson({ ...person, name: "New" });                 │
   │  // spread creates copy → new reference → re-render ✓   │
   └──────────────────────────────────────────────────────────┘

   NESTED OBJECTS:
   ┌──────────────────────────────────────────────────────────┐
   │  setPerson({                                            │
   │    ...person,                       // copy top level   │
   │    address: {                                           │
   │      ...person.address,             // copy nested obj  │
   │      city: "New Delhi"              // override field   │
   │    }                                                    │
   │  });                                                    │
   └──────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. Spread (...) is SHALLOW copy — nested objects still share reference.
   2. You must spread at EVERY nesting level you want to update.
   3. Computed property names: [e.target.name] lets you handle
      multiple fields with one handler.
   4. Object.is(oldObj, newObj) determines re-render. Same reference = skip.
   5. NEVER do: state.field = value. Always create a new object.
   6. For deeply nested state, consider useReducer or flattening the shape.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  field: { marginBottom: 10 },
  label: { display: "block", marginBottom: 4, fontWeight: "bold", fontSize: 13 },
  input: { width: "100%", padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, boxSizing: "border-box" },
  output: { marginTop: 12, padding: 12, background: "#f5f5f5", borderRadius: 6, fontSize: 13, fontFamily: "monospace", whiteSpace: "pre" },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  bad: { background: "#fce4ec", padding: 12, borderRadius: 6, fontSize: 13, fontFamily: "monospace", whiteSpace: "pre" },
  good: { background: "#e8f5e9", padding: 12, borderRadius: 6, fontSize: 13, fontFamily: "monospace", whiteSpace: "pre" },
};

/* ─── Example 1: Simple Object Update ─── */

function SimpleObjectUpdate() {
  const [person, setPerson] = useState({
    firstName: "John",
    lastName: "Doe",
    email: "john@test.com",
  });

  // ONE handler for ALL fields using computed property names [name]
  const handleChange = (e) => {
    setPerson({
      ...person,                  // copy all existing fields
      [e.target.name]: e.target.value, // override the one that changed
    });
  };

  return (
    <div style={styles.section}>
      <h3>1. Simple Object — Computed Property Names</h3>

      <div style={styles.field}>
        <label style={styles.label}>First Name</label>
        <input style={styles.input} name="firstName" value={person.firstName} onChange={handleChange} />
      </div>
      <div style={styles.field}>
        <label style={styles.label}>Last Name</label>
        <input style={styles.input} name="lastName" value={person.lastName} onChange={handleChange} />
      </div>
      <div style={styles.field}>
        <label style={styles.label}>Email</label>
        <input style={styles.input} name="email" value={person.email} onChange={handleChange} />
      </div>

      <div style={styles.good}>{`// [e.target.name] = computed property name
handleChange = (e) => {
  setPerson({ ...person, [e.target.name]: e.target.value });
}`}</div>

      <div style={styles.output}>{JSON.stringify(person, null, 2)}</div>
    </div>
  );
}

/* ─── Example 2: Nested Object Update ─── */

function NestedObjectUpdate() {
  const [person, setPerson] = useState({
    name: "Niki de Saint Phalle",
    artwork: {
      title: "Blue Nana",
      city: "Hamburg",
      image: "https://example.com/nana.jpg",
    },
  });

  return (
    <div style={styles.section}>
      <h3>2. Nested Object — Spread at Every Level</h3>

      <div style={styles.field}>
        <label style={styles.label}>Name</label>
        <input
          style={styles.input}
          value={person.name}
          onChange={(e) =>
            setPerson({ ...person, name: e.target.value })
          }
        />
      </div>
      <div style={styles.field}>
        <label style={styles.label}>Artwork Title</label>
        <input
          style={styles.input}
          value={person.artwork.title}
          onChange={(e) =>
            setPerson({
              ...person,                       // copy top-level fields
              artwork: {
                ...person.artwork,             // copy nested object fields
                title: e.target.value,         // override just title
              },
            })
          }
        />
      </div>
      <div style={styles.field}>
        <label style={styles.label}>City</label>
        <input
          style={styles.input}
          value={person.artwork.city}
          onChange={(e) =>
            setPerson({
              ...person,
              artwork: { ...person.artwork, city: e.target.value },
            })
          }
        />
      </div>

      <div style={styles.good}>{`// Spread at EVERY nesting level:
setPerson({
  ...person,
  artwork: {
    ...person.artwork,
    city: "New Delhi"
  }
});`}</div>

      <div style={styles.output}>{JSON.stringify(person, null, 2)}</div>
    </div>
  );
}

/* ─── Example 3: Mutation Bug Demo ─── */

function MutationBugDemo() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleCorrectMove = (e) => {
    setPosition({ x: e.clientX, y: e.clientY }); // new object each time ✓
  };

  return (
    <div style={styles.section}>
      <h3>3. Why Mutation Fails</h3>

      <div style={styles.bad}>{`// WRONG — mutation:
position.x = e.clientX;   // mutates existing object
setPosition(position);     // same ref → React skips re-render!

// The object reference hasn't changed, so Object.is returns true,
// and React thinks nothing changed.`}</div>

      <div style={styles.good}>{`// RIGHT — new object:
setPosition({ x: e.clientX, y: e.clientY });
// New reference → Object.is returns false → re-render ✓`}</div>

      <div
        onPointerMove={handleCorrectMove}
        style={{ height: 100, background: "#e3f2fd", borderRadius: 8, position: "relative", cursor: "crosshair", marginTop: 8 }}
      >
        <div
          style={{
            width: 16, height: 16, borderRadius: "50%", background: "#1a73e8",
            position: "absolute",
            left: Math.min(position.x - 8, 484), top: Math.min(position.y - 8, 92),
            pointerEvents: "none",
          }}
        />
        <span style={{ position: "absolute", bottom: 4, right: 8, fontSize: 11, color: "#999" }}>
          Move mouse here — x: {position.x}, y: {position.y}
        </span>
      </div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UpdatingObjectsInState() {
  return (
    <div style={styles.container}>
      <h2>Updating Objects in State</h2>
      <SimpleObjectUpdate />
      <NestedObjectUpdate />
      <MutationBugDemo />
    </div>
  );
}
