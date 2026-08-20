# CopilotKit — Working React Examples

Simple, runnable examples showing how CopilotKit works under the hood.
Each example builds on the previous one.

---

## Table of Contents

1. [Basic Chat — Just Send & Receive Messages](#1-basic-chat)
2. [Reading Page Context — Send Data to the AI](#2-reading-page-context)
3. [Chat Actions — Let AI Call Frontend Functions](#3-chat-actions)
4. [Agent Interrupts — AI Asks User a Question Mid-Flow](#4-agent-interrupts)
5. [Generative UI — Show Custom UI While AI Works](#5-generative-ui)
6. [Skill Calls — Track Tool Executions](#6-skill-calls)
7. [Session Management — Save & Load Conversations](#7-session-management)
8. [File Upload — Send Files to AI](#8-file-upload)
9. [Full Working App — Everything Together](#9-full-working-app)
10. [How Reuters Wraps Each Concept](#10-reuters-wrapping)

---

## 1. Basic Chat

The simplest CopilotKit app — a chat box that sends messages to an AI backend.

```tsx
// App.tsx — Wrap your app with CopilotKit provider
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

function App() {
  return (
    // Step 1: Wrap with CopilotKit — tell it where the backend is
    <CopilotKit url="http://localhost:8000/copilotkit">
      {/* Step 2: Drop in the chat UI */}
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
2. CopilotKit sends it to `http://localhost:8000/copilotkit` as a GraphQL request
3. Backend processes it and streams back the response via SSE
4. CopilotKit renders the streamed response in real time

**Reuters equivalent:**
```tsx
// Instead of CopilotChat, LEON uses ReutersAssistantAI which wraps CopilotKit internally
import { ReutersAssistantAI } from '@reuters/assistant-v2';

<ReutersAssistantAI
  tenantId="leon-shubham"
  jwtToken={token}
  environment="qa"
/>
// This creates CopilotKit internally + adds sessions, MCP, skills, etc.
```

---

## 2. Reading Page Context

Send application data to the AI so it knows what the user is looking at.

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import { useCopilotReadable } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';

// A component that shows a news story
function StoryEditor({ story }) {
  // Tell CopilotKit about the current story
  // This data is sent with EVERY message to the AI
  useCopilotReadable({
    description: "The news story the user is currently editing",
    value: {
      headline: story.headline,
      slug: story.slug,
      body: story.body,
      language: story.language,
    },
  });

  return (
    <div>
      <h1>{story.headline}</h1>
      <p>{story.body}</p>
    </div>
  );
}

function App() {
  const story = { headline: "Markets Rally", slug: "MARKETS-RALLY", body: "..." };

  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <StoryEditor story={story} />
      <CopilotChat />
    </CopilotKit>
  );
}
```

**What happens:**
1. `useCopilotReadable` registers data in CopilotKit's context
2. When user sends a message, CopilotKit includes this data in the request
3. The AI can now say "I see you're editing the Markets Rally story..."

**Reuters equivalent:**
```tsx
// LEON builds page context in reuter-ai-assistant-v2-page-context.tsx
// and passes it as externalContext prop:
<ReutersAssistantAI
  externalContext={JSON.stringify({
    storyId: "abc123",
    headline: "Markets Rally",
    ric: "AAPL.O",
  })}
/>
// The backend extracts this from the request and passes it to the LLM
```

---

## 3. Chat Actions

Let the AI call functions in your frontend. Think of these as "tools" the AI can use.

```tsx
import { useCopilotAction } from '@copilotkit/react-core';

function StoryEditor({ story, onInsertDraft }) {
  // Register an action the AI can call
  useCopilotAction({
    name: "insert_draft",
    description: "Insert a generated draft into the story editor",
    parameters: [
      {
        name: "content",
        type: "string",
        description: "The draft text to insert",
        required: true,
      },
      {
        name: "position",
        type: "string",
        description: "Where to insert: 'beginning', 'end', or 'replace'",
        enum: ["beginning", "end", "replace"],
        required: true,
      },
    ],
    handler: async ({ content, position }) => {
      // This runs in the browser when the AI decides to call it
      console.log(`Inserting draft at ${position}:`, content);
      onInsertDraft(content, position);
      return "Draft inserted successfully";
    },
  });

  return <div>{story.body}</div>;
}
```

**What happens:**
1. `useCopilotAction` tells the backend "the frontend has a tool called insert_draft"
2. If the user says "Write a paragraph about earnings and add it to my story"
3. The AI generates content AND calls `insert_draft` with the text
4. The `handler` runs in the browser, inserting the text into the editor

**Reuters equivalent:**
```tsx
// Reuters wraps this in useChatAction():
import { useChatAction } from '@reuters/assistant-v2';

useChatAction({
  name: "insert_draft",
  description: "Insert draft into LEON editor",
  parameters: [...],
  handler: async ({ content, position }) => {
    // LEON-specific: calls Redux actions to update the editor
    dispatch(insertDraftAction(content, position));
    return "Draft inserted";
  },
});
```

---

## 4. Agent Interrupts

The AI pauses mid-execution to ask the user something, then continues with their answer.

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import { useCopilotAction } from '@copilotkit/react-core';
import { useState } from 'react';

function DraftReviewer() {
  const [showReview, setShowReview] = useState(false);
  const [draft, setDraft] = useState("");
  const [resolveCallback, setResolveCallback] = useState(null);

  // This action renders custom UI and waits for user input
  useCopilotAction({
    name: "review_draft",
    description: "Show a draft to the user for review",
    parameters: [
      { name: "content", type: "string", description: "Draft content" },
    ],
    // Instead of a handler, use renderAndWait — it shows UI and pauses
    renderAndWait: ({ args, resolve, status }) => {
      if (status === "complete") {
        return <p>Review submitted!</p>;
      }

      return (
        <div className="review-card">
          <h3>Review This Draft</h3>
          <div className="draft-content">{args.content}</div>
          <div className="actions">
            <button onClick={() => resolve("approved")}>
              Approve
            </button>
            <button onClick={() => resolve("rejected")}>
              Reject
            </button>
            <button onClick={() => {
              const feedback = prompt("What changes?");
              resolve(`refine: ${feedback}`);
            }}>
              Refine
            </button>
          </div>
        </div>
      );
    },
  });

  return null; // UI is rendered by CopilotKit when action fires
}
```

**What happens:**
1. User says "Write me a news buzz for AAPL"
2. AI generates a draft and calls `review_draft` action
3. CopilotKit renders the review card in the chat
4. Execution PAUSES — the AI waits
5. User clicks "Approve" → `resolve("approved")` is called
6. The AI receives "approved" and continues (e.g., formats and finalizes)

**This is the core of the Reuters interrupt system!**

**Reuters equivalent:**
```tsx
// Reuters uses useAgentInterrupt + useSkillInterrupt hooks:
import { useAgentInterrupt } from '@reuters/assistant-v2';

useAgentInterrupt({
  // Called when backend sends a LangGraphInterruptEvent
  handler: (interrupt) => {
    // interrupt.resolve("approved")  — resume with visible message
    // interrupt.resolveWithoutSendingMessage("approved")  — resume silently
  },
  // OR use render to show custom UI:
  render: (interrupt) => (
    <BuzzReviewCard
      content={interrupt.data.content}
      onApprove={() => interrupt.resolve("approved")}
      onRefine={(msg) => interrupt.resolve(`refine: ${msg}`)}
    />
  ),
});
```

---

## 5. Generative UI

Show different UI as a tool runs through its stages (loading → executing → done).

```tsx
import { useCopilotAction } from '@copilotkit/react-core';

function SearchTool() {
  useCopilotAction({
    name: "search_archive",
    description: "Search the Reuters text archive",
    parameters: [
      { name: "query", type: "string", description: "Search query" },
    ],
    // render shows UI at each stage of execution
    render: ({ status, args, result }) => {
      // Stage 1: Tool is about to run
      if (status === "inProgress") {
        return (
          <div className="search-chip loading">
            🔍 Searching for "{args.query}"...
          </div>
        );
      }

      // Stage 2: Tool is running
      if (status === "executing") {
        return (
          <div className="search-chip executing">
            ⏳ Processing results...
          </div>
        );
      }

      // Stage 3: Tool finished
      if (status === "complete") {
        return (
          <div className="search-chip done">
            ✅ Found {result.count} results for "{args.query}"
            <ul>
              {result.items.map(item => (
                <li key={item.id}>{item.title}</li>
              ))}
            </ul>
          </div>
        );
      }
    },
    handler: async ({ query }) => {
      const response = await fetch(`/api/search?q=${query}`);
      return response.json();
    },
  });

  return null;
}
```

**What happens:**
1. AI decides to search → `render` shows "Searching for..."
2. API call starts → `render` shows "Processing..."
3. API call finishes → `render` shows results list
4. User sees a live progress chip in the chat, not just plain text

**Reuters equivalent:**
```tsx
// Reuters shows MCP execution summaries and skill call chips:
// MCPExecutionSummary — shows which MCP servers were used
// SkillCallChip — shows live status of each tool call
// These are built into @reuters/assistant-v2 automatically
```

---

## 6. Skill Calls

Track which backend tools (skills) are being called in real time.

```tsx
import { useState } from 'react';

// In Reuters, skill calls come from the backend MCP orchestrator
// The frontend tracks them via the useSkillCalls hook

function SkillTracker() {
  const [skillCalls, setSkillCalls] = useState([]);

  // This is how @reuters/assistant-v2 tracks skill executions:
  // (simplified version of what useSkillCalls does internally)
  const handleSkillCall = (skillCall) => {
    setSkillCalls(prev => {
      const existing = prev.find(s => s.id === skillCall.id);
      if (existing) {
        // Update existing (status changed)
        return prev.map(s => s.id === skillCall.id ? skillCall : s);
      }
      return [...prev, skillCall];
    });
  };

  return (
    <div className="skill-tracker">
      {skillCalls.map(skill => (
        <div key={skill.id} className={`skill-chip ${skill.status}`}>
          <span className="skill-name">{skill.toolName}</span>
          <span className="skill-status">
            {skill.status === 'running' && '⏳'}
            {skill.status === 'completed' && '✅'}
            {skill.status === 'failed' && '❌'}
          </span>
          <span className="skill-server">{skill.serverName}</span>
        </div>
      ))}
    </div>
  );
}

// In ReutersAssistantAI, you pass a callback:
<ReutersAssistantAI
  onSkillCallReceived={(skillCall) => {
    console.log(`Tool ${skillCall.toolName} is ${skillCall.status}`);
  }}
/>
```

---

## 7. Session Management

Save conversations and load them later.

```tsx
import { useState, useEffect } from 'react';

// Simplified version of what @reuters/assistant-v2 does with useSessionAPI

function SessionManager({ backendUrl, headers }) {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);

  // Load session list
  const loadSessions = async () => {
    const res = await fetch(`${backendUrl}/api/v1/sessions`, { headers });
    const data = await res.json();
    setSessions(data.sessions);
  };

  // Create new session
  const createSession = async () => {
    const newId = crypto.randomUUID();
    setActiveSessionId(newId);
    // Session is auto-created on first message
    return newId;
  };

  // Switch to existing session
  const switchSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    // CopilotKit re-initializes with the session's message history
  };

  // Delete session
  const deleteSession = async (sessionId) => {
    await fetch(`${backendUrl}/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
      headers,
    });
    setSessions(prev => prev.filter(s => s.id !== sessionId));
  };

  return (
    <div className="session-panel">
      <button onClick={createSession}>New Chat</button>
      {sessions.map(session => (
        <div
          key={session.id}
          className={session.id === activeSessionId ? 'active' : ''}
          onClick={() => switchSession(session.id)}
        >
          <span>{session.title || 'Untitled'}</span>
          <small>{new Date(session.updated_at).toLocaleDateString()}</small>
          <button onClick={(e) => {
            e.stopPropagation();
            deleteSession(session.id);
          }}>🗑</button>
        </div>
      ))}
    </div>
  );
}
```

**Reuters equivalent:**
```tsx
// Built into ReutersAssistantAI when showHistory={true}
<ReutersAssistantAI
  showHistory={true}
  customHistoryComponents={{
    NewChatButton: CustomNewChatButton,    // Custom "New Chat" button
    HistoryToggle: CustomHistoryToggle,    // Custom toggle button
    HistoryPanel: CustomHistoryPanel,      // Custom session list
  }}
/>
```

---

## 8. File Upload

Let users send files to the AI.

```tsx
import { useState, useRef } from 'react';

function FileUpload({ backendUrl, headers }) {
  const [files, setFiles] = useState([]);
  const fileInputRef = useRef(null);

  const uploadFile = async (file) => {
    // Validate
    if (file.size > 20 * 1024 * 1024) {
      alert("File too large (max 20MB)");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${backendUrl}/api/copilotkit/upload`, {
      method: 'POST',
      headers: { Authorization: headers.Authorization },
      body: formData,
    });

    const data = await res.json();
    // Backend converts file to markdown and returns metadata
    setFiles(prev => [...prev, {
      id: data.file_id,
      name: file.name,
      markdown: data.markdown_content,  // Backend converts PDF/Word → markdown
    }]);
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.png,.jpg"
        onChange={(e) => uploadFile(e.target.files[0])}
      />
      <div className="file-list">
        {files.map(f => (
          <div key={f.id} className="file-chip">
            📄 {f.name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Reuters equivalent:**
```tsx
<ReutersAssistantAI
  fileUploadEnabled={true}
  // Max 5 files, 20MB each, 100MB total per session
  // Supports: PDF, Word, text, images
/>
```

---

## 9. Full Working App

Everything wired together in one app.

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';
import { useCopilotReadable, useCopilotAction } from '@copilotkit/react-core';
import { useState } from 'react';
import '@copilotkit/react-ui/styles.css';

// The main editor component with AI integration
function NewsEditor() {
  const [story, setStory] = useState({
    headline: "Tech Giants Report Strong Q2",
    body: "Leading technology companies reported...",
    ric: "AAPL.O",
  });

  // 1. Send page context to AI
  useCopilotReadable({
    description: "Current story being edited",
    value: story,
  });

  // 2. Let AI insert drafts
  useCopilotAction({
    name: "update_story",
    description: "Update the story headline or body",
    parameters: [
      { name: "headline", type: "string", description: "New headline" },
      { name: "body", type: "string", description: "New body text" },
    ],
    handler: async ({ headline, body }) => {
      setStory(prev => ({
        ...prev,
        ...(headline && { headline }),
        ...(body && { body }),
      }));
      return "Story updated";
    },
  });

  // 3. Let AI show a review card (interrupt pattern)
  useCopilotAction({
    name: "review_draft",
    description: "Show draft for user review before applying",
    parameters: [
      { name: "draft", type: "string", description: "Draft to review" },
    ],
    renderAndWait: ({ args, resolve, status }) => {
      if (status === "complete") return <p>✅ Review complete</p>;
      return (
        <div style={{ border: '1px solid #ccc', padding: 16, borderRadius: 8 }}>
          <h4>Review Draft</h4>
          <p style={{ whiteSpace: 'pre-wrap' }}>{args.draft}</p>
          <button onClick={() => resolve("approved")}
                  style={{ marginRight: 8, background: '#22c55e', color: '#fff', padding: '8px 16px' }}>
            Approve
          </button>
          <button onClick={() => resolve("rejected")}
                  style={{ background: '#ef4444', color: '#fff', padding: '8px 16px' }}>
            Reject
          </button>
        </div>
      );
    },
  });

  return (
    <div style={{ padding: 24 }}>
      <h1>{story.headline}</h1>
      <p>{story.body}</p>
      <small>RIC: {story.ric}</small>
    </div>
  );
}

// The app with CopilotKit wrapping everything
export default function App() {
  return (
    <CopilotKit url="http://localhost:8000/copilotkit">
      <div style={{ display: 'flex', height: '100vh' }}>
        {/* Left: Editor */}
        <div style={{ flex: 1 }}>
          <NewsEditor />
        </div>
        {/* Right: Chat panel */}
        <div style={{ width: 400, borderLeft: '1px solid #eee' }}>
          <CopilotChat
            labels={{ title: "AI Assistant" }}
            instructions="You are a Reuters newsroom assistant. Help the user edit their story."
          />
        </div>
      </div>
    </CopilotKit>
  );
}
```

**Try it:**
1. User types: "What story am I editing?" → AI reads the page context and responds
2. User types: "Rewrite the headline to be more concise" → AI calls `update_story`
3. User types: "Draft a new lead paragraph and show me first" → AI calls `review_draft`, user approves, then AI calls `update_story`

---

## 10. How Reuters Wraps Each Concept

Quick reference showing CopilotKit → Reuters mapping:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CopilotKit (Foundation)                      │
│                                                                 │
│  CopilotKit provider      ──→  Wrapped inside ReutersAssistantAI│
│  CopilotChat               ──→  Custom chat UI in assistant-v2  │
│  useCopilotReadable        ──→  externalContext prop            │
│  useCopilotAction          ──→  useChatAction hook              │
│  useCopilotChat            ──→  useChat hook                    │
│  renderAndWait (interrupts)──→  useAgentInterrupt hook          │
│  Message streaming (SSE)   ──→  + MCP metadata interception     │
│  GraphQL protocol          ──→  copilotkit_rest.py on backend   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                @reuters/assistant-v2 (Adds)                     │
│                                                                 │
│  Session management (DynamoDB)                                  │
│  MCP server badges                                              │
│  Skill call tracking chips                                      │
│  Skill interrupt UI (buzz review, RIC selection, etc.)          │
│  File upload with markdown conversion                           │
│  Progress tracking via WebSocket                                │
│  Permission-based skill filtering                               │
│  Tenant isolation (X-Tenant-ID header)                          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                      LEON (Consumer)                            │
│                                                                 │
│  Provides JWT token, user email                                 │
│  Builds page context (story/alert data)                         │
│  Renders custom interrupt components (per event type)           │
│  Filters skills by user rights                                  │
│  Handles "Create Draft" / "Insert" actions via Redux            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### The Data Flow in One Picture

```
User types "Write a buzz for AAPL"
    │
    ▼
CopilotKit builds request:
    {
      messages: [{role: "user", content: "Write a buzz for AAPL"}],
      properties: {                              ← from useCopilotReadable
        externalContext: { ric: "AAPL.O", ... }
      },
      frontend: {                                ← from useCopilotAction
        actions: ["insert_draft", "review_draft"]
      }
    }
    │
    ▼
POST /copilotkit/agent/reuters_assistant
    │
    ▼
Backend (copilotkit_rest.py):
    1. Parse request, extract messages + context
    2. Get/create session from DynamoDB
    3. Send to LangGraph MCP orchestrator
    │
    ▼
Orchestrator:
    1. Selects "generate_news_buzz" tool
    2. Calls story-drafting MCP server
    3. Gets draft back
    4. Calls interrupt() → checkpoint to DynamoDB
    │
    ▼
SSE streams interrupt to frontend:
    data: { "type": "LangGraphInterruptEvent", "data": { "content": "..." } }
    │
    ▼
CopilotKit triggers interrupt handler
    │
    ▼
Reuters renders BuzzReviewCard
    │
    ▼
User clicks "Approve"
    │
    ▼
resolve("approved") → CopilotKit sends back to backend
    │
    ▼
Backend resumes from DynamoDB checkpoint
    │
    ▼
Orchestrator continues → final response streamed back
    │
    ▼
Chat shows: "Here's your approved AAPL buzz: ..."
```
