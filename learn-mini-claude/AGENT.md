# Project instructions

Everything in this file is appended to the agent's system prompt on every
run — the same idea as Claude Code's `CLAUDE.md`. Edit it, restart, done.

Delete the lines below and write your own. They're deliberately specific
so you can tell whether the file is actually being read: ask the agent to
create a script and see if it obeys them.

## Code style

- Python scripts must start with a one-line `#` comment saying what they do.
- Prefer standard library over third-party packages.
- No emoji in generated files.

## Working habits

- Before editing a file you haven't read this session, read it first.
- After writing a script, say in one line what it does and how to run it.
- If you can't do something (blocked tool, missing file), say so plainly
  rather than substituting something you can do.
