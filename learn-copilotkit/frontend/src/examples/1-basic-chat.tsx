/**
 * Example 1: Basic Chat
 * ---------------------
 * The simplest CopilotKit app — a chat box that talks to an AI backend.
 *
 * CopilotKit needs two things:
 *   1. A provider (CopilotKit) with the backend URL
 *   2. A chat UI component (CopilotChat)
 *
 * Backend: uv run python 01_hello_copilotkit.py  (or 06_full_backend.py)
 *
 * USED IN REUTERS:
 *   lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2.component.tsx
 *     — Wraps <ReutersAssistantAI> which internally uses CopilotKit + CopilotChat
 *   @reuters/assistant-v2 → reuters-assistant-ai.tsx
 *     — The ReutersAssistantAI component that LEON wraps
 */

import React from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function BasicChatApp() {
  // The URL where your CopilotKit-compatible backend lives.
  // In Reuters, this is built by createConfig() based on environment.
  const backendUrl = "http://localhost:8000/copilotkit";

  return (
    // CopilotKit wraps your app — everything inside can talk to the AI
    <CopilotKit url={backendUrl}>
      <div style={{ display: "flex", height: "100vh" }}>
        {/* Your app content goes here */}
        <div style={{ flex: 1, padding: 32 }}>
          <h1>My News App</h1>
          <p>The chat panel is on the right →</p>
        </div>

        {/* CopilotChat is the pre-built chat UI */}
        <div style={{ width: 400, borderLeft: "1px solid #e5e5e5" }}>
          <CopilotChat
            labels={{
              title: "AI Assistant",
              initial: "Hi! How can I help you today?",
            }}
            instructions="You are a helpful news assistant."
          />
        </div>
      </div>
    </CopilotKit>
  );
}

/*
 * HOW IT WORKS:
 *
 * 1. User types a message in the chat input
 * 2. CopilotKit sends a request to your backend:
 *      POST http://localhost:8000/copilotkit
 * 3. Backend streams response via SSE (Server-Sent Events)
 * 4. CopilotChat renders the streamed text in real time
 *
 * REUTERS EQUIVALENT:
 *   Instead of CopilotKit + CopilotChat directly,
 *   LEON uses <ReutersAssistantAI> which wraps both internally.
 *   See: lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2.component.tsx
 */
