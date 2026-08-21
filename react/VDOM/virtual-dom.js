/* ═══════════════════════════════════════════════════════════════════════════════
   VIRTUAL DOM — HOW REACT WORKS INTERNALLY (Simplified)
   ═══════════════════════════════════════════════════════════════════════════════

   This file mimics React's core Virtual DOM mechanism in plain JavaScript.
   Run it with: node virtual-dom.js

   ARCHITECTURE:
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  1. createElement(type, props, ...children)                              │
   │     → Creates a virtual node (JS object describing the UI)               │
   │                                                                          │
   │  2. render(vNode, container)                                             │
   │     → Converts virtual nodes into REAL DOM nodes                         │
   │                                                                          │
   │  3. diff(oldVNode, newVNode)                                             │
   │     → Compares two virtual trees, produces a list of patches             │
   │                                                                          │
   │  4. patch(dom, patches)                                                  │
   │     → Applies only the minimum changes to the real DOM                   │
   └────────────────────────────────────────────────────────────────────────────┘

   WHY VIRTUAL DOM:
   ┌──────────────────────────────────────────────────────┐
   │  Direct DOM manipulation:                            │
   │    Change 1 → DOM update → reflow → repaint          │
   │    Change 2 → DOM update → reflow → repaint          │
   │    Change 3 → DOM update → reflow → repaint          │
   │    = 3 costly reflows!                                │
   │                                                      │
   │  Virtual DOM approach:                               │
   │    Change 1, 2, 3 → diff virtual trees               │
   │    → batch minimal DOM updates → 1 reflow             │
   └──────────────────────────────────────────────────────┘

   RECONCILIATION (Diffing Algorithm):
   ┌──────────────────────────────────────────────────────┐
   │  Rule 1: Different TYPE → tear down old, build new   │
   │    <div> → <span> = destroy div, create span         │
   │                                                      │
   │  Rule 2: Same TYPE → update props/attributes only    │
   │    <div class="a"> → <div class="b"> = just update   │
   │                                                      │
   │  Rule 3: Lists use KEY for efficient reordering      │
   │    Without key: re-render all items                   │
   │    With key: move, add, remove only what changed     │
   └──────────────────────────────────────────────────────┘
   ═══════════════════════════════════════════════════════════════════════════════ */

// ─────────────────────────────────────────────────────────────
// STEP 1: createElement — Build virtual nodes
// ─────────────────────────────────────────────────────────────

function createElement(type, props = {}, ...children) {
  return {
    type,
    props: props || {},
    children: children
      .flat()
      .map((child) =>
        typeof child === "object" ? child : createTextElement(String(child))
      ),
  };
}

function createTextElement(text) {
  return {
    type: "TEXT",
    props: {},
    children: [],
    text,
  };
}

// ─────────────────────────────────────────────────────────────
// STEP 2: render — Convert virtual nodes to real DOM
// ─────────────────────────────────────────────────────────────

function render(vNode) {
  // Text node
  if (vNode.type === "TEXT") {
    return document.createTextNode(vNode.text);
  }

  // Element node
  const el = document.createElement(vNode.type);

  // Set props/attributes
  for (const [key, value] of Object.entries(vNode.props)) {
    if (key.startsWith("on")) {
      // Event listener: onClick → click
      el.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key === "style" && typeof value === "object") {
      Object.assign(el.style, value);
    } else if (key === "className") {
      el.className = value;
    } else {
      el.setAttribute(key, value);
    }
  }

  // Recursively render children
  for (const child of vNode.children) {
    el.appendChild(render(child));
  }

  return el;
}

// ─────────────────────────────────────────────────────────────
// STEP 3: diff — Compare two virtual trees
// ─────────────────────────────────────────────────────────────

const PATCH_TYPES = {
  CREATE: "CREATE",
  REMOVE: "REMOVE",
  REPLACE: "REPLACE",
  UPDATE_PROPS: "UPDATE_PROPS",
  UPDATE_TEXT: "UPDATE_TEXT",
};

function diff(oldNode, newNode, index = 0) {
  const patches = [];

  // New node doesn't exist → remove old
  if (!newNode) {
    patches.push({ type: PATCH_TYPES.REMOVE, index });
    return patches;
  }

  // Old node doesn't exist → create new
  if (!oldNode) {
    patches.push({ type: PATCH_TYPES.CREATE, newNode, index });
    return patches;
  }

  // Different types → replace entirely (Rule 1)
  if (oldNode.type !== newNode.type) {
    patches.push({ type: PATCH_TYPES.REPLACE, newNode, index });
    return patches;
  }

  // Both are text nodes → check if text changed
  if (oldNode.type === "TEXT") {
    if (oldNode.text !== newNode.text) {
      patches.push({ type: PATCH_TYPES.UPDATE_TEXT, newText: newNode.text, index });
    }
    return patches;
  }

  // Same type → diff props (Rule 2)
  const propPatches = diffProps(oldNode.props, newNode.props);
  if (propPatches.length > 0) {
    patches.push({ type: PATCH_TYPES.UPDATE_PROPS, propPatches, index });
  }

  // Diff children recursively
  const maxLen = Math.max(oldNode.children.length, newNode.children.length);
  for (let i = 0; i < maxLen; i++) {
    const childPatches = diff(
      oldNode.children[i],
      newNode.children[i],
      i
    );
    patches.push(
      ...childPatches.map((p) => ({ ...p, path: [index, ...(p.path || [])] }))
    );
  }

  return patches;
}

function diffProps(oldProps, newProps) {
  const patches = [];
  const allKeys = new Set([...Object.keys(oldProps), ...Object.keys(newProps)]);

  for (const key of allKeys) {
    if (key.startsWith("on")) continue; // Skip events for simplicity

    if (!(key in newProps)) {
      patches.push({ op: "remove", key });
    } else if (!(key in oldProps) || oldProps[key] !== newProps[key]) {
      patches.push({ op: "set", key, value: newProps[key] });
    }
  }

  return patches;
}

// ─────────────────────────────────────────────────────────────
// STEP 4: patch — Apply changes to real DOM
// ─────────────────────────────────────────────────────────────

function applyPatch(parent, domNode, patchItem) {
  switch (patchItem.type) {
    case PATCH_TYPES.CREATE: {
      const newEl = render(patchItem.newNode);
      parent.appendChild(newEl);
      return newEl;
    }
    case PATCH_TYPES.REMOVE: {
      if (domNode) parent.removeChild(domNode);
      return null;
    }
    case PATCH_TYPES.REPLACE: {
      const newEl = render(patchItem.newNode);
      if (domNode) {
        parent.replaceChild(newEl, domNode);
      } else {
        parent.appendChild(newEl);
      }
      return newEl;
    }
    case PATCH_TYPES.UPDATE_TEXT: {
      if (domNode) domNode.textContent = patchItem.newText;
      return domNode;
    }
    case PATCH_TYPES.UPDATE_PROPS: {
      if (!domNode) return domNode;
      for (const p of patchItem.propPatches) {
        if (p.op === "remove") {
          domNode.removeAttribute(p.key);
        } else if (p.key === "className") {
          domNode.className = p.value;
        } else if (p.key === "style" && typeof p.value === "object") {
          Object.assign(domNode.style, p.value);
        } else {
          domNode.setAttribute(p.key, p.value);
        }
      }
      return domNode;
    }
    default:
      return domNode;
  }
}

// ─────────────────────────────────────────────────────────────
// DEMO — Run this in Node.js to see the diff output
// ─────────────────────────────────────────────────────────────

function demo() {
  console.log("═══════════════════════════════════════════");
  console.log("  VIRTUAL DOM DEMO");
  console.log("═══════════════════════════════════════════\n");

  // Initial virtual tree
  const oldTree = createElement(
    "div",
    { className: "container" },
    createElement("h1", { style: "color: blue" }, "Hello World"),
    createElement(
      "ul",
      {},
      createElement("li", { className: "item" }, "Item 1"),
      createElement("li", { className: "item" }, "Item 2"),
      createElement("li", { className: "item" }, "Item 3")
    ),
    createElement("p", {}, "Footer text")
  );

  console.log("1. OLD Virtual Tree:");
  console.log(JSON.stringify(oldTree, null, 2).slice(0, 500) + "...\n");

  // Updated virtual tree (simulating state change)
  const newTree = createElement(
    "div",
    { className: "container updated" }, // Changed: class updated
    createElement("h1", { style: "color: red" }, "Hello React!"), // Changed: color + text
    createElement(
      "ul",
      {},
      createElement("li", { className: "item" }, "Item 1"), // Same
      createElement("li", { className: "item active" }, "Item 2 (updated)"), // Changed
      createElement("li", { className: "item" }, "Item 3"), // Same
      createElement("li", { className: "item new" }, "Item 4") // Added
    )
    // Removed: <p> Footer text
  );

  console.log("2. NEW Virtual Tree (after state change):");
  console.log("   - div className: 'container' → 'container updated'");
  console.log("   - h1 color: blue → red, text: 'Hello World' → 'Hello React!'");
  console.log("   - li[1] class updated, text updated");
  console.log("   - li[3] added (Item 4)");
  console.log("   - <p> removed\n");

  // Diff the trees
  const patches = diff(oldTree, newTree);

  console.log("3. DIFF RESULT (patches to apply):");
  console.log(`   ${patches.length} patches found:\n`);

  patches.forEach((p, i) => {
    const location = p.path ? `path=[${p.path.join(",")}]` : `index=${p.index}`;
    switch (p.type) {
      case PATCH_TYPES.UPDATE_PROPS:
        console.log(`   [${i}] UPDATE_PROPS at ${location}`);
        p.propPatches.forEach((pp) => console.log(`        ${pp.op}: ${pp.key} = ${pp.value}`));
        break;
      case PATCH_TYPES.UPDATE_TEXT:
        console.log(`   [${i}] UPDATE_TEXT at ${location}: "${p.newText}"`);
        break;
      case PATCH_TYPES.CREATE:
        console.log(`   [${i}] CREATE at ${location}: <${p.newNode.type}>`);
        break;
      case PATCH_TYPES.REMOVE:
        console.log(`   [${i}] REMOVE at ${location}`);
        break;
      case PATCH_TYPES.REPLACE:
        console.log(`   [${i}] REPLACE at ${location}: → <${p.newNode.type}>`);
        break;
      default:
        console.log(`   [${i}] ${p.type} at ${location}`);
    }
  });

  console.log("\n4. KEY TAKEAWAYS:");
  console.log("   ✓ Only changed parts produce patches (not the entire tree)");
  console.log("   ✓ Same-type elements update props in place (no recreation)");
  console.log("   ✓ Different-type elements are fully replaced");
  console.log("   ✓ Patches are batched and applied in a single DOM update pass");
  console.log("   ✓ This is why React is efficient — minimal DOM manipulation");

  console.log("\n═══════════════════════════════════════════");
  console.log("  END DEMO");
  console.log("═══════════════════════════════════════════");
}

demo();

/* ═══════════════════════════════════════════════════════════════════════════════
   EXPECTED OUTPUT:
   ═══════════════════════════════════════════════════════════════════════════════

   1. OLD Virtual Tree:
   { "type": "div", "props": { "className": "container" }, "children": [...] }

   2. NEW Virtual Tree (after state change):
      - div className: 'container' → 'container updated'
      - h1 color: blue → red, text: 'Hello World' → 'Hello React!'
      - li[1] class updated, text updated
      - li[3] added (Item 4)
      - <p> removed

   3. DIFF RESULT:
      Several patches found showing UPDATE_PROPS, UPDATE_TEXT, CREATE, REMOVE

   4. KEY TAKEAWAYS:
      ✓ Only changed parts produce patches
      ✓ Same-type elements update in place
      ✓ Different-type elements fully replaced
      ✓ Batched DOM updates
   ═══════════════════════════════════════════════════════════════════════════════ */

// Export for use as a module (optional)
if (typeof module !== "undefined") {
  module.exports = { createElement, render, diff, applyPatch };
}
