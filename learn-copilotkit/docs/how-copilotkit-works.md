# How CopilotKit Works

> **Note:** This doc explains CopilotKit concepts generically. Reuters-specific references are in callout boxes marked with "USED IN REUTERS".

## What is CopilotKit?

CopilotKit is an open-source React framework for building AI-powered chat interfaces. It provides chat UI, message streaming, agent communication, and an action system.

> **USED IN REUTERS:** LEON never uses CopilotKit directly. The `@reuters/assistant-v2` npm package wraps CopilotKit with Reuters-specific business logic (MCP, sessions, skills, interrupts), and LEON imports from that package.
> ```
> LEON (reuter-ai-assistant-v2.component.tsx)
>     └── @reuters/assistant-v2 (npm package v0.1.47)
>             └── CopilotKit (@copilotkit/react-core, react-ui, etc.)
> ```

## CopilotKit Packages

| Package | Purpose |
|---------|---------|
| `@copilotkit/react-core` | Core hooks: `useCopilotChat`, `useCopilotAction`, message context |
| `@copilotkit/react-ui` | UI components: `CopilotChat`, message renderers |
| `@copilotkit/react-textarea` | Enhanced textarea with AI features |
| `@copilotkit/runtime-client-gql` | GraphQL client for CopilotKit backend protocol |
| `@copilotkit/shared` | Shared types: `Parameter`, `FrontendAction` |

---

## Architecture: Three-Layer Stack

### Layer 1: Your App (Consumer)

Your app mounts the CopilotKit provider and chat UI, passing configuration.

```tsx
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotChat } from '@copilotkit/react-ui';

<CopilotKit url="http://localhost:8000/copilotkit">
  <YourApp />
  <CopilotChat
    labels={{ title: "AI Assistant" }}
    instructions="You are a helpful assistant."
  />
</CopilotKit>
```

> **USED IN REUTERS:** LEON uses `<ReutersAssistantAI>` which wraps this internally.
> See: `lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2.component.tsx`

### Layer 2: Application Wrapper (Optional)

You can wrap CopilotKit hooks and components with your own business logic:

- Add session management
- Add metadata interception
- Add custom interrupt handling
- Add file upload
- Add progress tracking

> **USED IN REUTERS:** The `@reuters/assistant-v2` package is this wrapper layer. It adds session management (DynamoDB), MCP metadata interception, skill call tracking, interrupt handling, file upload, and progress tracking via WebSocket.

### Layer 3: CopilotKit (Foundation)

CopilotKit provides the core chat framework:

- Message state management and streaming
- SSE communication protocol
- Agent communication with interrupt support
- Frontend action system (tools the UI exposes to the LLM)
- Generative UI (rendering UI during tool execution)

---

## Key CopilotKit Concepts

### 1. Chat Actions (Frontend Actions)

CopilotKit allows the frontend to register "actions" — functions the LLM can invoke. These are essentially tools the UI exposes to the agent.

```typescript
interface FrontendAction {
  name: string;
  description: string;
  parameters: Parameter[];
  handler: (args: any) => Promise<any>;
}
```

> **USED IN REUTERS:** `useChatAction()` in `@reuters/assistant-v2` wraps this to register Reuters-specific actions (e.g., "create draft", "insert into story").
> See: `lynx_leon/src/components/reuter-ai-assistant-v2/hooks/use-raia-action-handler.ts`

### 2. Agent Interrupts

CopilotKit's agent communication supports "interrupts" — the agent can pause execution and ask the user for input before continuing.

```typescript
interface InterruptHandler {
  resolve: (value: any) => void;                    // Resume with a visible message
  resolveWithoutSendingMessage: (value: any) => void; // Resume silently
}
```

The interrupt flow:
1. Backend orchestrator hits an interrupt (e.g., "review this draft")
2. Backend checkpoints state
3. Interrupt payload streams to frontend via SSE
4. Frontend renders the appropriate UI (review card, selection, etc.)
5. User responds (approve/refine/reject)
6. Frontend calls `resolve()` with the user's response
7. CopilotKit sends the response back to the backend
8. Backend resumes from checkpoint

> **USED IN REUTERS:** Interrupts power the entire draft review workflow:
> - `reuter-ai-assistant-skills-interrupt.component.tsx` — renders interrupt UI based on EventType
> - `useAgentInterrupt` / `useSkillInterrupt` hooks in `@reuters/assistant-v2`
> - LangGraph `interrupt()` + DynamoDB checkpoints in `langgraph_mcp_orchestrator.py`

### 3. Generative UI Actions

CopilotKit supports rendering UI components during tool execution with status-based rendering:

```typescript
interface GenerativeUIAction {
  name: string;
  parameters: Parameter[];
  render: (props: {
    status: 'inProgress' | 'executing' | 'complete';
    args: any;
    result: any;
  }) => React.ReactNode;
}
```

This allows showing progress indicators, loading states, and final results as tools execute.

> **USED IN REUTERS:** This pattern is used for MCP execution summaries and skill call chips:
> - `mcp-execution-summary.tsx` — shows which MCP servers were called
> - `skill-call-chip.tsx` — live status chip per tool call
> - `ProgressTracker.tsx` — step-by-step progress display

### 4. Message Context

CopilotKit maintains a message context that tracks all messages in the conversation:

```typescript
interface CopilotMessagesContextParams {
  messages: Message[];
  setMessages: (messages: Message[]) => void;
}
```

The `useChatMessagesContext()` hook gives components access to read and manipulate the message list.

### 5. Page Context (useCopilotReadable)

CopilotKit's `useCopilotReadable` hook sends application context to the agent:

```tsx
useCopilotReadable({
  description: "The story the user is editing",
  value: { headline: "...", ric: "AAPL.O", body: "..." },
});
```

This data is automatically included in every chat request.

> **USED IN REUTERS:** Page context flows through three layers:
> - LEON builds page context in `reuter-ai-assistant-v2-page-context.tsx`
> - Passed as `externalContext` to `ReutersAssistantAI`
> - Backend extracts it and passes to the orchestrator's system prompt

---

## Data Flow: End-to-End

```
User types message
         │
         ▼
CopilotKit useChat() builds request
  ┌──────────────────────────────────────────┐
  │  messages: [{role, content}]             │
  │  properties: {externalContext, ...}      │
  │  frontend.actions: [registered actions]  │
  └──────────────────────────────────────────┘
         │
         ▼
Backend receives request
  - Extracts user message
  - Extracts external context (page context)
  - Checks for interrupt resolution
         │
         ▼
LLM Orchestrator
  - Analyzes query → selects tools
  - Executes tools
  - Streams text back
         │
         ▼
SSE Streaming Response
  - Text chunks streamed in real time
  - Interrupt events (if applicable)
         │
         ▼
CopilotKit renders response
  - Streamed text in chat
  - Generative UI components
  - Interrupt cards (if applicable)
```

> **USED IN REUTERS:** The backend uses GraphQL incremental delivery over SSE:
> ```
> data: {"data": {...}, "hasNext": true}        ← Initial shell
> data: {"incremental": [...text_delta...]}      ← Text chunks
> data: {"incremental": [...extensions...]}      ← MCP metadata, skill calls
> data: {"hasNext": false}                       ← Stream complete
> ```
> See: `reuters-assistant_backend/src/routers/copilotkit_rest.py`

---

## Summary: CopilotKit vs App Layer

| CopilotKit Provides | Your App Adds On Top |
|---------------------|---------------------|
| Chat message state management | Session persistence |
| SSE streaming protocol | Custom metadata |
| Frontend action system | Domain-specific tools |
| Agent interrupt mechanism | Custom review workflows |
| UI component library | Custom interrupt renderers |
| `useCopilotReadable` for context | App-specific context injection |
| Message context hooks | Source tracking per message |
| Generative UI actions | Progress indicators |

CopilotKit handles "how do we build a chat UI that talks to an AI agent." Your app layer handles domain-specific logic on top.
