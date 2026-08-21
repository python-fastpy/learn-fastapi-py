import { useState } from "react";
import { createPortal } from "react-dom";

/* ═══════════════════════════════════════════════════════════════════
   createPortal — Render children into a different DOM node while keeping them in the React tree.
   ┌─────── DOM Tree ────────┐  ┌───── React Tree ─────┐
   │ <div id="root">         │  │ <App>                 │
   │   <App><Parent/></App>  │  │   <Parent>            │
   │ </div>                  │  │     <Modal> (here!)   │
   │ <div id="modal-root">   │  │   </Parent>           │
   │   <Modal/> (here!)      │  │ </App>                │
   │ </div>                  │  └───────────────────────┘
   └─────────────────────────┘
   1. Event bubbling follows the REACT tree, not the DOM tree.
   2. Context flows through React tree — portals access React parent's context.
   3. Escapes overflow:hidden, z-index stacking, and transform contexts.
   4. Target domNode must already exist when createPortal is called.
   5. Portals require a real DOM node — no SSR support.
   ═══════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  overlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 },
  modal: { background: "#fff", padding: 24, borderRadius: 12, minWidth: 300, maxWidth: 400, boxShadow: "0 8px 32px rgba(0,0,0,0.3)" },
};

/* ─── Example 1: Modal Portal ─── */

function Modal({ children, onClose }) {
  return createPortal(
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {children}
        <button style={{ ...styles.btn, background: "#ea4335", marginTop: 12 }} onClick={onClose}>Close</button>
      </div>
    </div>,
    document.body
  );
}

function ModalExample() {
  const [show, setShow] = useState(false);

  return (
    <div style={styles.section}>
      <h3>1. Modal Portal</h3>
      <div style={{ overflow: "hidden", border: "2px dashed #ccc", padding: 16, borderRadius: 8 }}>
        <p>This container has <code>overflow: hidden</code>.</p>
        <p>Without portal, a modal here would be clipped.</p>
        <button style={styles.btn} onClick={() => setShow(true)}>Open Modal</button>
        {show && (
          <Modal onClose={() => setShow(false)}>
            <h3 style={{ margin: "0 0 8px" }}>Portal Modal</h3>
            <p>I render in document.body, escaping the overflow:hidden container.</p>
          </Modal>
        )}
      </div>
    </div>
  );
}

/* ─── Example 2: Event Bubbling Through React Tree ─── */

function EventBubblingExample() {
  const [logs, setLogs] = useState([]);
  const [showPortal, setShowPortal] = useState(false);

  const addLog = (msg) => setLogs((prev) => [...prev.slice(-4), msg]);

  return (
    <div style={styles.section}>
      <h3>2. Event Bubbling Follows React Tree</h3>
      <div onClick={() => addLog("Clicked on REACT parent div (bubbled up!)")}>
        <p style={{ fontSize: 12, color: "#999" }}>Click events inside the portal bubble to this React parent, even though the DOM nodes are separate.</p>
        <button style={styles.btn} onClick={(e) => { e.stopPropagation(); setShowPortal(!showPortal); }}>
          {showPortal ? "Hide" : "Show"} Portal
        </button>
        {showPortal && createPortal(
          <div
            style={{ position: "fixed", bottom: 20, right: 20, background: "#1a73e8", color: "#fff", padding: 16, borderRadius: 8, zIndex: 1000, cursor: "pointer" }}
            onClick={() => addLog("Clicked INSIDE portal (will bubble to React parent)")}
          >
            I'm a portal! Click me.
          </div>,
          document.body
        )}
      </div>
      <div style={{ background: "#f5f5f5", padding: 8, borderRadius: 4, marginTop: 8, minHeight: 40 }}>
        {logs.map((l, i) => <div key={i} style={{ fontSize: 12 }}>{l}</div>)}
      </div>
    </div>
  );
}

/* ─── Example 3: Tooltip Portal ─── */

function Tooltip({ children, text, show }) {
  if (!show) return children;

  return (
    <span style={{ position: "relative", display: "inline-block" }}>
      {children}
      {createPortal(
        <div style={{ position: "fixed", top: "50%", left: "50%", transform: "translate(-50%, -50%)", background: "#333", color: "#fff", padding: "8px 16px", borderRadius: 6, fontSize: 13, zIndex: 9999, pointerEvents: "none" }}>
          {text}
        </div>,
        document.body
      )}
    </span>
  );
}

function TooltipExample() {
  const [hover, setHover] = useState(false);

  return (
    <div style={styles.section}>
      <h3>3. Tooltip Portal</h3>
      <div style={{ overflow: "hidden", border: "2px dashed #ccc", padding: 16, borderRadius: 8, height: 60 }}>
        <Tooltip text="I escape overflow:hidden via portal!" show={hover}>
          <button
            style={styles.btn}
            onMouseEnter={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
          >
            Hover me
          </button>
        </Tooltip>
        <p style={{ fontSize: 12, color: "#999" }}>Container has overflow:hidden</p>
      </div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function CreatePortalExample() {
  return (
    <div style={styles.container}>
      <h2>createPortal</h2>
      <ModalExample />
      <EventBubblingExample />
      <TooltipExample />
    </div>
  );
}
