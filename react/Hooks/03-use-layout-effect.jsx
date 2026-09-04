import { useState, useRef, useEffect, useLayoutEffect } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useLayoutEffect HOOK — vs useEffect
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: useLayoutEffect(setup, dependencies?)  — identical to useEffect.
   The ONLY difference is WHEN it fires relative to the browser paint.

   TIMING DIAGRAM:
   ┌────────────────────────────────────────────────────────────────────────┐
   │  render()  →  React commits DOM mutations                              │
   │                     │                                                  │
   │                     ├─▶ useLayoutEffect runs SYNCHRONOUSLY, BLOCKING   │
   │                     │   the browser from painting until it finishes    │
   │                     │                                                  │
   │                     ▼                                                  │
   │              BROWSER PAINTS (user sees the frame)                      │
   │                     │                                                  │
   │                     └─▶ useEffect runs ASYNCHRONOUSLY, AFTER paint     │
   └────────────────────────────────────────────────────────────────────────┘

   RULE OF THUMB:
   ┌───────────────────────┬────────────────────────────────────────────────┐
   │ useEffect (default)   │ 99% of effects: data fetching, subscriptions,   │
   │                        │ logging, anything that doesn't touch layout    │
   │ useLayoutEffect (rare) │ ONLY when you must read layout (scroll position,│
   │                        │ element size/position via getBoundingClientRect)│
   │                        │ and synchronously adjust it before the user     │
   │                        │ ever sees the wrong frame — avoids a flicker    │
   └───────────────────────┴────────────────────────────────────────────────┘

   GOTCHAS:
   1. useLayoutEffect BLOCKS painting — overusing it makes your app feel
      slower/janky. Default to useEffect; reach for useLayoutEffect only
      when you can point to an actual visual flicker it fixes.
   2. No SSR support: React warns "useLayoutEffect does nothing on the
      server" because there's no DOM/paint to synchronize with. The common
      fix is a `useIsomorphicLayoutEffect` that falls back to useEffect
      when `typeof window === 'undefined'`.
   3. Both hooks have identical signatures and dependency-array rules —
      swapping one for the other is always syntactically valid; the only
      question is timing.
   4. Classic use cases: measuring a tooltip/popover before positioning it,
      synchronizing scroll position after a DOM change, avoiding a
      flash-of-wrong-content on autofocus.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
  box: { display: "inline-block", padding: "4px 12px", borderRadius: 4, background: "#eef", marginRight: 8 },
};

/* ─── Example 1: Measuring a DOM node — useEffect vs useLayoutEffect ─── */

function MeasuredBox({ label, useHook, text }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);

  useHook(() => {
    if (ref.current) setWidth(ref.current.getBoundingClientRect().width);
  }, [text]);

  return (
    <div style={{ marginBottom: 8 }}>
      <div ref={ref} style={styles.box}>{text}</div>
      <span>{label} measured width: <strong>{Math.round(width)}px</strong></span>
    </div>
  );
}

function MeasureComparison() {
  const [text, setText] = useState("hi");

  return (
    <div style={styles.section}>
      <h3>1. Measuring a DOM Node (both report the SAME number)</h3>
      <p>The measured value is identical — what differs is invisible here (timing),
        but matters when you use the measurement to reposition something before paint.</p>
      <button style={styles.btn} onClick={() => setText((t) => (t === "hi" ? "a much longer label" : "hi"))}>
        Toggle text length
      </button>
      <MeasuredBox label="useEffect" useHook={useEffect} text={text} />
      <MeasuredBox label="useLayoutEffect" useHook={useLayoutEffect} text={text} />
      <div style={styles.code}>{`// useEffect: measurement happens AFTER the browser already painted
// the old size — if you resized something based on it, users would
// briefly see the wrong size flash by (a "layout jump").

// useLayoutEffect: measurement + any resulting DOM write happen
// BEFORE paint — the user only ever sees the final, correct frame.`}</div>
    </div>
  );
}

/* ─── Example 2: Avoiding a flicker — tooltip that repositions itself ─── */

function Tooltip({ targetWidth }) {
  const ref = useRef(null);
  const [offset, setOffset] = useState(0);

  useLayoutEffect(() => {
    // If the tooltip would overflow past targetWidth, shift it left —
    // this MUST run before paint or the user sees it jump.
    if (!ref.current) return;
    const tooltipWidth = ref.current.getBoundingClientRect().width;
    setOffset(tooltipWidth > targetWidth ? -(tooltipWidth - targetWidth) : 0);
  }, [targetWidth]);

  return (
    <div
      ref={ref}
      style={{ ...styles.box, position: "relative", left: offset, background: "#333", color: "#fff" }}
    >
      Tooltip content that might overflow
    </div>
  );
}

function TooltipDemo() {
  const [containerWidth, setContainerWidth] = useState(300);

  return (
    <div style={styles.section}>
      <h3>2. Flicker-Free Repositioning (realistic useLayoutEffect case)</h3>
      <p>Shrink the container — the tooltip shifts left to stay in bounds, with no flash:</p>
      <div style={{ width: containerWidth, border: "1px dashed #999", padding: 8, overflow: "hidden" }}>
        <Tooltip targetWidth={containerWidth - 16} />
      </div>
      <button style={styles.btn} onClick={() => setContainerWidth((w) => (w === 300 ? 150 : 300))}>
        Toggle container width
      </button>
      <div style={styles.code}>{`useLayoutEffect(() => {
  const tooltipWidth = ref.current.getBoundingClientRect().width;
  setOffset(/* adjust before the user ever sees it overflow */);
}, [targetWidth]);`}</div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseLayoutEffectExample() {
  return (
    <div style={styles.container}>
      <h2>useLayoutEffect Hook</h2>
      <MeasureComparison />
      <TooltipDemo />
    </div>
  );
}
