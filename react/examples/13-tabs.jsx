import { useState } from "react";

/*
  TABS COMPONENT
  ──────────────
  Diagram:
    ┌────────┬────────┬────────┐
    │ Tab 1  │▐Tab 2▐│ Tab 3  │   ← active tab highlighted
    ├────────┴────────┴────────┤
    │                          │
    │   Content for Tab 2      │   ← only active content visible
    │                          │
    └──────────────────────────┘

  Key concepts:
    - Parent owns activeTab state
    - Tab header buttons set activeTab
    - Conditional rendering shows only active panel
    - aria attributes for accessibility
*/

const TAB_DATA = [
  {
    id: "overview",
    label: "Overview",
    content:
      "React lets you build user interfaces out of individual pieces called components. Create your own React components like Thumbnail, LikeButton, and Video. Then combine them into entire screens, pages, and apps.",
  },
  {
    id: "features",
    label: "Features",
    content:
      "Key features include: Virtual DOM for performance, JSX syntax, one-way data flow, component-based architecture, hooks for state management, and a rich ecosystem of tools and libraries.",
  },
  {
    id: "getting-started",
    label: "Getting Started",
    content:
      'The easiest way to start with React is: npx create-react-app my-app. For production projects, consider Next.js or Vite. Install React DevTools browser extension for debugging.',
  },
];

const styles = {
  container: { padding: 20, fontFamily: "sans-serif", maxWidth: 500 },
  tabList: { display: "flex", borderBottom: "2px solid #ddd" },
  tab: {
    padding: "10px 20px",
    cursor: "pointer",
    border: "none",
    background: "transparent",
    fontSize: 14,
    borderBottom: "2px solid transparent",
    marginBottom: -2,
    color: "#666",
    transition: "all 0.2s",
  },
  tabActive: {
    borderBottomColor: "#1a73e8",
    color: "#1a73e8",
    fontWeight: "bold",
  },
  panel: {
    padding: 16,
    lineHeight: 1.6,
    border: "1px solid #ddd",
    borderTop: "none",
    borderRadius: "0 0 8px 8px",
    minHeight: 100,
  },
};

// ─── Reusable Tab Component ──────────────────────────────────────────────────

function Tabs({ tabs, defaultTab }) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0].id);

  const activeContent = tabs.find((t) => t.id === activeTab)?.content;

  return (
    <div>
      {/* Tab Headers */}
      <div style={styles.tabList} role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            style={{
              ...styles.tab,
              ...(activeTab === tab.id ? styles.tabActive : {}),
            }}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Active Panel */}
      <div style={styles.panel} role="tabpanel">
        {activeContent}
      </div>
    </div>
  );
}

// ─── Demo ────────────────────────────────────────────────────────────────────

export default function TabsExample() {
  return (
    <div style={styles.container}>
      <h3>Tabs</h3>
      <Tabs tabs={TAB_DATA} defaultTab="overview" />
    </div>
  );
}
