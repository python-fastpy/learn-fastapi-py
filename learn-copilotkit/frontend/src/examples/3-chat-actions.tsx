/**
 * Example 3: Chat Actions (useCopilotAction)
 * -------------------------------------------
 * Let the AI call functions in your frontend.
 *
 * Think of actions as "tools" that the AI can use.
 * You define the function name, its parameters, and a handler.
 * When the AI decides to use it, the handler runs in the browser.
 *
 * Real example: User says "change the headline to be shorter"
 * → AI generates a shorter headline
 * → AI calls your "update_headline" action
 * → Handler updates the React state
 * → UI re-renders with the new headline
 *
 * Backend: uv run python 06_full_backend.py
 *
 * USED IN REUTERS:
 *   lynx_leon/src/components/reuter-ai-assistant-v2/hooks/use-raia-action-handler.ts
 *     — Registers "create_draft" and "insert_into_story" frontend actions
 *   @reuters/assistant-v2 → hooks/useChatAction.ts
 *     — CopilotKit's useCopilotAction wrapped for Reuters patterns
 */

import React, { useState } from "react";
import { CopilotKit, useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function StoryEditor() {
  const [headline, setHeadline] = useState("Apple Reports Record Q2 Revenue Beating Analyst Expectations");
  const [body, setBody] = useState(
    "Apple Inc reported quarterly revenue of $94.8 billion, beating analyst expectations of $92.3 billion."
  );
  const [log, setLog] = useState<string[]>([]);

  // Send current story data to AI
  useCopilotReadable({
    description: "Current story",
    value: { headline, body },
  });

  // ACTION 1: Update the headline
  useCopilotAction({
    name: "update_headline",
    description: "Update the story headline. Use when the user asks to change, shorten, or rewrite the headline.",
    parameters: [
      {
        name: "new_headline",
        type: "string",
        description: "The new headline text",
        required: true,
      },
    ],
    handler: async ({ new_headline }) => {
      setHeadline(new_headline);
      setLog((prev) => [...prev, `Headline updated: "${new_headline}"`]);
      return `Headline updated to: "${new_headline}"`;
    },
  });

  // ACTION 2: Update the story body
  useCopilotAction({
    name: "update_body",
    description: "Update the story body text. Use when the user asks to rewrite, expand, or modify the story.",
    parameters: [
      {
        name: "new_body",
        type: "string",
        description: "The new body text",
        required: true,
      },
    ],
    handler: async ({ new_body }) => {
      setBody(new_body);
      setLog((prev) => [...prev, `Body updated (${new_body.length} chars)`]);
      return `Body updated (${new_body.length} characters)`;
    },
  });

  // ACTION 3: Insert text at a specific position
  useCopilotAction({
    name: "insert_text",
    description: "Insert text at the beginning or end of the story body.",
    parameters: [
      {
        name: "text",
        type: "string",
        description: "Text to insert",
        required: true,
      },
      {
        name: "position",
        type: "string",
        description: "Where to insert",
        enum: ["beginning", "end"],
        required: true,
      },
    ],
    handler: async ({ text, position }) => {
      if (position === "beginning") {
        setBody((prev) => text + "\n\n" + prev);
      } else {
        setBody((prev) => prev + "\n\n" + text);
      }
      setLog((prev) => [...prev, `Inserted text at ${position}`]);
      return `Text inserted at ${position}`;
    },
  });

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: 4 }}>Headline</label>
        <input
          value={headline}
          onChange={(e) => setHeadline(e.target.value)}
          style={{ width: "100%", padding: 8, fontSize: 18, border: "1px solid #d1d5db", borderRadius: 6 }}
        />
      </div>

      <div style={{ marginBottom: 24 }}>
        <label style={{ fontWeight: "bold", display: "block", marginBottom: 4 }}>Body</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={8}
          style={{ width: "100%", padding: 8, fontSize: 14, border: "1px solid #d1d5db", borderRadius: 6 }}
        />
      </div>

      {/* Action log — shows what the AI did */}
      {log.length > 0 && (
        <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 6, padding: 12 }}>
          <strong>Action Log:</strong>
          {log.map((entry, i) => (
            <div key={i} style={{ fontSize: 13, color: "#166534" }}>
              {entry}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ChatActionsApp() {
  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <div style={{ display: "flex", height: "100vh" }}>
        <div style={{ flex: 1, overflow: "auto" }}>
          <StoryEditor />
        </div>
        <div style={{ width: 400, borderLeft: "1px solid #e5e5e5" }}>
          <CopilotChat
            labels={{ title: "AI Assistant" }}
            instructions={`You are a Reuters story editor assistant.
You can update the headline, body, or insert text using the available actions.
Always confirm what you changed after making edits.`}
          />
        </div>
      </div>
    </CopilotKit>
  );
}

/*
 * TRY IT:
 *   1. "Make the headline shorter" → AI calls update_headline
 *   2. "Add a paragraph about market reaction at the end" → AI calls insert_text
 *   3. "Rewrite the entire body in AP style" → AI calls update_body
 *
 * HOW IT WORKS:
 *   1. useCopilotAction registers actions with CopilotKit
 *   2. CopilotKit sends them as available tools in the request
 *   3. The LLM sees these alongside backend tools
 *   4. When the LLM calls one, CopilotKit runs the handler in the browser
 *   5. The return value goes back to the LLM as the tool result
 */
