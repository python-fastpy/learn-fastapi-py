import { Fragment, useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   Fragments — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature:
     <Fragment>...</Fragment>  or  <>...</>  (shorthand)
     <Fragment key={id}>...</Fragment>  (with key — can't use shorthand)

   PURPOSE: Group elements without adding extra DOM nodes.

   DIAGRAM:
   ┌───────────────────────────────────────────────────────────────┐
   │  With <div> wrapper:              With Fragment:              │
   │  <div>              (extra DOM)   <></>   (no DOM node)       │
   │    <td>A</td>                     <td>A</td>                 │
   │    <td>B</td>                     <td>B</td>                 │
   │  </div>                                                      │
   │                                                               │
   │  <table><tr><div><td>  ← INVALID HTML!                       │
   │  <table><tr><td>       ← valid with Fragment                 │
   └───────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. <></> (shorthand) does NOT support key or any other props.
      Use <Fragment key={id}> when you need a key.
   2. Fragments don't create DOM nodes — no styling, no event handlers,
      no refs on fragments.
   3. key is the ONLY prop that Fragment accepts.
   4. Common use case: returning multiple elements from map().
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  table: { width: "100%", borderCollapse: "collapse", marginTop: 8 },
  td: { padding: 8, border: "1px solid #ddd" },
};

/* ─── Example 1: Basic Fragment ─── */

function Greeting({ name }) {
  // Without Fragment, you'd need a wrapper div
  return (
    <>
      <h4>Hello, {name}!</h4>
      <p>Welcome to Fragments.</p>
    </>
  );
}

function BasicExample() {
  return (
    <div style={styles.section}>
      <h3>1. Basic Fragment (no extra DOM)</h3>
      <Greeting name="React Developer" />
      <div style={styles.code}>{`// Shorthand: no key needed
return (
  <>
    <h4>Hello</h4>
    <p>World</p>
  </>
);`}</div>
    </div>
  );
}

/* ─── Example 2: Fragment with key (in lists) ─── */

function GlossaryList() {
  const terms = [
    { id: 1, term: "JSX", definition: "JavaScript XML — syntax extension for React." },
    { id: 2, term: "Props", definition: "Read-only data passed from parent to child." },
    { id: 3, term: "State", definition: "Mutable data that triggers re-renders on change." },
    { id: 4, term: "Hook", definition: "Functions that let you use React features in function components." },
  ];

  return (
    <div style={styles.section}>
      <h3>2. Fragment with key (list rendering)</h3>
      <dl>
        {terms.map((item) => (
          // MUST use explicit Fragment (not <></>) to pass key
          <Fragment key={item.id}>
            <dt style={{ fontWeight: "bold", marginTop: 8 }}>{item.term}</dt>
            <dd style={{ margin: "0 0 0 20px", color: "#555" }}>{item.definition}</dd>
          </Fragment>
        ))}
      </dl>
      <div style={styles.code}>{`// Shorthand <></> can't have key!
// Must use <Fragment key={id}>:
terms.map(item => (
  <Fragment key={item.id}>
    <dt>{item.term}</dt>
    <dd>{item.definition}</dd>
  </Fragment>
))`}</div>
    </div>
  );
}

/* ─── Example 3: Table Rows (semantic HTML) ─── */

function UserRow({ user }) {
  // Can't wrap <td> in <div> inside a <tr> — Fragment is the answer
  return (
    <>
      <td style={styles.td}>{user.name}</td>
      <td style={styles.td}>{user.email}</td>
      <td style={styles.td}>{user.role}</td>
    </>
  );
}

function TableExample() {
  const users = [
    { id: 1, name: "Alice", email: "alice@test.com", role: "Admin" },
    { id: 2, name: "Bob", email: "bob@test.com", role: "User" },
    { id: 3, name: "Charlie", email: "charlie@test.com", role: "Editor" },
  ];

  return (
    <div style={styles.section}>
      <h3>3. Table Rows (valid HTML needs Fragment)</h3>
      <table style={styles.table}>
        <thead>
          <tr style={{ background: "#f5f5f5" }}>
            <th style={styles.td}>Name</th>
            <th style={styles.td}>Email</th>
            <th style={styles.td}>Role</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <UserRow user={user} />
            </tr>
          ))}
        </tbody>
      </table>
      <div style={styles.code}>{`// <div> inside <tr> = INVALID HTML
// Fragment adds no DOM node:
function UserRow({ user }) {
  return (
    <>
      <td>{user.name}</td>
      <td>{user.email}</td>
    </>
  );
}`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function FragmentsExample() {
  return (
    <div style={styles.container}>
      <h2>Fragments</h2>
      <BasicExample />
      <GlossaryList />
      <TableExample />
    </div>
  );
}
