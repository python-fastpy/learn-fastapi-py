import { useState } from "react";

/* ─── Fundamentals ─── */
import EventHandling from "./Fundamentals/01-event-handling";
import StateAsMemory from "./Fundamentals/02-state-as-memory";
import RenderAndCommit from "./Fundamentals/03-render-and-commit";
import KeysAndListReconciliation from "./Fundamentals/04-keys-and-list-reconciliation";
import StateAsSnapshot from "./Fundamentals/05-state-as-snapshot";
import StateUpdateQueuing from "./Fundamentals/06-state-update-queuing";
import UpdatingObjects from "./Fundamentals/07-updating-objects-in-state";
import UpdatingArrays from "./Fundamentals/08-updating-arrays-in-state";

/* ─── Legacy APIs ─── */
import CreateElement from "./LegacyAPIs/01-create-element";

/* ─── Class Components ─── */
import LifecycleMethods from "./ClassComponents/01-lifecycle-methods";
import ErrorBoundaries from "./ClassComponents/02-error-boundaries";

/* ─── Hooks ─── */
import UseState from "./Hooks/01-use-state";
import UseEffect from "./Hooks/02-use-effect";
import UseLayoutEffect from "./Hooks/03-use-layout-effect";
import UseContext from "./Hooks/04-use-context";
import UseReducer from "./Hooks/05-use-reducer";
import UseRef from "./Hooks/06-use-ref";
import UseMemo from "./Hooks/07-use-memo";
import UseCallback from "./Hooks/08-use-callback";
import UseDeferredValue from "./Hooks/09-use-deferred-value";
import UseImperativeHandle from "./Hooks/10-use-imperative-handle";
import CustomHooks from "./Hooks/11-custom-hooks";

/* ─── APIs ─── */
import MemoExample from "./APIs/01-memo";
import CreatePortal from "./APIs/02-create-portal";
import ForwardRef from "./APIs/03-forward-ref";
import LazyLoading from "./APIs/04-lazy-loading";
import StartTransition from "./APIs/05-start-transition";

/* ─── Components ─── */
import Fragments from "./Components/01-fragments";
import Profiler from "./Components/02-profiler";
import Suspense from "./Components/03-suspense";

/* ─── Examples ─── */
import Checkbox from "./examples/01-checkbox";
import NestedCheckbox from "./examples/02-nested-checkbox";
import InputSuggestion from "./examples/03-input-suggestion";
import Filter from "./examples/04-filter";
import TableSort from "./examples/05-table-with-sort";
import Debounce from "./examples/06-debounce";
import Throttle from "./examples/07-throttle";
import ApiCrud from "./examples/08-crud-app";
import Hoc from "./examples/09-higher-order-component";
import RenderPropsAndCompoundComponents from "./examples/10-render-props-and-compound-components";
import Accordion from "./examples/11-accordion";
import ControlledUncontrolled from "./examples/12-controlled-vs-uncontrolled";
import Tabs from "./examples/13-tabs";
import Form from "./examples/14-form";
import FormValidation from "./examples/15-form-with-validation";

/* NOTE: VDOM/virtual-dom.js is a standalone, node-runnable conceptual
   reference (hand-rolled createElement/render/diff/applyPatch) — it is
   not a React component and is intentionally not wired into the sidebar
   below. Run it directly: `node VDOM/virtual-dom.js` */

/* ═══════════════════════════════════════════════════════════════════════════════
   MAIN APP — React Complete Learning Guide
   ═══════════════════════════════════════════════════════════════════════════════

   Run with: npx create-react-app my-app (then copy files in)
   Or with Vite: npm create vite@latest my-app -- --template react

   This app provides sidebar navigation to explore every React concept.
   ═══════════════════════════════════════════════════════════════════════════════ */

const sections = [
  {
    title: "Fundamentals",
    items: [
      { id: "event-handling", label: "01 Event Handling", component: EventHandling },
      { id: "state-memory", label: "02 State as Memory", component: StateAsMemory },
      { id: "render-commit", label: "03 Render & Commit", component: RenderAndCommit },
      { id: "keys-reconciliation", label: "04 Keys & List Reconciliation", component: KeysAndListReconciliation },
      { id: "state-snapshot", label: "05 State as Snapshot", component: StateAsSnapshot },
      { id: "state-queuing", label: "06 State Update Queuing", component: StateUpdateQueuing },
      { id: "updating-objects", label: "07 Updating Objects", component: UpdatingObjects },
      { id: "updating-arrays", label: "08 Updating Arrays", component: UpdatingArrays },
    ],
  },
  {
    title: "Legacy APIs",
    items: [
      { id: "create-element", label: "01 createElement", component: CreateElement },
    ],
  },
  {
    title: "Class Components",
    items: [
      { id: "lifecycle-methods", label: "01 Lifecycle Methods", component: LifecycleMethods },
      { id: "error-boundaries", label: "02 Error Boundaries", component: ErrorBoundaries },
    ],
  },
  {
    title: "Hooks",
    items: [
      { id: "use-state", label: "01 useState", component: UseState },
      { id: "use-effect", label: "02 useEffect", component: UseEffect },
      { id: "use-layout-effect", label: "03 useLayoutEffect", component: UseLayoutEffect },
      { id: "use-context", label: "04 useContext", component: UseContext },
      { id: "use-reducer", label: "05 useReducer", component: UseReducer },
      { id: "use-ref", label: "06 useRef", component: UseRef },
      { id: "use-memo", label: "07 useMemo", component: UseMemo },
      { id: "use-callback", label: "08 useCallback", component: UseCallback },
      { id: "use-deferred", label: "09 useDeferredValue", component: UseDeferredValue },
      { id: "use-imperative", label: "10 useImperativeHandle", component: UseImperativeHandle },
      { id: "custom-hooks", label: "11 Custom Hooks", component: CustomHooks },
    ],
  },
  {
    title: "APIs",
    items: [
      { id: "memo", label: "01 memo", component: MemoExample },
      { id: "create-portal", label: "02 createPortal", component: CreatePortal },
      { id: "forward-ref", label: "03 forwardRef", component: ForwardRef },
      { id: "lazy-loading", label: "04 lazy + Suspense", component: LazyLoading },
      { id: "start-transition", label: "05 startTransition", component: StartTransition },
    ],
  },
  {
    title: "Components",
    items: [
      { id: "fragments", label: "01 Fragments", component: Fragments },
      { id: "profiler", label: "02 Profiler", component: Profiler },
      { id: "suspense", label: "03 Suspense", component: Suspense },
    ],
  },
  {
    title: "Practical Examples",
    items: [
      { id: "ex-checkbox", label: "01 Checkbox", component: Checkbox },
      { id: "ex-nested-cb", label: "02 Nested Checkbox", component: NestedCheckbox },
      { id: "ex-suggestion", label: "03 Input Suggestion", component: InputSuggestion },
      { id: "ex-filter", label: "04 Filter", component: Filter },
      { id: "ex-table", label: "05 Table Sort", component: TableSort },
      { id: "ex-debounce", label: "06 Debounce", component: Debounce },
      { id: "ex-throttle", label: "07 Throttle", component: Throttle },
      { id: "ex-crud", label: "08 API CRUD", component: ApiCrud },
      { id: "ex-hoc", label: "09 HOC", component: Hoc },
      { id: "ex-render-props", label: "10 Render Props & Compound Components", component: RenderPropsAndCompoundComponents },
      { id: "ex-accordion", label: "11 Accordion", component: Accordion },
      { id: "ex-controlled", label: "12 Controlled vs Uncontrolled", component: ControlledUncontrolled },
      { id: "ex-tabs", label: "13 Tabs", component: Tabs },
      { id: "ex-form", label: "14 Form", component: Form },
      { id: "ex-validation", label: "15 Form Validation", component: FormValidation },
    ],
  },
];

const styles = {
  app: { display: "flex", height: "100vh", fontFamily: "sans-serif" },
  sidebar: { width: 260, minWidth: 260, background: "#1a1a2e", color: "#eee", overflowY: "auto", padding: "16px 0" },
  sidebarTitle: { padding: "8px 16px", fontSize: 18, fontWeight: "bold", color: "#4fc3f7", borderBottom: "1px solid #333", marginBottom: 8 },
  sectionTitle: { padding: "12px 16px 4px", fontSize: 11, textTransform: "uppercase", letterSpacing: 1, color: "#888" },
  navItem: { display: "block", padding: "6px 16px 6px 24px", fontSize: 13, cursor: "pointer", border: "none", background: "none", color: "#ccc", textAlign: "left", width: "100%" },
  navItemActive: { display: "block", padding: "6px 16px 6px 24px", fontSize: 13, cursor: "pointer", border: "none", background: "#16213e", color: "#4fc3f7", textAlign: "left", width: "100%", fontWeight: "bold" },
  content: { flex: 1, overflowY: "auto", padding: 24, background: "#fafafa" },
  welcome: { textAlign: "center", paddingTop: 80, color: "#666" },
};

export default function App() {
  const [activeId, setActiveId] = useState(null);

  const activeItem = sections.flatMap((s) => s.items).find((i) => i.id === activeId);
  const ActiveComponent = activeItem?.component;

  return (
    <div style={styles.app}>
      {/* Sidebar */}
      <nav style={styles.sidebar}>
        <div style={styles.sidebarTitle}>React Guide</div>
        {sections.map((section) => (
          <div key={section.title}>
            <div style={styles.sectionTitle}>{section.title}</div>
            {section.items.map((item) => (
              <button
                key={item.id}
                style={activeId === item.id ? styles.navItemActive : styles.navItem}
                onClick={() => setActiveId(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        ))}
      </nav>

      {/* Content */}
      <main style={styles.content}>
        {ActiveComponent ? (
          <ActiveComponent />
        ) : (
          <div style={styles.welcome}>
            <h1 style={{ fontSize: 28, color: "#333" }}>React Complete Guide</h1>
            <p style={{ fontSize: 16, maxWidth: 500, margin: "16px auto" }}>
              Select a topic from the sidebar to explore interactive examples covering Fundamentals, Legacy APIs, Class Components, Hooks, APIs, Components, and practical patterns.
            </p>
            <p style={{ fontSize: 13, color: "#999" }}>
              {sections.reduce((n, s) => n + s.items.length, 0)} interactive examples across {sections.length} categories
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
