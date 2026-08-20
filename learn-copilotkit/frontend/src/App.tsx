/**
 * App.tsx — Example Selector
 *
 * Pick an example from the sidebar to render it.
 * Each example connects to the Python backend at http://localhost:8000/copilotkit.
 *
 * Start the backend first:
 *   cd learn-copilotkit
 *   uv run python 06_full_backend.py   (works with all examples)
 *
 * Or run a specific lesson's backend to see only those features.
 */

import React, { useState } from "react";

import BasicChatApp from "./examples/1-basic-chat";
import PageContextApp from "./examples/2-page-context";
import ChatActionsApp from "./examples/3-chat-actions";
import InterruptsApp from "./examples/4-interrupts";
import GenerativeUIApp from "./examples/5-generative-ui";
import FullApp from "./examples/6-full-app";

const EXAMPLES = [
  { id: "1", name: "1 — Basic Chat", component: BasicChatApp, backend: "01_hello_copilotkit.py" },
  { id: "2", name: "2 — Page Context", component: PageContextApp, backend: "03_system_prompt_and_context.py" },
  { id: "3", name: "3 — Chat Actions", component: ChatActionsApp, backend: "06_full_backend.py" },
  { id: "4", name: "4 — Interrupts", component: InterruptsApp, backend: "06_full_backend.py" },
  { id: "5", name: "5 — Generative UI", component: GenerativeUIApp, backend: "04_streaming_and_generative_ui.py" },
  { id: "6", name: "6 — Full App", component: FullApp, backend: "06_full_backend.py" },
];

export default function App() {
  const [activeId, setActiveId] = useState("1");

  const activeExample = EXAMPLES.find((e) => e.id === activeId)!;
  const ActiveComponent = activeExample.component;

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      {/* Sidebar */}
      <div
        style={{
          width: 240,
          background: "#1e293b",
          color: "#e2e8f0",
          display: "flex",
          flexDirection: "column",
          padding: "16px 0",
        }}
      >
        <div style={{ padding: "0 16px 16px", fontWeight: 700, fontSize: 14 }}>
          Learn CopilotKit
        </div>

        {EXAMPLES.map((ex) => (
          <button
            key={ex.id}
            onClick={() => setActiveId(ex.id)}
            style={{
              background: ex.id === activeId ? "#334155" : "transparent",
              color: "#e2e8f0",
              border: "none",
              padding: "10px 16px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: ex.id === activeId ? 600 : 400,
            }}
          >
            {ex.name}
          </button>
        ))}

        <div style={{ marginTop: "auto", padding: "16px", fontSize: 11, color: "#94a3b8" }}>
          Backend: {activeExample.backend}
        </div>
      </div>

      {/* Active example */}
      <div style={{ flex: 1, overflow: "auto" }}>
        <ActiveComponent key={activeId} />
      </div>
    </div>
  );
}
