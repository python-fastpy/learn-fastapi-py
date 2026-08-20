/**
 * Example 6: Full Working App
 * ----------------------------
 * Everything from examples 1-5 wired together into one app.
 * This mimics what LEON does with @reuters/assistant-v2.
 *
 * Features:
 *   - Page context (AI knows what story you're editing)
 *   - Chat actions (AI can update headline, body, insert text)
 *   - Interrupts (AI shows draft review card before applying changes)
 *   - Generative UI (live progress chips during operations)
 */

import React, { useState, useCallback } from "react";
import {
  CopilotKit,
  useCopilotReadable,
  useCopilotAction,
} from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

// ─────────────────────────────────────────────────────────────
// Story data type
// ─────────────────────────────────────────────────────────────
interface Story {
  id: string;
  headline: string;
  slug: string;
  ric: string;
  body: string;
}

const INITIAL_STORY: Story = {
  id: "story-1",
  headline: "Apple Reports Record Q2 Revenue",
  slug: "AAPL-EARNINGS",
  ric: "AAPL.O",
  body: "Apple Inc reported quarterly revenue of $94.8 billion, beating analyst expectations of $92.3 billion. The company's services division saw 15% growth.",
};

// ─────────────────────────────────────────────────────────────
// Activity log — shows what the AI did
// ─────────────────────────────────────────────────────────────
function ActivityLog({ entries }: { entries: string[] }) {
  if (entries.length === 0) return null;
  return (
    <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: 12, marginTop: 16 }}>
      <strong style={{ fontSize: 13 }}>Activity Log</strong>
      {entries.map((entry, i) => (
        <div key={i} style={{ fontSize: 12, color: "#166534", padding: "2px 0" }}>
          {entry}
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main editor with all CopilotKit hooks
// ─────────────────────────────────────────────────────────────
function StoryEditor({
  story,
  onUpdate,
  log,
  addLog,
}: {
  story: Story;
  onUpdate: (updates: Partial<Story>) => void;
  log: string[];
  addLog: (msg: string) => void;
}) {
  // ── PAGE CONTEXT ──
  // AI can see the current story data in every request
  useCopilotReadable({
    description: "The news story currently open in the editor",
    value: {
      headline: story.headline,
      slug: story.slug,
      ric: story.ric,
      body: story.body,
    },
  });

  // ── ACTION: Direct edit (no approval needed) ──
  useCopilotAction({
    name: "quick_edit_headline",
    description: "Directly update the headline without review. Use for small tweaks only.",
    parameters: [
      { name: "headline", type: "string", description: "New headline", required: true },
    ],
    handler: async ({ headline }) => {
      onUpdate({ headline });
      addLog(`Headline → "${headline}"`);
      return `Headline updated to: "${headline}"`;
    },
  });

  // ── ACTION WITH INTERRUPT: Review before applying ──
  // This is how Reuters draft reviews work
  useCopilotAction({
    name: "review_and_apply_draft",
    description:
      "Generate a rewritten story and show it for user approval before applying. " +
      "ALWAYS use this for major rewrites. The user must approve before changes are applied.",
    parameters: [
      { name: "headline", type: "string", description: "Proposed headline", required: true },
      { name: "body", type: "string", description: "Proposed body text", required: true },
      { name: "change_summary", type: "string", description: "Brief summary of what changed" },
    ],
    // renderAndWait = interrupt = pauses until user responds
    renderAndWait: ({ args, resolve, status }) => {
      if (status === "complete") {
        return (
          <div style={styles.reviewCard}>
            <span style={{ color: "#16a34a", fontWeight: 600 }}>Review complete</span>
          </div>
        );
      }

      return (
        <div style={styles.reviewCard}>
          <div style={styles.reviewHeader}>
            <span style={styles.reviewBadge}>DRAFT REVIEW</span>
            {args.change_summary && (
              <span style={{ fontSize: 12, color: "#6b7280" }}>{args.change_summary}</span>
            )}
          </div>

          <div style={styles.reviewField}>
            <label style={styles.reviewLabel}>Headline</label>
            <div style={styles.reviewValue}>{args.headline}</div>
          </div>

          <div style={styles.reviewField}>
            <label style={styles.reviewLabel}>Body</label>
            <div style={{ ...styles.reviewValue, maxHeight: 150, overflow: "auto" }}>
              {args.body}
            </div>
          </div>

          <div style={styles.reviewActions}>
            <button
              onClick={() => resolve("approved")}
              style={{ ...styles.reviewBtn, background: "#22c55e", color: "#fff" }}
            >
              Apply Changes
            </button>
            <button
              onClick={() => resolve("rejected")}
              style={{ ...styles.reviewBtn, background: "#ef4444", color: "#fff" }}
            >
              Discard
            </button>
            <button
              onClick={() => {
                const feedback = window.prompt("What should be changed?");
                if (feedback) resolve(`refine: ${feedback}`);
              }}
              style={{ ...styles.reviewBtn, background: "#3b82f6", color: "#fff" }}
            >
              Refine
            </button>
          </div>
        </div>
      );
    },

    // This handler runs AFTER the user approves
    handler: async ({ headline, body }) => {
      onUpdate({ headline, body });
      addLog(`Draft approved and applied`);
      return "Changes applied successfully";
    },
  });

  // ── ACTION WITH GENERATIVE UI: Search with progress ──
  useCopilotAction({
    name: "search_related",
    description: "Search for related stories in the archive.",
    parameters: [
      { name: "query", type: "string", description: "Search query", required: true },
    ],
    render: ({ status, args, result }) => {
      if (status === "inProgress" || status === "executing") {
        return (
          <div style={styles.searchChip}>Searching for "{args.query}"...</div>
        );
      }
      if (status === "complete" && result) {
        return (
          <div style={{ ...styles.searchChip, background: "#dcfce7", color: "#166534" }}>
            Found results for "{args.query}"
          </div>
        );
      }
      return null;
    },
    handler: async ({ query }) => {
      await new Promise((r) => setTimeout(r, 1500));
      addLog(`Searched archive: "${query}"`);
      return `Found 12 related articles about "${query}"`;
    },
  });

  return (
    <div style={{ padding: 24, maxWidth: 700 }}>
      {/* Headline editor */}
      <div style={{ marginBottom: 16 }}>
        <label style={styles.editorLabel}>Headline</label>
        <input
          value={story.headline}
          onChange={(e) => onUpdate({ headline: e.target.value })}
          style={styles.headlineInput}
        />
      </div>

      {/* Metadata */}
      <div style={{ display: "flex", gap: 16, marginBottom: 16, fontSize: 13, color: "#6b7280" }}>
        <span>Slug: {story.slug}</span>
        <span>RIC: {story.ric}</span>
      </div>

      {/* Body editor */}
      <div style={{ marginBottom: 16 }}>
        <label style={styles.editorLabel}>Body</label>
        <textarea
          value={story.body}
          onChange={(e) => onUpdate({ body: e.target.value })}
          rows={10}
          style={styles.bodyTextarea}
        />
      </div>

      {/* What the AI did */}
      <ActivityLog entries={log} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Root app
// ─────────────────────────────────────────────────────────────
export default function FullApp() {
  const [story, setStory] = useState<Story>(INITIAL_STORY);
  const [log, setLog] = useState<string[]>([]);

  const handleUpdate = useCallback((updates: Partial<Story>) => {
    setStory((prev) => ({ ...prev, ...updates }));
  }, []);

  const addLog = useCallback((msg: string) => {
    const time = new Date().toLocaleTimeString();
    setLog((prev) => [...prev, `[${time}] ${msg}`]);
  }, []);

  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <div style={{ display: "flex", height: "100vh" }}>
        {/* Left: Story editor */}
        <div style={{ flex: 1, overflow: "auto" }}>
          <StoryEditor
            story={story}
            onUpdate={handleUpdate}
            log={log}
            addLog={addLog}
          />
        </div>

        {/* Right: Chat panel */}
        <div style={{ width: 420, borderLeft: "1px solid #e5e5e5", display: "flex", flexDirection: "column" }}>
          <CopilotChat
            labels={{
              title: "AI Assistant",
              initial: "I can see your story. Ask me to edit, rewrite, or search for related content.",
            }}
            instructions={`You are a Reuters newsroom assistant helping edit a news story.

RULES:
- For small headline tweaks: use quick_edit_headline
- For major rewrites: ALWAYS use review_and_apply_draft so the user can approve first
- For finding related content: use search_related
- You can see the current story data — reference it naturally
- Be concise and professional`}
          />
        </div>
      </div>
    </CopilotKit>
  );
}

// ─────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  editorLabel: {
    display: "block",
    fontWeight: 600,
    fontSize: 13,
    marginBottom: 4,
    color: "#374151",
  },
  headlineInput: {
    width: "100%",
    padding: 10,
    fontSize: 18,
    fontWeight: 600,
    border: "1px solid #d1d5db",
    borderRadius: 6,
  },
  bodyTextarea: {
    width: "100%",
    padding: 10,
    fontSize: 14,
    lineHeight: 1.6,
    border: "1px solid #d1d5db",
    borderRadius: 6,
    resize: "vertical" as const,
  },
  reviewCard: {
    border: "1px solid #e5e7eb",
    borderRadius: 8,
    padding: 16,
    margin: "8px 0",
    background: "#fafafa",
  },
  reviewHeader: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  reviewBadge: {
    background: "#dbeafe",
    color: "#1d4ed8",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    fontWeight: "bold",
  },
  reviewField: { marginBottom: 12 },
  reviewLabel: {
    display: "block",
    fontSize: 11,
    fontWeight: 600,
    color: "#6b7280",
    marginBottom: 4,
    textTransform: "uppercase" as const,
  },
  reviewValue: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 6,
    padding: 10,
    fontSize: 14,
    lineHeight: 1.5,
    whiteSpace: "pre-wrap" as const,
  },
  reviewActions: {
    display: "flex",
    gap: 8,
    marginTop: 12,
  },
  reviewBtn: {
    padding: "8px 16px",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontWeight: 500,
    fontSize: 13,
  },
  searchChip: {
    background: "#fef3c7",
    color: "#92400e",
    padding: "8px 12px",
    borderRadius: 8,
    fontSize: 13,
    margin: "4px 0",
  },
};

/*
 * TRY THESE PROMPTS:
 *
 *   1. "What story am I editing?"
 *      → AI reads page context and describes the AAPL story
 *
 *   2. "Make the headline shorter"
 *      → AI calls quick_edit_headline (no approval needed)
 *
 *   3. "Rewrite the story in a more formal Reuters style"
 *      → AI calls review_and_apply_draft (shows review card, waits for approval)
 *
 *   4. "Find related stories about Apple earnings"
 *      → AI calls search_related (shows search progress chip)
 *
 *   5. "Rewrite and add a paragraph about market reaction"
 *      → AI calls review_and_apply_draft with new content
 *      → Click "Refine" and say "make it shorter"
 *      → AI regenerates and shows another review card
 *
 * HOW THIS MAPS TO REUTERS:
 *
 *   This example                     Reuters production
 *   ─────────────────────────────────────────────────────
 *   CopilotKit provider         →   Inside ReutersAssistantAI
 *   CopilotChat                 →   Custom chat UI in assistant-v2
 *   useCopilotReadable          →   externalContext prop (page context)
 *   useCopilotAction            →   useChatAction hook
 *   renderAndWait               →   useAgentInterrupt + useSkillInterrupt
 *   render (progress chips)     →   MCPExecutionSummary + SkillCallChip
 *   In-memory story state       →   Redux store + LEON editor
 *   localhost backend           →   LangGraph MCP orchestrator + MCP skills
 */
