# 1-Week Python + FastAPI + MCP + LangGraph Preparation Guide

**Goal:** Go from foundations to production-ready, covering every file in the `learn-fastapi-py` repo.

**Daily structure:** ~5 hours total (including lunch). Morning session (3 slots), lunch break, afternoon session (3 slots). Each slot is 40 minutes (30 min study + 10 min practice/review).

**How to use each file:** Every `.py` file has 3 sections — read the Content section first, code along, then use the Cheat Sheet for review and the Detailed Reference for deeper understanding.

---

## Day 1 (Mon) — Python Fundamentals

_Build the language foundation. Everything else depends on this._

### Morning (9:00 - 11:00)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 9:00 - 9:40 | `python/01-data-types.py` | Numbers, strings, lists, dicts, sets, tuples, type conversions | Create a contact book using dicts and lists |
| 9:40 - 10:20 | `python/02-functions.py` | Args, kwargs, closures, generators, lambda, decorators | Write a function that accepts `*args` and `**kwargs`, returns a generator |
| 10:20 - 11:00 | `python/03-decorators.py` | Function/class decorators, chaining, `functools.wraps` | Build a `@timer` and `@retry` decorator, chain them |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 11:30 - 12:10 | `python/04-annotations.py` | Type hints, Optional, Union, TypeVar, Protocol, generics | Add type annotations to all functions from morning |
| 12:10 - 12:50 | `python/05-oops.py` | Classes, inheritance, MRO, dunder methods, ABC, dataclasses | Create a `Shape` ABC with `Circle` and `Rectangle` subclasses |
| 12:50 - 13:30 | `python/06-exception-handling.py` | try/except, custom exceptions, context managers, ExceptionGroup | Write a custom `ValidationError` with context manager for file cleanup |

**End of day check:** Can you write a decorated class with type hints, custom exceptions, and a context manager from scratch?

---

## Day 2 (Tue) — Python Advanced + Pydantic

_Async thinking and data validation — the two pillars of FastAPI._

### Morning (9:00 - 11:00)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 9:00 - 9:40 | `python/07-file-handling.py` | File I/O, CSV, JSON, pathlib, tempfile, shutil | Read a JSON config, modify it, write it back using pathlib |
| 9:40 - 10:20 | `python/08-typeddict.py` | TypedDict, NotRequired, Required, nested, inheritance, JSON patterns | Model an API response as nested TypedDicts |
| 10:20 - 11:00 | `python/09-pydantic-basics.py` | BaseModel basics, Field, validation | Create models for a user registration form with validation |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 11:30 - 12:10 | `python/10-async-await.py` | asyncio, gather, create_task, Semaphore, Lock, Event, Queue, TaskGroup | Write an async script that fetches 5 URLs concurrently with a semaphore limit of 2 |
| 12:10 - 12:50 | `fastapi/pydantic.py` | BaseModel, Field validation, validators, nested models, response_model, model_dump | Build a nested order/line-item model with custom validators |
| 12:50 - 13:30 | Review & connect | Re-read cheat sheets from Day 1 + Day 2 | Write a Pydantic model that uses TypedDict, custom validators, and `model_dump` |

**End of day check:** Can you define a complex Pydantic model with nested types, validators, and serialize it? Can you write async code with `gather` and semaphores?

---

## Day 3 (Wed) — FastAPI Core

_Build real APIs. This is the heart of the week._

### Morning (9:00 - 11:00)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 9:00 - 9:40 | `fastapi/crud.py` | CRUD operations, Body/Query/Path/Header/Cookie/Form/File params, Depends, Annotated | Build a complete CRUD API for a todo app |
| 9:40 - 10:20 | `fastapi/routes.py` | APIRouter, response types, error handling, Enum paths, catch-all routes | Split the todo app into routers (`/api/v1/todos`, `/api/v1/users`) |
| 10:20 - 11:00 | `fastapi/headers-auth-request-anatomy.py` | Headers, auth patterns, request anatomy | Add API key auth via headers to your todo app |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 11:30 - 12:10 | `fastapi/session.py` | Lifespan, cookie/Redis/JWT sessions, Depends chains, Request/Response | Add JWT session management to your todo app |
| 12:10 - 12:50 | `fastapi/middleware-cors-caching.py` | CORS, GZip, custom middleware, Cache-Control, ETag, rate limiting | Add CORS + rate limiting middleware to your todo app |
| 12:50 - 13:30 | `fastapi/async-await.py` | async/await in FastAPI, gather, create_task, httpx | Add an endpoint that calls 3 external APIs concurrently |

**End of day check:** Can you build a FastAPI app with routers, auth, middleware, CORS, and async external calls? Test every endpoint with curl.

---

## Day 4 (Thu) — FastAPI Advanced + AWS Foundations

_Production patterns: lifespan, deployment targets._

### Morning (9:00 - 11:00)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 9:00 - 9:40 | `fastapi/lifespan.py` | Lifespan events, startup/shutdown, shared state | Add a lifespan that initializes a DB connection pool and cleans up on shutdown |
| 9:40 - 10:20 | `aws/01-overview-and-app.py` | AWS overview, core services, regions, CLI | Set up AWS CLI, run basic commands |
| 10:20 - 11:00 | `aws/02-vpc.py` | VPC, subnets, security groups, routing | Understand the networking layer your ECS tasks run in |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 11:30 - 12:10 | `aws/03-s3.py` | S3 buckets, objects, policies, presigned URLs | Create a bucket, upload/download with boto3 |
| 12:10 - 12:50 | `aws/05-lambda.py` | Lambda functions, triggers, layers, cold starts | Deploy a simple Lambda that processes S3 events |
| 12:50 - 13:30 | `aws/06-api-gateway.py` | API Gateway, REST vs HTTP APIs, stages, throttling | Create an API Gateway -> Lambda integration |

**End of day check:** Can you explain VPC -> API Gateway -> Lambda -> S3 data flow? Can you set up each piece?

---

## Day 5 (Fri) — AWS Production Stack

_The infra behind your FastAPI apps in production._

### Morning (9:00 - 11:00)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 9:00 - 9:40 | `aws/07-ecr.py` | ECR, Docker images, push/pull | Build a FastAPI Docker image, push to ECR |
| 9:40 - 10:20 | `aws/08-ecs-fargate.py` | ECS, Fargate, task definitions, services | Deploy your FastAPI app as a Fargate task |
| 10:20 - 11:00 | `aws/09-alb.py` | ALB, target groups, health checks, path routing | Route traffic to your ECS service via ALB |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Practice |
|------|------|--------|----------|
| 11:30 - 12:10 | `aws/13-secrets-manager.py` | Secrets Manager, rotation, SDK access | Inject secrets into your ECS task as env vars |
| 12:10 - 12:50 | `aws/15-dynamodb.py` | DynamoDB, tables, GSI, queries, boto3 | Create a table, CRUD with boto3 (this is how LangGraph checkpointer stores state) |
| 12:50 - 13:30 | `aws/10-cloudwatch.py` | CloudWatch logs, metrics, alarms, dashboards | Set up log groups + alarms for your ECS service |

**End of day check:** Can you trace the full deployment path: code -> Docker -> ECR -> ECS Fargate -> ALB -> CloudWatch? Can you use DynamoDB and Secrets Manager?

---

## Day 6 (Sat) — MCP (Model Context Protocol)

_How AI skills are built and connected. Follow the lesson numbers in order._

### Morning (9:00 - 11:00)

| Time | File | Topics | Production Equivalent |
|------|------|--------|-----------------------|
| 9:00 - 9:40 | `learn-mcp/01_hello_mcp_server.py` | Create a minimal MCP server with `@mcp.tool()` | Every skill's `main.py` |
| 9:40 - 10:20 | `learn-mcp/02_mcp_client.py` | Connect to a server, call tools, inspect results | Backend's `mcp_protocol.py` |
| 10:20 - 11:00 | `learn-mcp/04_resources_and_prompts.py` | All three primitives: tool, resource, prompt | Skills expose tools; workflows as resources |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Production Equivalent |
|------|------|--------|-----------------------|
| 11:30 - 12:10 | `learn-mcp/04_structured_content.py` | Return `structuredContent` + `_meta` with timing | Interrupt payloads + `skill_call_extras` |
| 12:10 - 12:50 | `learn-mcp/05_hitl_interrupt.py` | Interrupt/resume with continuation tokens | HITL cycle: interrupt -> checkpoint -> resume |
| 12:50 - 13:30 | `learn-mcp/06_http_transport.py` | MCP over Streamable HTTP (production transport) | ECS Fargate behind ALB, path-based routing |

**Bonus files if time permits:** `07_llm_tool_server.py` through `15_mcp_to_mcp.py` for advanced patterns (multi-server, workflows, LangGraph integration).

**End of day check:** Can you build an MCP server with tools, connect to it with a client, implement HITL interrupts, and run it over HTTP transport?

---

## Day 7 (Sun) — LangGraph + Full Integration

_Orchestration: the brain that ties MCP skills together._

### Morning (9:00 - 11:00)

| Time | File | Topics | Production Equivalent |
|------|------|--------|-----------------------|
| 9:00 - 9:40 | `learn-langgraph/01_state_basics.py` | StateGraph, TypedDict state, nodes, edges, compile | `langgraph_mcp_orchestrator.py` state |
| 9:40 - 10:20 | `learn-langgraph/02_conditional_routing.py` | `add_conditional_edges`, router functions, branching | Execution strategies: none/single/sequential/parallel |
| 10:20 - 11:00 | `learn-langgraph/03_tool_calling_agent.py` | Bind tools to LLM, ToolNode, agent loop | Core agent loop that decides which MCP tool to call |

### Lunch Break (11:00 - 11:30)

### Afternoon (11:30 - 13:30)

| Time | File | Topics | Production Equivalent |
|------|------|--------|-----------------------|
| 11:30 - 12:10 | `learn-langgraph/04_human_in_the_loop.py` | `interrupt()`, MemorySaver, resume from checkpoint | DynamoDB checkpointer + interrupt/resume cycle |
| 12:10 - 12:50 | `learn-langgraph/05_mcp_plus_langgraph.py` | LangGraph agent discovering and calling MCP tools | Full pattern: LangGraph orchestrator -> MCP skills |
| 12:50 - 13:30 | `learn-langgraph/06_streaming_sse.py` | Stream graph execution via FastAPI SSE endpoint | `/api/v1/chat` SSE streaming response |

**Bonus files if time permits:** `07_agent_loop.py` through `13_orchestrator.py` for subgraphs, error handling, and full orchestrator patterns.

**End of day check:** Can you build a LangGraph agent that discovers MCP tools, calls them with HITL interrupts, and streams results via SSE?

---

## Full Production Flow (What You've Learned)

After completing the week, you can trace the entire production request lifecycle:

```
User sends message
  -> FastAPI endpoint receives POST         (Day 3: crud.py, routes.py)
  -> JWT auth validates session             (Day 3: session.py, headers-auth)
  -> Middleware logs + rate limits           (Day 3: middleware-cors-caching.py)
  -> LangGraph orchestrator invoked         (Day 7: state_basics, conditional_routing)
  -> LLM decides which tool to call         (Day 7: tool_calling_agent)
  -> MCP client connects to skill server    (Day 6: mcp_client, http_transport)
  -> Skill executes, may interrupt for HITL (Day 6: hitl_interrupt, structured_content)
  -> LangGraph checkpoints to DynamoDB      (Day 5: dynamodb + Day 7: human_in_the_loop)
  -> Response streamed back via SSE         (Day 7: streaming_sse)
  -> Running on ECS Fargate behind ALB      (Day 5: ecr, ecs-fargate, alb)
  -> Secrets from Secrets Manager           (Day 5: secrets-manager)
  -> Logs to CloudWatch                     (Day 5: cloudwatch)
```

---

## Tips

- **Don't just read** — run every file with `uv run python <file>`. Modify the examples. Break things.
- **Use curl** — test every FastAPI endpoint. The Detailed Reference sections have curl examples.
- **Connect to production** — after each file, check the "Reuters Prod Equivalent" column and find the matching code in the actual codebase.
- **Review before bed** — spend 10 minutes re-reading the day's cheat sheets.
- **If you're stuck on a file for more than 20 minutes**, move on and come back to it. Progress > perfection.
