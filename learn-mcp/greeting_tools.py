"""Shared tools for lessons 10-12.

Not a lesson itself. The same greet/farewell/translate trio was previously
copy-pasted three times (lessons 10, 11, 12) with small accidental drift
between copies (an unused "source" field in one, a dead default argument
in another). Defined once here instead, the way `learn-fastmcp-client`'s
`target_server.py` and `learn-agents`' `tools.py` share their tools.
"""


def greet(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}


def farewell(name: str) -> dict:
    """Say goodbye to someone."""
    return {"message": f"Goodbye, {name}!"}


def translate(text: str, language: str) -> dict:
    """Translate text into another language (simulated)."""
    return {"translated": f"[{language}] {text}"}
