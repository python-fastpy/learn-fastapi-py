/**
 * Example 2: Page Context (useCopilotReadable)
 * ---------------------------------------------
 * Send data from your app to the AI so it knows what the user is looking at.
 *
 * useCopilotReadable registers data that gets sent with EVERY chat message.
 * When the user asks "what story am I editing?", the AI already knows.
 *
 * Backend: uv run python 03_system_prompt_and_context.py  (or 06_full_backend.py)
 *
 * USED IN REUTERS:
 *   lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2-page-context.tsx
 *     — Builds page context from Redux store (story/alert data) and passes as externalContext
 *   @reuters/assistant-v2 → ReutersAssistantAI component
 *     — externalContext prop passes page data through CopilotKit's protocol
 *   reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py
 *     — Backend extracts page context and injects it into the system prompt
 */

import React, { useState } from "react";
import { CopilotKit, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

// Fake story data — in LEON this comes from the Redux store
const STORIES = [
  {
    id: "story-1",
    headline: "Apple Reports Record Q2 Earnings",
    slug: "AAPL-EARNINGS",
    ric: "AAPL.O",
    body: "Apple Inc reported quarterly revenue of $94.8 billion, beating analyst expectations...",
    language: "en",
  },
  {
    id: "story-2",
    headline: "Fed Holds Rates Steady at 5.5%",
    slug: "FED-RATES",
    ric: ".FED",
    body: "The Federal Reserve kept its benchmark interest rate unchanged...",
    language: "en",
  },
];

// This component makes its data available to the AI
function StoryEditor({ story }: { story: typeof STORIES[0] }) {
  // Tell CopilotKit: "here's what the user is looking at"
  // This data is automatically included in every chat request
  useCopilotReadable({
    description: "The news story the user is currently editing in the LEON editor",
    value: {
      headline: story.headline,
      slug: story.slug,
      ric: story.ric,
      body: story.body,
      language: story.language,
    },
  });

  return (
    <div style={{ padding: 24 }}>
      <h2>{story.headline}</h2>
      <p style={{ color: "#666" }}>
        {story.slug} | {story.ric} | {story.language}
      </p>
      <p>{story.body}</p>
    </div>
  );
}

export default function PageContextApp() {
  const [activeStory, setActiveStory] = useState(STORIES[0]);

  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <div style={{ display: "flex", height: "100vh" }}>
        {/* Left side: story selector + editor */}
        <div style={{ flex: 1 }}>
          <div style={{ padding: 16, borderBottom: "1px solid #e5e5e5" }}>
            {STORIES.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveStory(s)}
                style={{
                  marginRight: 8,
                  padding: "8px 16px",
                  background: s.id === activeStory.id ? "#2563eb" : "#f3f4f6",
                  color: s.id === activeStory.id ? "#fff" : "#000",
                  border: "none",
                  borderRadius: 6,
                  cursor: "pointer",
                }}
              >
                {s.slug}
              </button>
            ))}
          </div>

          {/* StoryEditor calls useCopilotReadable — AI knows this data */}
          <StoryEditor story={activeStory} />
        </div>

        {/* Right side: chat */}
        <div style={{ width: 400, borderLeft: "1px solid #e5e5e5" }}>
          <CopilotChat
            labels={{ title: "AI Assistant" }}
            instructions="You are a Reuters newsroom assistant. You can see the story the user is editing."
          />
        </div>
      </div>
    </CopilotKit>
  );
}

/*
 * TRY IT:
 *   1. Select AAPL-EARNINGS story
 *   2. Ask the AI: "What story am I editing?"
 *   3. AI responds with details about the AAPL story
 *   4. Switch to FED-RATES story
 *   5. Ask again — AI now sees the FED story
 *
 * HOW IT WORKS:
 *   useCopilotReadable injects data into CopilotKit's context.
 *   When a message is sent, CopilotKit includes this as a system
 *   message in the request. The backend reads it and passes it to the LLM.
 */
