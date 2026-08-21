import { useState, useEffect } from "react";

/*
  HIGHER-ORDER COMPONENT (HOC)
  ────────────────────────────
  What: A function that takes a component and returns a NEW component
        with additional behavior/props injected.

  Pattern:
    const EnhancedComponent = withSomething(OriginalComponent);

  Diagram:
    ┌──────────────┐      ┌───────────────┐      ┌──────────────────┐
    │ Original     │ --→  │  HOC          │ --→  │ Enhanced         │
    │ Component    │      │  withLoader() │      │ Component        │
    │ (no loader)  │      │               │      │ (has loader!)    │
    └──────────────┘      └───────────────┘      └──────────────────┘

  When to use:
    - Cross-cutting concerns (auth, logging, loading)
    - Before hooks existed, HOCs were the primary reuse pattern
    - Today: prefer custom hooks for most cases
    - HOCs still useful when you need to WRAP JSX (e.g., error boundaries, layouts)

  Common HOC examples:
    - withAuth   → redirect if not logged in
    - withLoader → show spinner while loading
    - withLogger → log props on every render
*/

const styles = {
  container: { padding: 20, fontFamily: "sans-serif" },
  card: { padding: 16, border: "1px solid #ddd", borderRadius: 8, marginBottom: 12 },
  loading: { textAlign: "center", padding: 40, color: "#999" },
  logEntry: { fontSize: 12, color: "#666", padding: "2px 0" },
  section: { marginBottom: 24 },
};

// ─── HOC 1: withLoader ───────────────────────────────────────────────────────
// Shows a loading spinner while `isLoading` prop is true

function withLoader(WrappedComponent, loadingMessage = "Loading...") {
  // Return a new component
  return function WithLoaderComponent({ isLoading, ...rest }) {
    if (isLoading) {
      return <div style={styles.loading}>{loadingMessage}</div>;
    }
    // Pass all remaining props to the wrapped component
    return <WrappedComponent {...rest} />;
  };
}

// ─── HOC 2: withLogger ───────────────────────────────────────────────────────
// Logs component name and props on every render

function withLogger(WrappedComponent) {
  return function WithLoggerComponent(props) {
    useEffect(() => {
      console.log(`[Logger] ${WrappedComponent.name || "Component"} rendered with:`, props);
    });
    return <WrappedComponent {...props} />;
  };
}

// ─── HOC 3: withAuth ─────────────────────────────────────────────────────────
// Only renders component if user is authenticated

function withAuth(WrappedComponent) {
  return function WithAuthComponent({ isAuthenticated, ...rest }) {
    if (!isAuthenticated) {
      return (
        <div style={{ ...styles.card, background: "#fff3e0" }}>
          Please log in to view this content.
        </div>
      );
    }
    return <WrappedComponent {...rest} />;
  };
}

// ─── Base Components ─────────────────────────────────────────────────────────

function UserList({ users }) {
  return (
    <div>
      {users.map((user) => (
        <div key={user.id} style={styles.card}>
          <strong>{user.name}</strong> — {user.email}
        </div>
      ))}
    </div>
  );
}

function SecretPanel({ message }) {
  return (
    <div style={{ ...styles.card, background: "#e8f5e9" }}>
      <strong>Secret:</strong> {message}
    </div>
  );
}

// ─── Enhanced Components (HOC applied) ───────────────────────────────────────

const UserListWithLoader = withLoader(UserList, "Fetching users...");
const UserListWithLoaderAndLogger = withLogger(withLoader(UserList));  // compose!
const ProtectedPanel = withAuth(SecretPanel);

// ─── Demo ────────────────────────────────────────────────────────────────────

export default function HOCExample() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loggedIn, setLoggedIn] = useState(false);

  // Simulate API fetch
  useEffect(() => {
    setTimeout(() => {
      setUsers([
        { id: 1, name: "Alice", email: "alice@test.com" },
        { id: 2, name: "Bob", email: "bob@test.com" },
      ]);
      setLoading(false);
    }, 2000);
  }, []);

  return (
    <div style={styles.container}>
      <h3>Higher-Order Components</h3>

      {/* HOC 1: withLoader */}
      <div style={styles.section}>
        <h4>withLoader HOC</h4>
        <p>Shows "Fetching users..." for 2 seconds, then renders the list.</p>
        <UserListWithLoader isLoading={loading} users={users} />
      </div>

      {/* HOC 3: withAuth */}
      <div style={styles.section}>
        <h4>withAuth HOC</h4>
        <label>
          <input
            type="checkbox"
            checked={loggedIn}
            onChange={(e) => setLoggedIn(e.target.checked)}
          />{" "}
          Logged in
        </label>
        <ProtectedPanel isAuthenticated={loggedIn} message="The treasure is buried under the old oak tree!" />
      </div>

      {/* HOC Composition */}
      <div style={styles.section}>
        <h4>Composed HOC: withLogger(withLoader(UserList))</h4>
        <p>Check console — logs props on every render.</p>
        <UserListWithLoaderAndLogger isLoading={loading} users={users} />
      </div>
    </div>
  );
}
