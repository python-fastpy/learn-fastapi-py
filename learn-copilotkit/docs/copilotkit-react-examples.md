# CopilotKit — React Examples Reference

Code examples showing how CopilotKit works under the hood. Each example builds on the previous one.

> **Runnable versions:** The `frontend/src/examples/` directory contains working TSX files for examples 1-6.
> Run them with `cd frontend && npm install && npm run dev`.

---

## Table of Contents

1. [Basic Chat — Send & Receive Messages](#1-basic-chat)
2. [Reading Page Context — Send Data to the AI](#2-reading-page-context)
3. [Chat Actions — Let AI Call Frontend Functions](#3-chat-actions)
4. [Agent Interrupts — AI Asks User a Question Mid-Flow](#4-agent-interrupts)
5. [Generative UI — Show Custom UI While AI Works](#5-generative-ui)
6. [Skill Calls — Track Tool Executions](#6-skill-calls)
7. [Session Management — Save & Load Conversations](#7-session-management)
8. [File Upload — Send Files to AI](#8-file-upload)
9. [Full Working App — Everything Together](#9-full-working-app)
10. [CopilotKit → App Mapping](#10-mapping)

---

## 1. Basic Chat

The simplest CopilotKit app — a chat box that sends messages to an AI backend.

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

function App() {
  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <CopilotChat
        labels={{ title: "My AI Assistant" }}
        instructions="You are a helpful assistant."
      />
    </CopilotKit>
  );
}
```

**What happens:**
1. User types a message
2. CopilotKit sends it to `http://localhost:8000/copilotkit`
3. Backend streams response via SSE
4. CopilotKit renders streamed response in real time

> **USED IN REUTERS:** LEON uses `<ReutersAssistantAI>` which wraps CopilotKit + CopilotChat internally.
> See: `lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2.component.tsx`

---

## 2. Reading Page Context

Send application data to the AI so it knows what the user is looking at.

```tsx
import { useCopilotReadable } from '@copilotkit/react-core';

function StoryEditor({ story }) {
  useCopilotReadable({
    description: "The story the user is currently editing",
    value: {
      headline: story.headline,
      slug: story.slug,
      body: story.body,
    },
  });

  return <div><h1>{story.headline}</h1><p>{story.body}</p></div>;
}
```

**What happens:**
1. `useCopilotReadable` registers data in CopilotKit's context
2. When user sends a message, CopilotKit includes this data in the request
3. The AI can reference "I see you're editing the Markets Rally story..."

> **USED IN REUTERS:** Page context is built from the Redux store in `reuter-ai-assistant-v2-page-context.tsx`
> and passed as the `externalContext` prop to `ReutersAssistantAI`.
> The backend extracts it and injects it into the orchestrator's system prompt.

---

## 3. Chat Actions

Let the AI call functions in your frontend. These are "tools" the UI exposes to the agent.

```tsx
import { useCopilotAction } from '@copilotkit/react-core';

function StoryEditor({ story, onInsertDraft }) {
  useCopilotAction({
    name: "insert_draft",
    description: "Insert a generated draft into the story editor",
    parameters: [
      { name: "content", type: "string", description: "Draft text", required: true },
      { name: "position", type: "string", enum: ["beginning", "end", "replace"], required: true },
    ],
    handler: async ({ content, position }) => {
      onInsertDraft(content, position);
      return "Draft inserted successfully";
    },
  });

  return <div>{story.body}</div>;
}
```

**What happens:**
1. `useCopilotAction` tells the backend "the frontend has a tool called insert_draft"
2. If the user says "Write a paragraph about earnings and add it"
3. The AI generates content AND calls `insert_draft` with the text
4. The handler runs in the browser

> **USED IN REUTERS:** `use-raia-action-handler.ts` registers "create_draft" and "insert_into_story" frontend actions.
> `@reuters/assistant-v2` wraps this in `useChatAction()`.

---

## 4. Agent Interrupts

The AI pauses mid-execution to ask the user something, then continues with their answer.

```tsx
useCopilotAction({
  name: "review_draft",
  description: "Show a draft to the user for review",
  parameters: [
    { name: "content", type: "string", description: "Draft content" },
  ],
  renderAndWait: ({ args, resolve, status }) => {
    if (status === "complete") return <p>Review submitted!</p>;
    return (
      <div>
        <h3>Review This Draft</h3>
        <p>{args.content}</p>
        <button onClick={() => resolve("approved")}>Approve</button>
        <button onClick={() => resolve("rejected")}>Reject</button>
        <button onClick={() => {
          const feedback = prompt("What changes?");
          resolve(`refine: ${feedback}`);
        }}>Refine</button>
      </div>
    );
  },
});
```

**What happens:**
1. AI generates a draft and calls `review_draft`
2. CopilotKit renders the review card in the chat
3. Execution PAUSES — the AI waits
4. User clicks "Approve" → `resolve("approved")` fires
5. The AI receives "approved" and continues

> **USED IN REUTERS:** This is the core of the interrupt system:
> - `reuter-ai-assistant-skills-interrupt.component.tsx` renders interrupt UI by EventType
> - `useAgentInterrupt` + `useSkillInterrupt` hooks handle the lifecycle
> - Backend uses LangGraph `interrupt()` + DynamoDB checkpoints
> - Event types: `NEWS_BUZZ.REVIEW`, `SPOT_STORY_REVIEW`, `URGENT_BUILDER_REVIEW`, etc.

---

## 5. Generative UI

Show different UI as a tool runs through its stages (loading → executing → done).

```tsx
useCopilotAction({
  name: "search_archive",
  description: "Search the text archive",
  parameters: [
    { name: "query", type: "string", description: "Search query" },
  ],
  render: ({ status, args, result }) => {
    if (status === "inProgress") return <div>Searching for "{args.query}"...</div>;
    if (status === "executing") return <div>Processing results...</div>;
    if (status === "complete") return <div>Found {result.count} results</div>;
  },
  handler: async ({ query }) => {
    const response = await fetch(`/api/search?q=${query}`);
    return response.json();
  },
});
```

**Key difference:** `render` shows UI but does NOT pause. `renderAndWait` shows UI and PAUSES.

> **USED IN REUTERS:** This pattern powers:
> - `mcp-execution-summary.tsx` — shows which MCP servers were called
> - `skill-call-chip.tsx` — live status chip per tool call (loading → done)
> - `ProgressTracker.tsx` — step-by-step progress display

---

## 6. Skill Calls

Track which backend tools (skills) are being called in real time.

```tsx
function SkillTracker() {
  const [skillCalls, setSkillCalls] = useState([]);

  const handleSkillCall = (skillCall) => {
    setSkillCalls(prev => {
      const existing = prev.find(s => s.id === skillCall.id);
      if (existing) return prev.map(s => s.id === skillCall.id ? skillCall : s);
      return [...prev, skillCall];
    });
  };

  return (
    <div>
      {skillCalls.map(skill => (
        <div key={skill.id} className={skill.status}>
          {skill.toolName} — {skill.status} — {skill.serverName}
        </div>
      ))}
    </div>
  );
}
```

> **USED IN REUTERS:** `useSkillCalls` hook in `@reuters/assistant-v2` tracks skill executions.
> `onSkillCallReceived` callback on `ReutersAssistantAI` provides the data.

---

## 7. Session Management

Save conversations and load them later.

```tsx
function SessionManager({ backendUrl, headers }) {
  const [sessions, setSessions] = useState([]);

  const loadSessions = async () => {
    const res = await fetch(`${backendUrl}/api/v1/sessions`, { headers });
    setSessions((await res.json()).sessions);
  };

  const createSession = () => crypto.randomUUID();

  const deleteSession = async (sessionId) => {
    await fetch(`${backendUrl}/api/v1/sessions/${sessionId}`, {
      method: 'DELETE', headers,
    });
  };

  return (
    <div>
      <button onClick={createSession}>New Chat</button>
      {sessions.map(s => (
        <div key={s.id} onClick={() => switchSession(s.id)}>
          {s.title} <button onClick={() => deleteSession(s.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}
```

> **USED IN REUTERS:** Built into `ReutersAssistantAI` when `showHistory={true}`.
> `useSessionAPI()` and `useSessionManager()` hooks in `@reuters/assistant-v2`.
> Sessions stored in DynamoDB `session-history` table with 30-day TTL.

---

## 8. File Upload

Let users send files to the AI.

```tsx
const uploadFile = async (file) => {
  if (file.size > 20 * 1024 * 1024) return alert("File too large (max 20MB)");

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${backendUrl}/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  const data = await res.json();
  // Backend converts file to markdown and returns metadata
};
```

> **USED IN REUTERS:** `ReutersAssistantAI` with `fileUploadEnabled={true}`.
> `useFileManager()` hook handles upload queue and state.
> Max 5 files, 20MB each, 100MB total per session. Supports PDF, Word, text, images.

---

## 9. Full Working App

See `frontend/src/examples/6-full-app.tsx` for a complete working example that combines:
- Page context (AI knows what story you're editing)
- Chat actions (AI can update headline, body, insert text)
- Interrupts (AI shows draft review card before applying changes)
- Generative UI (live progress chips during operations)

---

## 10. CopilotKit → App Mapping

```
┌─────────────────────────────────────────────────────────────────┐
│                    CopilotKit (Foundation)                      │
│                                                                 │
│  CopilotKit provider      ──→  Your app wrapper component      │
│  CopilotChat               ──→  Custom chat UI                 │
│  useCopilotReadable        ──→  Page/app context injection     │
│  useCopilotAction          ──→  Domain-specific frontend tools │
│  useCopilotChat            ──→  Chat state management          │
│  renderAndWait (interrupts)──→  Review/approval workflows      │
│  render (generative UI)    ──→  Progress indicators            │
│  Message streaming (SSE)   ──→  + metadata interception        │
└─────────────────────────────────────────────────────────────────┘
```

> **USED IN REUTERS:** The three-layer mapping:
> - **CopilotKit** → foundation (hooks, streaming, actions)
> - **@reuters/assistant-v2** → wrapper (sessions, MCP, skills, interrupts, files)
> - **LEON** → consumer (JWT, page context, Redux, user rights, interrupt renderers)
