// ============================================================
//  DOM API  --  ULTIMATE QUICK-REFERENCE
// ============================================================
//  Organized:  Basic  ->  Intermediate  ->  Advanced
//  Legend:     [BASIC]  [INTERMEDIATE]  [ADVANCED]
//  Source:     https://www.youtube.com/watch?v=rhvec8cXLlo
// ============================================================


// ************************************************************
//                     B A S I C
// ************************************************************


// ============================================================
// 1. DOM TREE STRUCTURE                              [BASIC]
// ============================================================
//
//  ASCII DOM tree for <html> below:
//
//         document
//            |
//          <html>
//          /    \
//      <head>  <body>
//        |      /   \
//     <title> <div> <script>
//               |
//             <p>
//              |
//          "Hello"          <-- Text node
//
//  INTERVIEW: "What is the difference between a node and an element?"
//  - Node:    anything in the tree (element, text, comment, document)
//  - Element: only HTML tags (<div>, <p>, etc.)  --  a subset of Node
//
//  Key node types (node.nodeType):
//    1 = ELEMENT_NODE      (<div>)
//    3 = TEXT_NODE          ("Hello")
//    8 = COMMENT_NODE      (<!-- ... -->)
//    9 = DOCUMENT_NODE     (document)


// ============================================================
// 2. PAGE LIFECYCLE EVENTS                           [BASIC]
// ============================================================
//
//  Timeline:
//    HTML parsing starts
//      |
//      v
//   [ DOMContentLoaded ]   -- DOM tree ready, images/CSS may still load
//      |
//      v
//   [      load         ]  -- everything loaded (images, stylesheets)
//      :
//      : (user navigates away)
//      v
//   [ beforeunload      ]  -- chance to show "unsaved changes?" dialog
//      |
//      v
//   [   unload          ]  -- page fully unloaded, send analytics
//

// DOMContentLoaded -- DOM ready, external resources may still load
document.addEventListener("DOMContentLoaded", () => {
  console.log("DOM tree built -- safe to query elements");
});

// load -- everything (images, stylesheets, iframes) finished loading
window.addEventListener("load", () => {
  console.log("All resources loaded");
});

// beforeunload -- prompt user before leaving (prevent data loss)
window.addEventListener("beforeunload", (e) => {
  e.preventDefault();       // required by spec
  e.returnValue = "";       // Chrome requires this
});

// unload -- final cleanup / analytics beacon
window.addEventListener("unload", () => {
  navigator.sendBeacon("/analytics", JSON.stringify({ left: Date.now() }));
});

// GOTCHAS -- Page Lifecycle
// - DOMContentLoaded fires on "document", NOT on "window".
// - <script> without defer/async BLOCKS DOMContentLoaded.
// - "unload" is unreliable on mobile -- prefer "visibilitychange".
// - navigator.sendBeacon() is the only reliable way to send data in unload.
// - beforeunload dialog text is browser-controlled; custom text is ignored.


// ============================================================
// 3. LOCAL STORAGE & SESSION STORAGE                 [BASIC]
// ============================================================
// INTERVIEW: "Difference between localStorage and sessionStorage?"
//
//  +------------------+-----------------+---------------------+
//  |                  | localStorage    | sessionStorage      |
//  +------------------+-----------------+---------------------+
//  | Lifetime         | Until cleared   | Until tab closes    |
//  | Scope            | Same origin     | Same origin + tab   |
//  | Size limit       | ~5-10 MB        | ~5-10 MB            |
//  | Shared across    | All tabs        | Single tab only     |
//  | Survives refresh | Yes             | Yes                 |
//  +------------------+-----------------+---------------------+

// Set, get, remove
localStorage.setItem("theme", "dark");
const theme = localStorage.getItem("theme");   // "dark"
localStorage.removeItem("theme");
localStorage.clear();                           // remove all

// Storing objects (must serialize)
const user = { name: "Alice", role: "editor" };
localStorage.setItem("user", JSON.stringify(user));
const stored = JSON.parse(localStorage.getItem("user"));

// Listen for cross-tab changes
window.addEventListener("storage", (e) => {
  console.log(e.key, e.oldValue, "->", e.newValue);
});

// GOTCHAS -- Storage
// - Values are ALWAYS strings; forgetting JSON.parse/stringify is common.
// - The "storage" event fires only in OTHER tabs, not the tab that changed it.
// - Exceeding quota throws a QuotaExceededError -- always wrap setItem in try/catch.
// - Private/incognito mode may limit or disable storage entirely.
// - Never store sensitive data (tokens, passwords) in localStorage.


// ============================================================
// 4. CUSTOM EVENTS                                   [BASIC]
// ============================================================

// --- Basic Event (no payload) ---
const myEvent = new Event("myCustomEvent", {
  bubbles: true,
  cancelable: true,
  composed: true,       // crosses shadow DOM boundary
});

document.addEventListener("myCustomEvent", (e) => console.log("fired:", e.type));
document.dispatchEvent(myEvent);

// --- CustomEvent (with payload via "detail") ---
const dataEvent = new CustomEvent("custom::event", {
  bubbles: true,
  detail: { user: "shubham", role: "dev" },
});

document.addEventListener("custom::event", (e) => {
  console.log(e.detail.user);   // "shubham"
});
document.dispatchEvent(dataEvent);

// INTERVIEW: "When would you use CustomEvent over Event?"
// Use CustomEvent when you need to pass data via `detail`.
// Event has no `detail` property.

// GOTCHAS -- Custom Events
// - CustomEvent.detail is READ-ONLY after creation.
// - If bubbles is false (default), parent listeners will NOT hear it.
// - "composed: true" is only relevant inside Shadow DOM.


// ************************************************************
//            I N T E R M E D I A T E
// ************************************************************


// ============================================================
// 5. EVENT BUBBLING vs CAPTURING                     [INTERMEDIATE]
// ============================================================
//
//  INTERVIEW: "Explain event propagation phases."
//
//  Three phases when an event fires on <span>:
//
//        CAPTURING (1)           TARGET (2)          BUBBLING (3)
//
//        window     |                                  ^  window
//        document   |                                  |  document
//        <html>     |                                  |  <html>
//        <body>     |                                  |  <body>
//        <div>      |                                  |  <div>
//        <p>        v                                  |  <p>
//                   +---->  [ <span>  TARGET ]  -------+
//
//  Phase 1 (Capture): window -> document -> html -> body -> div -> p -> span
//  Phase 2 (Target):  event reaches the target element
//  Phase 3 (Bubble):  span -> p -> div -> body -> html -> document -> window
//

const parent2 = document.getElementById("parent");
const child = document.getElementById("child");

// Bubbling (default) -- fires bottom-up
parent2.addEventListener("click", () => console.log("parent (bubble)"));
child.addEventListener("click", () => console.log("child (bubble)"));
// Click child -> "child (bubble)" then "parent (bubble)"

// Capturing -- fires top-down
parent2.addEventListener("click", () => console.log("parent (capture)"), true);
// OR: { capture: true }

// ---- addEventListener options comparison ----
//  +---------------------+------------------------------------------+
//  | Option              | Purpose                                  |
//  +---------------------+------------------------------------------+
//  | capture: true       | Listen during capture phase (top-down)   |
//  | once: true          | Auto-remove after first invocation       |
//  | passive: true       | Promise not to call preventDefault()     |
//  |                     |   (improves scroll/touch performance)    |
//  | signal: controller  | AbortSignal to remove listener later     |
//  +---------------------+------------------------------------------+

// Using AbortController to remove listeners
const controller = new AbortController();
document.addEventListener("click", handleClick, { signal: controller.signal });
controller.abort();   // removes the listener


// ============================================================
// 6. stopPropagation vs stopImmediatePropagation     [INTERMEDIATE]
// ============================================================
//
//  INTERVIEW: "What is the difference?"
//
//  +-------------------------------+-----------------------------------+
//  | stopPropagation()             | stopImmediatePropagation()        |
//  +-------------------------------+-----------------------------------+
//  | Stops event from reaching     | Same, PLUS stops other listeners  |
//  | ancestors/descendants         | on the SAME element from firing   |
//  +-------------------------------+-----------------------------------+

const btn = document.getElementById("btn");

btn.addEventListener("click", (e) => {
  console.log("Handler 1");
  e.stopImmediatePropagation();   // Handler 2 will NOT run
});

btn.addEventListener("click", () => {
  console.log("Handler 2");      // never reached
});

// GOTCHAS -- Propagation
// - stopPropagation() does NOT prevent default browser behavior; use preventDefault().
// - stopImmediatePropagation() also stops propagation (it is a superset).
// - Overusing stopPropagation breaks event delegation -- avoid it when possible.


// ============================================================
// 7. EVENT DELEGATION                                [INTERMEDIATE]
// ============================================================
//
//  INTERVIEW: "Explain event delegation and why it matters."
//
//  Pattern: attach ONE listener to a common ancestor instead of
//  individual listeners on every child.  Uses event bubbling.
//
//  Benefits:
//   - Fewer listeners = less memory
//   - Works for dynamically added elements
//   - Cleaner code

// BAD -- one listener per button
document.querySelectorAll(".item").forEach((item) => {
  item.addEventListener("click", handleItem);
});

// GOOD -- delegate to parent
document.getElementById("list").addEventListener("click", (e) => {
  const item = e.target.closest(".item");   // find nearest .item ancestor
  if (!item) return;                        // click was not on an item
  console.log("Clicked:", item.dataset.id);
});

// INTERVIEW: "Why use closest() instead of checking e.target directly?"
// Because e.target might be a child element INSIDE .item (e.g., a <span>).
// closest() walks up the DOM and finds the matching ancestor.

// GOTCHAS -- Event Delegation
// - Does NOT work for events that do not bubble (focus, blur, scroll).
//   Use focusin/focusout instead of focus/blur for delegation.
// - closest() returns null if no match -- always null-check.
// - Be careful with deeply nested clickable areas; you may need to
//   distinguish between the delegate target and inner interactive elements.


// ============================================================
// 8. HISTORY API                                     [INTERMEDIATE]
// ============================================================
// INTERVIEW: "How do SPAs handle navigation without full page reloads?"
//
// The History API lets you manipulate the browser history stack.

// Push a new entry (URL changes, no page reload)
history.pushState({ page: 2 }, "", "/page-2");

// Replace current entry (no new history entry)
history.replaceState({ page: 2 }, "", "/page-2-updated");

// Go back/forward
history.back();
history.forward();
history.go(-2);   // go back 2 entries

// Listen for back/forward navigation
window.addEventListener("popstate", (e) => {
  console.log("User navigated, state:", e.state);
});

// GOTCHAS -- History API
// - pushState does NOT fire "popstate". Only browser back/forward does.
// - The second argument (title) is ignored by most browsers -- pass "".
// - URL must be same-origin; cross-origin throws a SecurityError.
// - Refreshing a pushState URL requires server-side routing support.


// ============================================================
// 9. requestAnimationFrame                           [INTERMEDIATE]
// ============================================================
// INTERVIEW: "Why use rAF instead of setInterval for animations?"
//
// rAF syncs with the browser's repaint cycle (~60fps).
// setInterval can cause jank and wasted frames.

let start = null;
function animate(timestamp) {
  if (!start) start = timestamp;
  const elapsed = timestamp - start;

  const element = document.getElementById("box");
  element.style.transform = `translateX(${Math.min(elapsed / 2, 300)}px)`;

  if (elapsed < 600) {
    requestAnimationFrame(animate);   // schedule next frame
  }
}
const rafId = requestAnimationFrame(animate);

// Cancel animation
cancelAnimationFrame(rafId);

// GOTCHAS -- requestAnimationFrame
// - rAF is paused when the tab is in the background (saves CPU).
// - It fires BEFORE the browser paints, not after.
// - Always use the timestamp parameter, NOT Date.now(), for smooth animation.
// - rAF runs once per call; you must call it again inside the callback to loop.


// ************************************************************
//              A D V A N C E D
// ************************************************************


// ============================================================
// 10. MUTATION OBSERVER                              [ADVANCED]
// ============================================================
//
//  INTERVIEW: "How do you watch for DOM changes without polling?"
//
//  MutationObserver fires a callback when the observed DOM subtree changes.
//  It replaces the deprecated Mutation Events (e.g., DOMSubtreeModified).

const mutationObserver = new MutationObserver((entries) => {
  entries.forEach((mutation) => {
    console.log(mutation.type, mutation.target);
  });
});

const observedParent = document.querySelector(".parent");

// --- Watch child additions/removals ---
mutationObserver.observe(observedParent, { childList: true });
// observedParent.childNodes[1].remove();   // triggers callback

// --- Watch attribute changes ---
mutationObserver.observe(observedParent, {
  attributes: true,
  attributeOldValue: true,
  attributeFilter: ["class", "id"],   // optional: limit to specific attrs
});
// observedParent.id = "shubham";   // triggers callback

// --- Watch text content changes ---
mutationObserver.observe(observedParent.childNodes[1].childNodes[0], {
  characterData: true,
  characterDataOldValue: true,
});

// --- Watch entire subtree ---
mutationObserver.observe(observedParent, {
  subtree: true,
  childList: true,
  attributes: true,
  characterData: true,
});

// Stop observing
mutationObserver.disconnect();

// Get pending records (before next callback)
const pending = mutationObserver.takeRecords();

// ---- MutationObserver options comparison ----
//  +-------------------------+------------------------------------------+
//  | Option                  | What it watches                          |
//  +-------------------------+------------------------------------------+
//  | childList               | Direct children added/removed            |
//  | attributes              | Attribute value changes                  |
//  | characterData           | Text node content changes                |
//  | subtree                 | Apply above options to entire subtree    |
//  | attributeOldValue       | Record previous attribute value          |
//  | characterDataOldValue   | Record previous text content             |
//  | attributeFilter: [...]  | Only watch listed attributes             |
//  +-------------------------+------------------------------------------+

// GOTCHAS -- MutationObserver
// - Callback is async (microtask); mutations are batched, not instant.
// - "subtree: true" alone does nothing; pair it with childList/attributes/characterData.
// - Observing a massive subtree can impact performance -- scope it narrowly.
// - disconnect() stops ALL observations for that observer instance.
// - If you need the old value, you MUST set attributeOldValue / characterDataOldValue.


// ============================================================
// 11. INTERSECTION OBSERVER                          [ADVANCED]
// ============================================================
//
//  INTERVIEW: "How would you implement lazy loading or infinite scroll?"
//
//  IntersectionObserver fires when an element enters/exits the viewport
//  (or any scrollable ancestor).  No scroll-event polling needed.
//
//  Common use cases: lazy-load images, infinite scroll, ad viewability,
//  "read more" tracking, scroll-triggered animations.

const lazyImages = document.querySelectorAll("img[data-src]");

const imageObserver = new IntersectionObserver(
  (entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;

      const img = entry.target;
      img.src = img.dataset.src;      // swap in the real image
      img.removeAttribute("data-src");
      observer.unobserve(img);         // stop watching this image
    });
  },
  {
    root: null,            // null = viewport (default)
    rootMargin: "200px",   // start loading 200px before visible
    threshold: 0,          // fire as soon as 1px is visible
  }
);

lazyImages.forEach((img) => imageObserver.observe(img));

// ---- threshold examples ----
// threshold: 0        -> fires when 1px enters viewport
// threshold: 0.5      -> fires when 50% visible
// threshold: 1.0      -> fires when 100% visible
// threshold: [0, 0.5, 1]  -> fires at each step

// GOTCHAS -- IntersectionObserver
// - The callback fires once immediately when observe() is called (initial state).
// - rootMargin only works with root: null (viewport) or a scrollable ancestor.
// - rootMargin uses CSS-like syntax: "10px 20px 30px 40px" (top right bottom left).
// - If the observed element has display: none, it is always "not intersecting".
// - threshold: 1.0 never fires if the element is larger than the viewport.


// ============================================================
// 12. RESIZE OBSERVER                                [ADVANCED]
// ============================================================
//
//  INTERVIEW: "How to respond to element size changes without window.resize?"
//
//  ResizeObserver fires when an element's dimensions change.
//  Unlike window "resize", it works on ANY element, not just the window.

const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    const { width, height } = entry.contentRect;
    console.log(`Resized: ${width} x ${height}`);

    // entry.borderBoxSize   -- includes padding + border
    // entry.contentBoxSize  -- content area only
  }
});

const sidebar = document.getElementById("sidebar");
resizeObserver.observe(sidebar);
// resizeObserver.unobserve(sidebar);
// resizeObserver.disconnect();

// ---- Observer types comparison ----
//  +-----------------------+----------------------------+--------------------+
//  | Observer              | Watches                    | Use case           |
//  +-----------------------+----------------------------+--------------------+
//  | MutationObserver      | DOM structure/attributes   | DOM change react   |
//  | IntersectionObserver  | Visibility in viewport     | Lazy load, scroll  |
//  | ResizeObserver        | Element size changes       | Responsive layout  |
//  | PerformanceObserver   | Performance entries        | Metrics / RUM      |
//  +-----------------------+----------------------------+--------------------+

// GOTCHAS -- ResizeObserver
// - Fires on initial observe() call (reports current size).
// - Avoid resizing the observed element inside the callback (infinite loop risk).
// - contentRect is deprecated in favor of borderBoxSize / contentBoxSize arrays.
// - Not triggered by scrollbar appearance alone.


// ============================================================
// 13. PERFORMANCE OBSERVER                           [ADVANCED]
// ============================================================
//
//  INTERVIEW: "How do you measure Core Web Vitals in JavaScript?"
//
//  PerformanceObserver asynchronously receives performance entries
//  (paint timing, largest contentful paint, layout shifts, etc.).

const perfObserver = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log(entry.name, entry.startTime, entry.duration);
  }
});

// Watch for specific entry types
perfObserver.observe({ type: "largest-contentful-paint", buffered: true });
// Other types: "paint", "layout-shift", "longtask", "resource",
//              "navigation", "first-input", "event", "mark", "measure"

// Custom marks and measures
performance.mark("myStart");
// ... expensive operation ...
performance.mark("myEnd");
performance.measure("myOperation", "myStart", "myEnd");

// GOTCHAS -- PerformanceObserver
// - "buffered: true" replays entries that fired BEFORE the observer was created.
// - Some entry types (e.g., "longtask") have limited browser support.
// - PerformanceObserver does NOT observe DOM mutations (that is MutationObserver).


// ============================================================
// 14. WEB WORKERS                                    [ADVANCED]
// ============================================================
//
//  INTERVIEW: "How do you run heavy computation without blocking the UI?"
//
//  Web Workers run JS in a background thread.  They communicate with the
//  main thread via postMessage / onmessage.
//
//       Main Thread                 Worker Thread
//      +------------+    message    +------------+
//      |   UI code  | -----------> | heavy work |
//      |            | <----------- |            |
//      +------------+    message    +------------+
//
//  Workers CANNOT access: DOM, window, document, localStorage.
//  Workers CAN access:    fetch, IndexedDB, WebSocket, setTimeout.

// --- main.js ---
const worker = new Worker("worker.js");

worker.postMessage({ numbers: [1, 2, 3, 4, 5] });

worker.onmessage = (e) => {
  console.log("Result from worker:", e.data);   // 15
};

worker.onerror = (e) => {
  console.error("Worker error:", e.message);
};

worker.terminate();   // kill the worker

// --- worker.js (runs in separate thread) ---
// self.onmessage = (e) => {
//   const sum = e.data.numbers.reduce((a, b) => a + b, 0);
//   self.postMessage(sum);
// };

// Inline worker (no separate file)
const blob = new Blob([`
  self.onmessage = (e) => {
    const result = e.data * 2;
    self.postMessage(result);
  };
`], { type: "application/javascript" });

const inlineWorker = new Worker(URL.createObjectURL(blob));
inlineWorker.postMessage(21);
inlineWorker.onmessage = (e) => console.log(e.data);   // 42

// GOTCHAS -- Web Workers
// - Data passed via postMessage is COPIED (structured clone), not shared.
//   Exception: Transferable objects (ArrayBuffer) can be zero-copy transferred.
// - Workers have their own global scope ("self"), NOT "window".
// - SharedWorker can be accessed by multiple tabs/iframes of the same origin.
// - Service Workers are a different API (for offline caching / PWA).
// - Workers cannot import ES modules in all browsers; use importScripts() or check support.


// ============================================================
// 15. ADVANCED EVENT PATTERNS                        [ADVANCED]
// ============================================================

// --- Debounce (fire AFTER user stops for N ms) ---
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

const searchInput = document.getElementById("search");
searchInput.addEventListener("input", debounce((e) => {
  console.log("Search:", e.target.value);
}, 300));

// --- Throttle (fire at most once per N ms) ---
function throttle(fn, limit) {
  let inThrottle = false;
  return (...args) => {
    if (inThrottle) return;
    fn(...args);
    inThrottle = true;
    setTimeout(() => (inThrottle = false), limit);
  };
}

window.addEventListener("scroll", throttle(() => {
  console.log("Scroll position:", window.scrollY);
}, 100));

// INTERVIEW: "When to debounce vs throttle?"
//  +-------------------+-----------------------------+-------------------------+
//  | Technique         | When it fires               | Use case                |
//  +-------------------+-----------------------------+-------------------------+
//  | Debounce          | After pause of N ms         | Search input, resize    |
//  | Throttle          | At most once per N ms       | Scroll, mousemove       |
//  +-------------------+-----------------------------+-------------------------+


// ============================================================
// 16. QUICK-REFERENCE:  GOTCHAS CHEAT SHEET
// ============================================================
//
//  1.  addEventListener("click", fn) with the SAME fn reference does NOT
//      add duplicates.  Different anonymous arrows DO add duplicates.
//
//  2.  event.target     = the element that triggered the event
//      event.currentTarget = the element the listener is attached to
//      INTERVIEW: "What is the difference between target and currentTarget?"
//
//  3.  preventDefault() stops default behavior (link navigation, form submit).
//      stopPropagation() stops event from traveling up/down the DOM.
//      They are INDEPENDENT -- one does not imply the other.
//
//  4.  "passive: true" on touchstart/touchmove/wheel makes scrolling smoother.
//      Calling preventDefault() inside a passive listener is silently ignored.
//
//  5.  querySelector returns FIRST match (or null).
//      querySelectorAll returns a static NodeList (not live).
//      getElementsByClassName returns a LIVE HTMLCollection.
//
//  6.  innerHTML triggers full reparse -- prefer textContent for plain text
//      and insertAdjacentHTML / createElement for new nodes.
//
//  7.  ClassList methods: add, remove, toggle, contains, replace.
//      element.classList.toggle("active") is idiomatic.
//
//  8.  dataset API: element.dataset.userId maps to data-user-id attribute.
//
//  9.  document.createDocumentFragment() batches DOM insertions (fewer reflows).
//
// 10.  Prefer "visibilitychange" event over "unload" for mobile reliability.
//      document.addEventListener("visibilitychange", () => {
//        if (document.visibilityState === "hidden") { /* save state */ }
//      });
