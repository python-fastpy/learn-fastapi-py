/**
 * Example 4: Agent Interrupts (Human-in-the-Loop)
 * ------------------------------------------------
 * The AI pauses mid-execution, shows a review card, and waits
 * for the user to approve/reject/refine before continuing.
 *
 * This is the CORE pattern behind Reuters draft reviews:
 *   - Buzz review cards
 *   - RIC selection prompts
 *   - Story draft approvals
 *   - Urgent builder reviews
 *
 * CopilotKit calls this "renderAndWait" — the action renders UI
 * and blocks until resolve() is called.
 *
 * Backend: uv run python 06_full_backend.py
 *
 * USED IN REUTERS:
 *   lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-skills-interrupt.component.tsx
 *     — Renders interrupt UI based on EventType (NEWS_BUZZ.REVIEW, SPOT_STORY_REVIEW, etc.)
 *   @reuters/assistant-v2 → hooks/useAgentInterrupt.ts
 *     — Handles agent interrupt lifecycle
 *   @reuters/assistant-v2 → hooks/useSkillInterrupt.ts
 *     — Handles skill-specific interrupts
 *   reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py
 *     — LangGraph interrupt() + DynamoDB checkpoint for state persistence across interrupts
 */

import React from "react";
import { CopilotKit, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function InterruptActions() {
  // ACTION: Review a generated draft before applying it
  // The AI calls this to show a draft card and wait for user approval
  useCopilotAction({
    name: "review_draft",
    description:
      "Present a generated draft to the user for review. " +
      "The user can approve, reject, or request changes. " +
      "Use this BEFORE applying any generated content.",
    parameters: [
      {
        name: "headline",
        type: "string",
        description: "The draft headline",
        required: true,
      },
      {
        name: "body",
        type: "string",
        description: "The draft body content",
        required: true,
      },
      {
        name: "draft_type",
        type: "string",
        description: "Type of draft",
        enum: ["buzz", "story", "bulletin", "urgent"],
        required: true,
      },
    ],

    // renderAndWait: shows UI and PAUSES execution until resolve() is called
    renderAndWait: ({ args, resolve, status }) => {
      // After user responds, show a "done" state
      if (status === "complete") {
        return (
          <div style={styles.card}>
            <div style={{ color: "#16a34a", fontWeight: "bold" }}>Review submitted</div>
          </div>
        );
      }

      // Active review card — user hasn't responded yet
      return (
        <div style={styles.card}>
          <div style={styles.header}>
            <span style={styles.badge}>{args.draft_type?.toUpperCase()}</span>
            <span style={{ fontSize: 12, color: "#6b7280" }}>Draft Review</span>
          </div>

          <h3 style={{ margin: "12px 0 8px" }}>{args.headline}</h3>

          <div style={styles.bodyPreview}>{args.body}</div>

          <div style={styles.actions}>
            {/* Approve — AI continues with the draft as-is */}
            <button
              onClick={() => resolve("approved")}
              style={{ ...styles.btn, background: "#22c55e", color: "#fff" }}
            >
              Approve
            </button>

            {/* Reject — AI discards the draft */}
            <button
              onClick={() => resolve("rejected")}
              style={{ ...styles.btn, background: "#ef4444", color: "#fff" }}
            >
              Reject
            </button>

            {/* Refine — AI gets feedback and tries again */}
            <button
              onClick={() => {
                const feedback = window.prompt("What should be changed?");
                if (feedback) {
                  resolve(`refine: ${feedback}`);
                }
              }}
              style={{ ...styles.btn, background: "#3b82f6", color: "#fff" }}
            >
              Refine
            </button>
          </div>
        </div>
      );
    },
  });

  // ACTION: RIC selection — let user pick from multiple options
  // Similar to NEWS_BUZZ.RIC_SELECTION interrupt in Reuters
  useCopilotAction({
    name: "select_ric",
    description:
      "Present multiple RIC options to the user and wait for them to select one. " +
      "Use when the user's company name matches multiple instruments.",
    parameters: [
      {
        name: "company_name",
        type: "string",
        description: "The company name searched for",
        required: true,
      },
      {
        name: "options",
        type: "object[]",
        description: "Array of RIC options with ric, exchange, and description",
        required: true,
      },
    ],
    renderAndWait: ({ args, resolve, status }) => {
      if (status === "complete") {
        return (
          <div style={styles.card}>
            <div style={{ color: "#16a34a" }}>RIC selected</div>
          </div>
        );
      }

      const options = (args.options as any[]) || [];

      return (
        <div style={styles.card}>
          <div style={styles.header}>
            <span style={styles.badge}>RIC SELECTION</span>
          </div>
          <p>Multiple instruments found for "{args.company_name}". Please select one:</p>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {options.map((opt: any, i: number) => (
              <button
                key={i}
                onClick={() => resolve(opt.ric)}
                style={{
                  ...styles.btn,
                  background: "#f3f4f6",
                  color: "#111",
                  textAlign: "left",
                  padding: "12px 16px",
                }}
              >
                <strong>{opt.ric}</strong> — {opt.exchange}
                <br />
                <span style={{ fontSize: 12, color: "#6b7280" }}>{opt.description}</span>
              </button>
            ))}
          </div>
        </div>
      );
    },
  });

  return null;
}

export default function InterruptsApp() {
  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <div style={{ display: "flex", height: "100vh" }}>
        <div style={{ flex: 1, padding: 32 }}>
          <h1>Interrupt Examples</h1>
          <p>Try these in the chat:</p>
          <ul>
            <li>"Write a buzz for Apple earnings" → AI generates draft → shows review card</li>
            <li>"Look up the RIC for Apple" → AI finds multiple RICs → shows selection card</li>
          </ul>
          <p style={{ color: "#6b7280", marginTop: 16 }}>
            The AI pauses when it shows a card. It only continues after you click a button.
          </p>
        </div>

        <div style={{ width: 420, borderLeft: "1px solid #e5e5e5" }}>
          <InterruptActions />
          <CopilotChat
            labels={{ title: "AI Assistant" }}
            instructions={`You are a Reuters newsroom assistant.
When generating any draft, ALWAYS use the review_draft action first to let the user approve it.
When looking up RICs that have multiple matches, use select_ric to let the user choose.
After approval, confirm what you did.`}
          />
        </div>
      </div>
    </CopilotKit>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  card: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: 16,
    margin: "8px 0",
    background: "#fafafa",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  badge: {
    background: "#dbeafe",
    color: "#1d4ed8",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    fontWeight: "bold",
  },
  bodyPreview: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 6,
    padding: 12,
    fontSize: 14,
    lineHeight: 1.6,
    whiteSpace: "pre-wrap" as const,
    maxHeight: 200,
    overflow: "auto",
  },
  actions: {
    display: "flex",
    gap: 8,
    marginTop: 12,
  },
  btn: {
    padding: "8px 16px",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontWeight: 500,
    fontSize: 14,
  },
};

/*
 * HOW IT WORKS:
 *
 *   1. AI decides to generate a draft
 *   2. AI calls "review_draft" action with the draft content
 *   3. CopilotKit sees renderAndWait → renders the card in the chat
 *   4. Execution PAUSES — AI is waiting for resolve()
 *   5. User clicks "Approve" → resolve("approved") fires
 *   6. CopilotKit sends the resolved value back to the backend
 *   7. AI receives "approved" and continues (e.g., applies the draft)
 *
 * REUTERS INTERRUPT EVENT TYPES:
 *   - NEWS_BUZZ.REVIEW         → Buzz draft review card
 *   - NEWS_BUZZ.RIC_SELECTION  → RIC picker (like select_ric above)
 *   - PREVIEW_BUZZ_REVIEW      → Preview buzz review
 *   - SPOT_STORY_REVIEW        → Spot story review
 *   - URGENT_BUILDER_REVIEW    → Urgent builder review
 *   - NEWS_BULLETIN_REVIEW     → Bulletin review
 */
