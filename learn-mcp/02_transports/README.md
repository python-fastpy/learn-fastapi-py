# Lesson 02 — Transports

One greet server, reached two ways. Four files, one job each — no command-line
flags, and no file re-runs itself.

| File | Job |
|------|-----|
| `greet_server.py` | The server: `greet` + `/health`. Run it directly and it speaks **stdio**. |
| `http_server.py` | Imports that same `mcp` and serves it over **HTTP** on `:8765`. |
| `stdio_client.py` | **Part A** — starts `greet_server.py` as a child process and talks over stdin/stdout. |
| `http_client.py` | **Part B** — connects by URL, checks `/health`, sends per-tenant headers. |

## Run

```bash
# Part A -- stdio. Starts the server itself; read this one first.
uv run python 02_transports/stdio_client.py

# Part B -- HTTP. Starts http_server.py if it isn't already running.
uv run python 02_transports/http_client.py
```

To see the HTTP split properly, run the server yourself in one terminal and
the client in another (or in two others at once — stdio cannot do that):

```bash
uv run python 02_transports/http_server.py     # terminal 1, keeps running
uv run python 02_transports/http_client.py     # terminal 2, step 5 changes
```

`stdio_client.py` holds the conceptual map: in-memory vs stdio vs HTTP, the
part A message flow, and the stdio/HTTP comparison table. `http_client.py`
holds the part B flow and how this maps to ALB + ECS in production.
