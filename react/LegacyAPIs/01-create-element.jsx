import { createElement, useState } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   createElement — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: createElement(type, props, ...children)

   PURPOSE: Create React elements WITHOUT JSX. This is what JSX compiles to.
   Every <div className="x">Hello</div> becomes:
     createElement('div', { className: 'x' }, 'Hello')

   DIAGRAM — JSX → createElement:
   ┌──────────────────────────────────────────────────────────────┐
   │  JSX:                                                       │
   │  <button onClick={fn} className="btn">                      │
   │    <span>Click</span>                                       │
   │  </button>                                                   │
   │                                                              │
   │  Compiled to:                                                │
   │  createElement('button', { onClick: fn, className: 'btn' }, │
   │    createElement('span', null, 'Click')                     │
   │  )                                                           │
   │                                                              │
   │  Returns (React element object):                             │
   │  {                                                           │
   │    $$typeof: Symbol(react.element),                          │
   │    type: 'button',                                           │
   │    props: { onClick: fn, className: 'btn', children: ... }, │
   │    key: null,                                                │
   │    ref: null                                                 │
   │  }                                                           │
   └──────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. JSX is syntactic sugar for createElement — they produce identical output.
   2. The type can be: a string ('div', 'span'), a component (MyComponent),
      or a Fragment (Fragment).
   3. Props is an object or null. Children can be strings, elements, arrays.
   4. key and ref are extracted from props — they appear on the element,
      not in props.children.
   5. createElement is rarely used directly — JSX is preferred for readability.
      Use it when generating elements dynamically.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

/* ─── Example 1: Basic createElement vs JSX ─── */

function BasicExample() {
  // These two are IDENTICAL:
  const jsxVersion = <p style={{ color: "#1a73e8" }}>I was created with JSX</p>;
  const ceVersion = createElement("p", { style: { color: "#34a853" } }, "I was created with createElement");

  return (
    <div style={styles.section}>
      <h3>1. createElement vs JSX (identical output)</h3>
      {jsxVersion}
      {ceVersion}
      <div style={styles.code}>{`// JSX:
<p style={{ color: "blue" }}>Hello</p>

// createElement (what JSX compiles to):
createElement("p", { style: { color: "blue" } }, "Hello")

// Both produce the same React element object.`}</div>
    </div>
  );
}

/* ─── Example 2: Nested Elements ─── */

function NestedExample() {
  const card = createElement(
    "div",
    { style: { border: "1px solid #ccc", borderRadius: 8, padding: 16 } },
    createElement("h4", { style: { margin: "0 0 8px" } }, "Card Title"),
    createElement("p", { style: { color: "#666", margin: 0 } }, "Card content created entirely with createElement."),
    createElement(
      "button",
      {
        style: styles.btn,
        onClick: () => alert("Clicked!"),
      },
      "Click Me"
    )
  );

  return (
    <div style={styles.section}>
      <h3>2. Nested Elements</h3>
      {card}
      <div style={styles.code}>{`createElement("div", { style: {...} },
  createElement("h4", null, "Title"),
  createElement("p", null, "Content"),
  createElement("button", { onClick: fn }, "Click")
)`}</div>
    </div>
  );
}

/* ─── Example 3: Dynamic Element Creation ─── */

function DynamicElements() {
  const [elements, setElements] = useState([
    { tag: "h3", text: "Heading", color: "#1a73e8" },
    { tag: "p", text: "Paragraph", color: "#333" },
    { tag: "em", text: "Italic text", color: "#e65100" },
    { tag: "strong", text: "Bold text", color: "#34a853" },
  ]);

  const [tag, setTag] = useState("p");
  const [text, setText] = useState("");

  const addElement = () => {
    if (!text.trim()) return;
    setElements([...elements, { tag, text, color: "#" + Math.floor(Math.random() * 16777215).toString(16) }]);
    setText("");
  };

  return (
    <div style={styles.section}>
      <h3>3. Dynamic Element Creation</h3>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <select value={tag} onChange={(e) => setTag(e.target.value)} style={{ padding: 6, borderRadius: 4 }}>
          <option value="p">p</option>
          <option value="h4">h4</option>
          <option value="em">em</option>
          <option value="strong">strong</option>
          <option value="code">code</option>
        </select>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Text content..."
          style={{ padding: "6px 10px", border: "1px solid #ccc", borderRadius: 4, flex: 1 }}
          onKeyDown={(e) => e.key === "Enter" && addElement()}
        />
        <button style={styles.btn} onClick={addElement}>Add</button>
      </div>
      <div style={{ borderTop: "1px solid #eee", paddingTop: 8 }}>
        {elements.map((el, i) =>
          // createElement is useful for dynamic tag names!
          createElement(el.tag, { key: i, style: { color: el.color, margin: "4px 0" } }, el.text)
        )}
      </div>
      <div style={styles.code}>{`// Dynamic tags — can't do <{tag}> in JSX
elements.map(el =>
  createElement(el.tag, { style }, el.text)
)`}</div>
    </div>
  );
}

/* ─── Example 4: Element Object Structure ─── */

function ElementStructure() {
  const element = createElement("div", { className: "demo", id: "test" }, "Hello");

  return (
    <div style={styles.section}>
      <h3>4. React Element Object</h3>
      <div style={styles.code}>{`// createElement returns a plain object:
{
  $$typeof: Symbol(react.element),
  type: "${element.type}",
  props: ${JSON.stringify(element.props, null, 4)},
  key: ${String(element.key)},
  ref: ${String(element.ref)}
}

// React reads this object to know WHAT to render.
// It's a description, not the DOM node itself.`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function CreateElementExample() {
  return (
    <div style={styles.container}>
      <h2>createElement (Legacy API)</h2>
      <BasicExample />
      <NestedExample />
      <DynamicElements />
      <ElementStructure />
    </div>
  );
}
