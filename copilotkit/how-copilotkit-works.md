# How CopilotKit Works in the Reuters AI Assistant

## What is CopilotKit?

CopilotKit is an open-source React framework for building AI-powered chat interfaces. It provides the underlying chat UI, message streaming, agent communication, and action system that powers the Reuters AI Assistant frontend.

In our architecture, CopilotKit is **never used directly by LEON**. Instead, the `@reuters/assistant-v2` npm package wraps CopilotKit with Reuters-specific business logic (MCP, sessions, skills, interrupts), and LEON imports from that package.

```
LEON (reuter-ai-assistant-v2.component.tsx)
    └── @reuters/assistant-v2 (npm package v0.1.47)
            └── CopilotKit (@copilotkit/react-core, react-ui, etc.)
```

## CopilotKit Packages Used

The `@reuters/assistant-v2` package depends on these CopilotKit peer dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `@copilotkit/react-core` | ^1.10.1 | Core hooks: `useCopilotChat`, `useCopilotAction`, message context |
| `@copilotkit/react-ui` | ^1.10.1 | UI components: `AssistantMessage`, `InputProps`, `ComponentsMap` |
| `@copilotkit/react-textarea` | ^1.10.1 | Enhanced textarea with AI features |
| `@copilotkit/runtime-client-gql` | ^1.10.1 | GraphQL client for CopilotKit backend protocol |
| `@copilotkit/shared` | (transitive) | Shared types: `Parameter`, `FrontendAction` |

---

## Architecture: Three-Layer Stack

### Layer 1: LEON (Consumer)

**File:** `lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2.component.tsx`

LEON mounts the `ReutersAssistantAI` component and passes configuration:

```tsx
import { ReutersAssistantAI, createConfig } from '@reuters/assistant-v2';

const config = createConfig({
  tenantId: 'leon-shubham',
  userId: userEmail,
  jwtToken: authToken,
  environment: 'local',        // local | development | qa | uat | staging | production
});

<ReutersAssistantAI
  tenantId="leon-shubham"
  userId={userEmail}
  jwtToken={authToken}
  environment="local"
  mcpEnabled={true}
  showMCPSummary={true}
  showSkillCalls={true}
  showHistory={true}
  fileUploadEnabled={true}
  onMCPMetadataReceived={handleMetadata}
  onSkillCallReceived={handleSkillCall}
  renderSkillInterrupt={renderInterrupt}
  allowedSkills={allowedSkills}
/>
```

### Layer 2: @reuters/assistant-v2 (Wrapper)

The npm package wraps CopilotKit hooks and components with Reuters-specific logic:

- Adds session management (create, load, switch, delete)
- Adds MCP metadata interception and server badge display
- Adds skill call tracking and live execution chips
- Adds human-in-the-loop interrupt handling
- Adds file upload with markdown conversion
- Adds progress tracking via WebSocket

### Layer 3: CopilotKit (Foundation)

CopilotKit provides the core chat framework:

- Message state management and streaming
- GraphQL/SSE communication protocol
- Agent communication with interrupt support
- Frontend action system (tools the UI exposes to the LLM)
- Generative UI (rendering UI during tool execution)

---

## The Hook Wrapping Pattern

The `@reuters/assistant-v2` package re-exports CopilotKit hooks under Reuters-named wrappers. This adds business logic while keeping the CopilotKit API accessible:

### Chat Hooks

| Reuters Hook | CopilotKit Source | Purpose |
|-------------|-------------------|---------|
| `useChat()` | Wraps `UseCopilotChatOptions` / `UseCopilotChatReturn` from `@copilotkit/react-core` | Core chat functionality (send messages, get responses) |
| `useCopilotChatInternal()` | Returns `UseCopilotChatReturn_c` from `@copilotkit/react-core` | Internal CopilotKit chat state (lower-level access) |
| `useChatMessagesContext()` | Wraps `CopilotMessagesContextParams` from `@copilotkit/react-core` | Access to raw message list and context |

### Action Hooks

| Reuters Hook | CopilotKit Source | Purpose |
|-------------|-------------------|---------|
| `useChatAction()` | Wraps `FrontendAction` from `@copilotkit/react-core` | Register frontend actions the LLM can call |
| `useRemoteAction()` | Uses `Parameter` from `@copilotkit/shared` | Register remote actions with parameter schemas |
| `useGenerativeUIAction()` | Uses `Parameter` from `@copilotkit/shared` | Status-based UI rendering during tool execution |

### Interrupt Hooks

| Reuters Hook | CopilotKit Source | Purpose |
|-------------|-------------------|---------|
| `useAgentInterrupt()` | CopilotKit interrupt mechanism | Handle agent interrupts with `resolve()` / `resolveWithoutSendingMessage()` callbacks |
| `useSkillInterrupt()` | Reuters-specific (builds on agent interrupt) | Handle skill-specific interrupts (draft review, RIC selection, etc.) |

---

## Key CopilotKit Concepts

### 1. Chat Actions (Frontend Actions)

CopilotKit allows the frontend to register "actions" — functions the LLM can invoke. These are essentially tools the UI exposes to the agent.

```typescript
// From @copilotkit/react-core
interface FrontendAction {
  name: string;
  description: string;
  parameters: Parameter[];
  handler: (args: any) => Promise<any>;
}
```

In our system, `useChatAction()` wraps this to register Reuters-specific actions (e.g., "create draft", "insert into story").

### 2. Agent Interrupts

CopilotKit's agent communication supports "interrupts" — the agent can pause execution and ask the user for input before continuing.

```typescript
// The interrupt provides two resolution callbacks:
interface InterruptHandler {
  resolve: (value: any) => void;                    // Resume with a visible message
  resolveWithoutSendingMessage: (value: any) => void; // Resume silently (no chat bubble)
}
```

This is how the human-in-the-loop cycle works:
1. Backend orchestrator hits an interrupt (e.g., "review this draft")
2. LangGraph calls `interrupt()` to checkpoint state to DynamoDB
3. Interrupt payload streams to frontend via SSE
4. Frontend renders the appropriate UI (draft review card, RIC selection, etc.)
5. User responds (approve/refine/reject)
6. Frontend calls `resolve()` with the user's response
7. CopilotKit sends the response back to the backend
8. Backend resumes from the DynamoDB checkpoint

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

### 4. Message Context

CopilotKit maintains a message context that tracks all messages in the conversation:

```typescript
// From @copilotkit/react-core
interface CopilotMessagesContextParams {
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  // ... other context methods
}
```

The `useChatMessagesContext()` hook gives components access to read and manipulate the message list.

### 5. Properties (useCopilotReadable)

CopilotKit's `useCopilotReadable` hook sends application context to the agent. In our system, this is how page context (story data, alert data) reaches the backend:

- LEON builds page context in `reuter-ai-assistant-v2-page-context.tsx`
- This is passed as `externalContext` to the `ReutersAssistantAI` component
- CopilotKit sends it as a `properties` field in GraphQL requests
- Backend extracts it from the request and passes it to the orchestrator

---

## Data Flow: End-to-End

```
User types message in LEON
         │
         ▼
ReutersAssistantAI (assistant-v2 package)
         │
         ▼
CopilotKit useChat() builds GraphQL request
  ┌──────────────────────────────────────────┐
  │  generateCopilotResponse mutation        │
  │  - messages: [{role, content}]           │
  │  - properties: {externalContext, ...}    │
  │  - metaEvents: [{LangGraphInterruptEvent}] (if resuming) │
  │  - frontend.actions: [registered actions]│
  └──────────────────────────────────────────┘
         │
         ▼
Backend: copilotkit_rest.py
  POST /copilotkit/agent/reuters_assistant (legacy GraphQL)
  POST /api/copilotkit (REST)
         │
         ▼
CopilotKitRouter parses request
  - Extracts user message
  - Extracts external context (page context)
  - Checks for interrupt resolution (metaEvents)
  - Gets/creates session from DynamoDB
         │
         ▼
LangGraph MCP Orchestrator (process_message)
  - Analyzes query → selects tools
  - Executes MCP tools on skill servers
  - Streams text deltas back
         │
         ▼
SSE Streaming Response (GraphQL incremental delivery)
  ┌──────────────────────────────────────────┐
  │  Phase 1: Initial payload (empty shell)  │
  │  Phase 2: text_delta events → @stream    │
  │  Phase 3: status, extensions, interrupts │
  └──────────────────────────────────────────┘
         │
         ▼
CopilotKit merges incremental patches
         │
         ▼
ReutersAssistantAI renders message
  - AssistantMessage (markdown rendering)
  - MCP server badges
  - Skill call chips
  - Interrupt UI (if applicable)
```

---

## Backend CopilotKit Endpoint

**File:** `reuters-assistant_backend/src/routers/copilotkit_rest.py`

The backend provides a `CopilotKitRouter` class that handles the CopilotKit protocol:

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/copilotkit/agent/reuters_assistant` | Legacy GraphQL endpoint (backward compat) |
| POST | `/api/copilotkit` | REST chat endpoint |
| POST | `/api/copilotkit/agent/{agent}` | Agent-specific REST endpoint |
| GET | `/api/copilotkit/health` | Health check |
| GET | `/api/copilotkit/info` | Service info |
| POST | `/api/copilotkit/upload` | File upload |
| DELETE | `/api/copilotkit/files/{file_id}` | File deletion |

### Two Protocol Modes

The backend supports both CopilotKit protocol formats:

1. **GraphQL Mode** (legacy) — CopilotKit sends `generateCopilotResponse` mutations with `variables.data.messages`. The backend parses the GraphQL structure, extracts messages, and returns SSE using GraphQL incremental delivery format.

2. **REST Mode** — CopilotKit sends a `CopilotKitRequest` JSON body with `messages`, `model`, `stream`, etc. The backend streams back plain SSE text events.

### CopilotKit Request Model

```python
class CopilotKitRequest(BaseModel):
    messages: list[CopilotKitMessage]
    model: str | None = "gemini-2-5-flash"
    stream: bool | None = True
    temperature: float | None = 0.7
    max_tokens: int | None = 2000
    external_context: str | None = None   # Page context (not stored in DB)
    available_skills: list[str] | None = None
```

### SSE Streaming Protocol

The backend streams responses using GraphQL incremental delivery over SSE:

```
data: {"data": {"generateCopilotResponse": {...}}, "hasNext": true}    ← Initial shell
data: {"incremental": [{"path": [..., "content", 0], "items": ["Hello"]}], "hasNext": true}  ← Text chunks
data: {"incremental": [{"path": [..., "content", 1], "items": [" world"]}], "hasNext": true}
data: {"incremental": [...], "hasNext": true}  ← Extensions, skill calls
data: {"hasNext": false}                        ← Stream complete
```

---

## Interrupt Flow (CopilotKit + LangGraph)

### How Interrupts Bridge Frontend and Backend

1. **Skill tool returns interrupt payload** — The MCP skill tool (e.g., `generate_news_buzz`) returns a review block with `status: "interrupted"`

2. **LangGraph orchestrator calls `interrupt()`** — This checkpoints the entire graph state (tool call, arguments, partial results) to DynamoDB

3. **Backend stores interrupt metadata in session** — `_store_interrupt_state()` saves:
   - `active_interrupt.id` — correlation ID
   - `pending_skill_interrupt` — thread_id, execution_id, step_id, tool_name, continuation_token, original_arguments

4. **SSE streams `LangGraphInterruptEvent` to frontend** — CopilotKit receives the event and calls the registered interrupt handler

5. **Frontend renders interrupt UI** — `reuter-ai-assistant-skills-interrupt.component.tsx` renders the appropriate component based on event type (e.g., `NEWS_BUZZ.REVIEW` → buzz review card)

6. **User responds** — Clicks "Approve", "Refine", or types a message

7. **CopilotKit sends resolution** — Two paths:
   - **Button click**: CopilotKit sends `LangGraphInterruptEvent` in `metaEvents` with a `response` field
   - **Typed message**: Backend detects pending interrupt in session and treats the message as an interrupt response

8. **Backend resumes from checkpoint** — `_resume_from_checkpoint()` loads the DynamoDB checkpoint, continues the LangGraph execution with the user's response

### Resume Detection Logic

```python
# Button click (metaEvent path)
interrupt_resolution = self._extract_interrupt_resolution(meta_events)

# Typed message (chat path)  
if not interrupt_resolution and self._has_pending_interrupt(session):
    interrupt_resolution = self._create_interrupt_resolution(session, user_message)
```

---

## Configuration Factory

The `createConfig()` function produces a configuration object that includes both the main backend URL and a separate CopilotKit URL:

```typescript
import { createConfig } from '@reuters/assistant-v2';

const config = createConfig({
  tenantId: 'leon-shubham',
  userId: 'user@reuters.com',
  jwtToken: authToken,
  environment: 'qa',
});

// Returns:
// {
//   backendUrl: 'https://api.assistant-test.int.thomsonreuters.com',
//   copilotKitUrl: 'https://api.assistant-test.int.thomsonreuters.com/copilotkit',
//   headers: { Authorization, X-Tenant-ID, X-User-ID, X-Application-ID, X-Application-Name },
//   applicationId: 'leon-shubham'
// }
```

The `copilotKitUrl` points to the CopilotKit-specific endpoint on the same backend server — it's the base URL that CopilotKit's internal GraphQL client uses to send chat requests.

### Environment URL Mapping

| Environment | Backend URL |
|-------------|-------------|
| `local` | `http://localhost:8000` |
| `development` | `https://api.assistant-dev.int.thomsonreuters.com` |
| `qa` | `https://api.assistant-test.int.thomsonreuters.com` |
| `uat` | `https://api.assistant-uat.thomsonreuters.com` |
| `staging` | `https://staging-api.reuters.com` |
| `production` | `https://api.assistant.thomsonreuters.com` |

---

## UI Components from CopilotKit

The `@reuters/assistant-v2` package imports these CopilotKit UI component types for customization:

```typescript
// From @copilotkit/react-ui
import type {
  AssistantMessageProps,  // Props for rendering assistant messages
  ButtonProps,            // Props for action buttons
  ComponentsMap,          // Map of overridable UI components
  InputProps,             // Props for the chat input
  MessagesProps,          // Props for the messages container
  RenderMessageProps,     // Props for individual message rendering
  WindowProps,            // Props for the chat window container
  UserMessageProps,       // Props for rendering user messages
  RenderSuggestionsListProps, // Props for suggestion rendering
} from '@copilotkit/react-ui';
```

These allow `ReutersAssistantChat` to accept custom component overrides:

```typescript
interface ReutersAssistantChatProps {
  components?: Partial<ComponentsMap>;  // Override default UI components
  // ... other props
}
```

---

## Summary: Why CopilotKit?

| What CopilotKit Provides | What Reuters Adds On Top |
|--------------------------|--------------------------|
| Chat message state management | Session persistence in DynamoDB |
| GraphQL/SSE streaming protocol | MCP tool execution metadata |
| Frontend action system | Skill call tracking and live chips |
| Agent interrupt mechanism | Human-in-the-loop draft review workflow |
| UI component library | Custom interrupt renderers (buzz review, RIC selection) |
| `useCopilotReadable` for context | Page context injection (story/alert data) |
| Message context hooks | Skill source tracking per message |
| Generative UI actions | MCP execution summary badges |

CopilotKit handles the "how do we build a chat UI that talks to an AI agent" problem. The Reuters layer handles "how do we make that agent a newsroom assistant with MCP skills, multi-tenant sessions, and editorial workflows."
