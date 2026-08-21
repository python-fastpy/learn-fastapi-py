import { useState, useRef, useImperativeHandle, forwardRef } from "react";

/* ═══════════════════════════════════════════════════════════════════════════════
   useImperativeHandle HOOK — COMPLETE GUIDE
   ═══════════════════════════════════════════════════════════════════════════════

   Signature: useImperativeHandle(ref, createHandle, [deps])

   PURPOSE: Customize the value exposed to parent when using ref.
   Instead of exposing the raw DOM node, you expose a CUSTOM object
   with only the methods you want.

   DIAGRAM:
   ┌───────────────────────────────────────────────────────────────┐
   │  WITHOUT useImperativeHandle:                                │
   │  parentRef.current = <input> DOM node                        │
   │  → Parent can do ANYTHING: .remove(), .style = ..., etc.     │
   │                                                               │
   │  WITH useImperativeHandle:                                   │
   │  parentRef.current = { focus(), scrollIntoView() }           │
   │  → Parent can ONLY call the methods you expose               │
   └───────────────────────────────────────────────────────────────┘

   GOTCHAS:
   1. MUST be used with forwardRef (component must accept a ref).
   2. The handle object replaces the default ref value.
      Parent does NOT get the DOM node unless you explicitly include it.
   3. Avoid overusing — imperative patterns break React's declarative model.
      Prefer props/state for communication. Use only when needed (focus,
      scroll, animations that can't be expressed declaratively).
   4. deps array works like useEffect/useMemo — handle is recreated
      when deps change.
   ═══════════════════════════════════════════════════════════════════════════════ */

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 600 },
  section: { marginBottom: 24, padding: 16, border: "1px solid #e0e0e0", borderRadius: 8 },
  btn: { padding: "8px 16px", margin: 4, cursor: "pointer", borderRadius: 4, border: "none", background: "#1a73e8", color: "#fff" },
  input: { padding: "8px 12px", border: "2px solid #ccc", borderRadius: 4, width: "100%", boxSizing: "border-box", fontSize: 14 },
  code: { background: "#f5f5f5", padding: 12, borderRadius: 6, fontFamily: "monospace", fontSize: 12, whiteSpace: "pre", marginTop: 8 },
};

/* ─── Example 1: Custom Input with limited API ─── */

const CustomInput = forwardRef(function CustomInput(props, ref) {
  const inputRef = useRef(null);

  useImperativeHandle(ref, () => ({
    // Only expose these methods — NOT the raw DOM node
    focus: () => inputRef.current.focus(),
    clear: () => {
      inputRef.current.value = "";
      inputRef.current.focus();
    },
    getValue: () => inputRef.current.value,
    alertValue: () => alert(`Input value: "${inputRef.current.value}"`),
    // Parent canNOT do: ref.current.style, ref.current.remove(), etc.
  }), []); // no deps — handle is stable

  return (
    <input
      ref={inputRef}
      style={{ ...styles.input, border: "2px solid #1a73e8" }}
      placeholder={props.placeholder}
      defaultValue={props.defaultValue}
    />
  );
});

function CustomInputExample() {
  const inputRef = useRef(null);

  return (
    <div style={styles.section}>
      <h3>1. Custom Input (limited API)</h3>
      <CustomInput ref={inputRef} placeholder="Type here..." defaultValue="Hello" />
      <div style={{ marginTop: 8 }}>
        <button style={styles.btn} onClick={() => inputRef.current.focus()}>Focus</button>
        <button style={styles.btn} onClick={() => inputRef.current.clear()}>Clear</button>
        <button style={styles.btn} onClick={() => inputRef.current.alertValue()}>Alert Value</button>
        <button style={styles.btn} onClick={() => alert(inputRef.current.getValue())}>Get Value</button>
      </div>
      <div style={styles.code}>{`// Parent sees: { focus(), clear(), getValue(), alertValue() }
// Parent canNOT access: .style, .remove(), .innerHTML, etc.

useImperativeHandle(ref, () => ({
  focus: () => inputRef.current.focus(),
  clear: () => { inputRef.current.value = ""; },
}));`}</div>
    </div>
  );
}

/* ─── Example 2: Video Player Controls ─── */

const VideoPlayer = forwardRef(function VideoPlayer({ src }, ref) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(50);

  useImperativeHandle(ref, () => ({
    play: () => setIsPlaying(true),
    pause: () => setIsPlaying(false),
    toggle: () => setIsPlaying((p) => !p),
    setVolume: (v) => setVolume(Math.max(0, Math.min(100, v))),
    getState: () => ({ isPlaying, volume }),
  }), [isPlaying, volume]); // recreate when state changes

  return (
    <div style={{ padding: 16, background: "#1e1e1e", borderRadius: 8, color: "#fff" }}>
      <p>{isPlaying ? "Playing" : "Paused"} — Vol: {volume}%</p>
      <div style={{ height: 8, background: "#333", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${volume}%`, height: "100%", background: "#1a73e8", transition: "width 0.2s" }} />
      </div>
      <p style={{ fontSize: 11, color: "#999" }}>Source: {src}</p>
    </div>
  );
});

function VideoPlayerExample() {
  const playerRef = useRef(null);

  return (
    <div style={styles.section}>
      <h3>2. Video Player (imperative controls)</h3>
      <VideoPlayer ref={playerRef} src="example-video.mp4" />
      <div style={{ marginTop: 8 }}>
        <button style={styles.btn} onClick={() => playerRef.current.play()}>Play</button>
        <button style={{ ...styles.btn, background: "#ea4335" }} onClick={() => playerRef.current.pause()}>Pause</button>
        <button style={styles.btn} onClick={() => playerRef.current.toggle()}>Toggle</button>
        <button style={styles.btn} onClick={() => playerRef.current.setVolume(100)}>Max Vol</button>
        <button style={styles.btn} onClick={() => playerRef.current.setVolume(0)}>Mute</button>
        <button style={styles.btn} onClick={() => alert(JSON.stringify(playerRef.current.getState()))}>Get State</button>
      </div>
    </div>
  );
}

/* ─── MAIN ─── */

export default function UseImperativeHandleExample() {
  return (
    <div style={styles.container}>
      <h2>useImperativeHandle Hook</h2>
      <CustomInputExample />
      <VideoPlayerExample />
    </div>
  );
}
