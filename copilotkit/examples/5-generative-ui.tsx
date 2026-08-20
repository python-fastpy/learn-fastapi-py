/**
 * Example 5: Generative UI (Status-Based Rendering)
 * --------------------------------------------------
 * Show different UI as a tool runs through its stages:
 *   inProgress → executing → complete
 *
 * Unlike renderAndWait (interrupts), this does NOT pause.
 * It just shows progress UI while the handler runs.
 *
 * Reuters uses this for:
 *   - MCP execution summaries (which servers were called)
 *   - Skill call chips (live status of each tool)
 *   - Progress indicators during long operations
 */

import React from "react";
import { CopilotKit, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function ToolActions() {
  // ACTION: Search with live progress UI
  useCopilotAction({
    name: "search_archive",
    description: "Search the Reuters text archive for articles matching a query.",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "Search keywords",
        required: true,
      },
      {
        name: "date_range",
        type: "string",
        description: "Date range: 'today', 'week', 'month', 'year'",
        enum: ["today", "week", "month", "year"],
      },
    ],

    // render (NOT renderAndWait) — shows UI but does NOT pause execution
    render: ({ status, args, result }) => {
      // Stage 1: Tool call detected, about to run
      if (status === "inProgress") {
        return (
          <div style={chipStyle("#fef3c7", "#92400e")}>
            <Spinner /> Searching archive for "{args.query}"...
          </div>
        );
      }

      // Stage 2: Handler is executing
      if (status === "executing") {
        return (
          <div style={chipStyle("#dbeafe", "#1e40af")}>
            <Spinner /> Processing results...
          </div>
        );
      }

      // Stage 3: Handler finished, show results
      if (status === "complete" && result) {
        const data = typeof result === "string" ? JSON.parse(result) : result;
        return (
          <div style={chipStyle("#dcfce7", "#166534")}>
            <span>Found {data.count} articles</span>
            <div style={{ marginTop: 8, fontSize: 13 }}>
              {data.articles?.slice(0, 3).map((a: any, i: number) => (
                <div key={i} style={{ padding: "4px 0", borderBottom: "1px solid #bbf7d0" }}>
                  {a.headline} <span style={{ color: "#6b7280" }}>({a.date})</span>
                </div>
              ))}
              {data.count > 3 && (
                <div style={{ color: "#6b7280", marginTop: 4 }}>
                  ... and {data.count - 3} more
                </div>
              )}
            </div>
          </div>
        );
      }

      return null;
    },

    // The actual handler — runs while render shows progress
    handler: async ({ query, date_range }) => {
      // Simulate API call
      await new Promise((r) => setTimeout(r, 2000));
      return JSON.stringify({
        count: 15,
        articles: [
          { headline: "Markets close higher on tech rally", date: "2026-08-20" },
          { headline: "Fed signals potential rate cut", date: "2026-08-19" },
          { headline: "Oil prices surge on supply concerns", date: "2026-08-18" },
        ],
      });
    },
  });

  // ACTION: Generate with multi-step progress
  useCopilotAction({
    name: "generate_buzz",
    description: "Generate a Reuters BUZZ article for a company.",
    parameters: [
      {
        name: "company",
        type: "string",
        description: "Company name",
        required: true,
      },
    ],
    render: ({ status, args, result }) => {
      if (status === "inProgress") {
        return (
          <div style={chipStyle("#fae8ff", "#86198f")}>
            <Spinner /> Preparing buzz for {args.company}...
          </div>
        );
      }
      if (status === "executing") {
        return (
          <div style={chipStyle("#fae8ff", "#86198f")}>
            <Spinner /> Fetching financial data and generating...
          </div>
        );
      }
      if (status === "complete") {
        return (
          <div style={chipStyle("#dcfce7", "#166534")}>
            Buzz generated for {args.company}
          </div>
        );
      }
      return null;
    },
    handler: async ({ company }) => {
      await new Promise((r) => setTimeout(r, 3000));
      return `BUZZ - ${company} beats Q2 expectations...`;
    },
  });

  return null;
}

// Simple spinner component
function Spinner() {
  return (
    <span
      style={{
        display: "inline-block",
        width: 14,
        height: 14,
        border: "2px solid currentColor",
        borderTopColor: "transparent",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
        marginRight: 6,
        verticalAlign: "middle",
      }}
    />
  );
}

function chipStyle(bg: string, color: string): React.CSSProperties {
  return {
    display: "inline-flex",
    alignItems: "center",
    background: bg,
    color: color,
    padding: "8px 12px",
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 500,
    margin: "4px 0",
    width: "100%",
    flexDirection: "column",
    alignItems: "flex-start",
  };
}

export default function GenerativeUIApp() {
  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
      <div style={{ display: "flex", height: "100vh" }}>
        <div style={{ flex: 1, padding: 32 }}>
          <h1>Generative UI</h1>
          <p>Try these in the chat:</p>
          <ul>
            <li>"Search the archive for Apple earnings" → shows search progress chip</li>
            <li>"Generate a buzz for Microsoft" → shows generation progress</li>
          </ul>
          <p style={{ color: "#6b7280", marginTop: 16 }}>
            Watch the chip change from yellow (loading) → blue (executing) → green (done)
          </p>
        </div>
        <div style={{ width: 420, borderLeft: "1px solid #e5e5e5" }}>
          <ToolActions />
          <CopilotChat
            labels={{ title: "AI Assistant" }}
            instructions="You are a Reuters assistant. Use the available tools when asked to search or generate content."
          />
        </div>
      </div>
    </CopilotKit>
  );
}

/*
 * render vs renderAndWait:
 *
 *   render:          Shows UI while handler runs. Does NOT pause.
 *                    Use for: progress indicators, loading states, result display
 *
 *   renderAndWait:   Shows UI and PAUSES until resolve() is called.
 *                    Use for: approvals, selections, user input mid-flow
 *
 * REUTERS EQUIVALENT:
 *   - MCPExecutionSummary component shows which MCP servers were used
 *   - SkillCallChip shows live status per tool call (loading → done)
 *   - ProgressTracker shows step-by-step progress for multi-step workflows
 *   These are built into @reuters/assistant-v2 automatically via:
 *     useMCPInterceptor, useSkillCalls, useProgressTracking hooks
 */
