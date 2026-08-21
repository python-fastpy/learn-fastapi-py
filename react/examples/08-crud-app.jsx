import { useState, useEffect, useReducer } from "react";

/*
  CRUD APP (with fake API)
  ────────────────────────
  Flow:
    ┌─────────────────────────────────────────────────┐
    │           CRUD Operations                       │
    │                                                 │
    │  CREATE  →  POST /api/users    → add to list    │
    │  READ    →  GET  /api/users    → show list      │
    │  UPDATE  →  PUT  /api/users/1  → edit in place  │
    │  DELETE  →  DEL  /api/users/1  → remove from list│
    └─────────────────────────────────────────────────┘

  Key concepts:
    - useReducer for complex state (list + loading + error)
    - Fake async API (setTimeout simulates network)
    - Optimistic updates vs server-confirmed updates
    - Edit mode toggle per item
    - Loading/error states
*/

// ─── Fake API (simulates server with 300ms delay) ────────────────────────────

let nextId = 4;
let fakeDB = [
  { id: 1, name: "Alice", email: "alice@test.com" },
  { id: 2, name: "Bob", email: "bob@test.com" },
  { id: 3, name: "Charlie", email: "charlie@test.com" },
];

const fakeApi = {
  getAll: () => delay(() => [...fakeDB]),
  create: (user) => delay(() => {
    const newUser = { ...user, id: nextId++ };
    fakeDB.push(newUser);
    return newUser;
  }),
  update: (id, data) => delay(() => {
    fakeDB = fakeDB.map((u) => (u.id === id ? { ...u, ...data } : u));
    return fakeDB.find((u) => u.id === id);
  }),
  remove: (id) => delay(() => {
    fakeDB = fakeDB.filter((u) => u.id !== id);
    return id;
  }),
};

function delay(fn, ms = 300) {
  return new Promise((resolve) => setTimeout(() => resolve(fn()), ms));
}

// ─── Reducer ─────────────────────────────────────────────────────────────────

const initialState = { users: [], loading: false, error: null };

function reducer(state, action) {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, loading: true, error: null };
    case "SET_USERS":
      return { ...state, users: action.payload, loading: false };
    case "ADD_USER":
      return { ...state, users: [...state.users, action.payload], loading: false };
    case "UPDATE_USER":
      return {
        ...state,
        users: state.users.map((u) => (u.id === action.payload.id ? action.payload : u)),
        loading: false,
      };
    case "DELETE_USER":
      return {
        ...state,
        users: state.users.filter((u) => u.id !== action.payload),
        loading: false,
      };
    case "SET_ERROR":
      return { ...state, error: action.payload, loading: false };
    default:
      return state;
  }
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  form: { display: "flex", gap: 8, marginBottom: 16 },
  input: { padding: "8px 12px", border: "1px solid #ccc", borderRadius: 4, flex: 1 },
  btn: { padding: "8px 16px", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 13 },
  addBtn: { background: "#1a73e8", color: "#fff" },
  editBtn: { background: "#fbbc04", color: "#000" },
  delBtn: { background: "#ea4335", color: "#fff" },
  saveBtn: { background: "#34a853", color: "#fff" },
  cancelBtn: { background: "#ccc", color: "#000" },
  row: { display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: "1px solid #eee" },
  info: { flex: 1 },
  loading: { color: "#999", fontStyle: "italic" },
  error: { color: "red", marginBottom: 8 },
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function CrudApp() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState("");
  const [editEmail, setEditEmail] = useState("");

  // READ — fetch all on mount
  useEffect(() => {
    dispatch({ type: "SET_LOADING" });
    fakeApi.getAll().then((users) => dispatch({ type: "SET_USERS", payload: users }));
  }, []);

  // CREATE
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    dispatch({ type: "SET_LOADING" });
    const newUser = await fakeApi.create({ name, email });
    dispatch({ type: "ADD_USER", payload: newUser });
    setName("");
    setEmail("");
  };

  // UPDATE — start editing
  const startEdit = (user) => {
    setEditingId(user.id);
    setEditName(user.name);
    setEditEmail(user.email);
  };

  // UPDATE — save
  const handleUpdate = async (id) => {
    dispatch({ type: "SET_LOADING" });
    const updated = await fakeApi.update(id, { name: editName, email: editEmail });
    dispatch({ type: "UPDATE_USER", payload: updated });
    setEditingId(null);
  };

  // DELETE
  const handleDelete = async (id) => {
    dispatch({ type: "SET_LOADING" });
    await fakeApi.remove(id);
    dispatch({ type: "DELETE_USER", payload: id });
  };

  return (
    <div style={styles.container}>
      <h3>CRUD App (Users)</h3>

      {state.error && <div style={styles.error}>{state.error}</div>}

      {/* CREATE form */}
      <form style={styles.form} onSubmit={handleCreate}>
        <input style={styles.input} placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        <input style={styles.input} placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button style={{ ...styles.btn, ...styles.addBtn }} type="submit">Add</button>
      </form>

      {state.loading && <div style={styles.loading}>Loading...</div>}

      {/* READ list */}
      {state.users.map((user) => (
        <div key={user.id} style={styles.row}>
          {editingId === user.id ? (
            // EDIT mode
            <>
              <input style={styles.input} value={editName} onChange={(e) => setEditName(e.target.value)} />
              <input style={styles.input} value={editEmail} onChange={(e) => setEditEmail(e.target.value)} />
              <button style={{ ...styles.btn, ...styles.saveBtn }} onClick={() => handleUpdate(user.id)}>Save</button>
              <button style={{ ...styles.btn, ...styles.cancelBtn }} onClick={() => setEditingId(null)}>Cancel</button>
            </>
          ) : (
            // VIEW mode
            <>
              <div style={styles.info}>
                <strong>{user.name}</strong> — {user.email}
              </div>
              <button style={{ ...styles.btn, ...styles.editBtn }} onClick={() => startEdit(user)}>Edit</button>
              <button style={{ ...styles.btn, ...styles.delBtn }} onClick={() => handleDelete(user.id)}>Del</button>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
