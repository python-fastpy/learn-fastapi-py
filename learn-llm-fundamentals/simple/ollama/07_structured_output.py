"""07 -- Structured output: get JSON your code can trust
=======================================================

CONCEPT IN ONE LINE:
  Give the model a JSON SCHEMA, then VALIDATE what comes back -- never trust it blindly.
                                                                  (details: simple/13)

   email text ──▶ model + format=SCHEMA ──▶ '{"category": "billing", "priority": 4}'
                                                    │
                                                    ▼
                                    json.loads ─▶ check keys ─▶ check values
                                       │ fail        │ fail        │ fail
                                       └─────────────┴─────────────┴──▶ retry with the error
                                                                         (max 3 tries)
                                                    │ all OK
                                                    ▼
                                         save to DB / return from FastAPI

  format=SCHEMA makes Ollama only allow tokens that fit the schema (constrained decoding),
  so broken JSON is rare -- but VALUES can still be wrong, so you still check.
"""

import json

from ollama_client import chat

SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["billing", "bug", "feature_request"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "summary": {"type": "string"},
    },
    "required": ["category", "priority", "summary"],
}


def check(data):
    """Return an error message, or None if the data is OK."""
    if set(data) != {"category", "priority", "summary"}:
        return f"wrong keys: {sorted(data)}"
    if data["category"] not in ("billing", "bug", "feature_request"):
        return f"bad category: {data['category']}"
    if not isinstance(data["priority"], int) or not 1 <= data["priority"] <= 5:
        return f"bad priority: {data['priority']}"
    return None


def classify(email, tries=3):
    messages = [{"role": "system", "content": "Classify the support email. priority 5 = urgent."},
                {"role": "user", "content": email}]
    for attempt in range(1, tries + 1):
        r = chat(messages, format=SCHEMA, options={"temperature": 0})
        text = r["message"]["content"]
        try:
            data = json.loads(text)
            error = check(data)
        except json.JSONDecodeError as e:
            error = f"not valid JSON: {e}"
        print(f"   try {attempt}: {text}  ->  {'OK' if not error else error}")
        if not error:
            return data
        messages += [r["message"], {"role": "user", "content": f"Fix this error: {error}"}]
    return None                                     # in FastAPI: return HTTP 502


def main():
    emails = [
        "I was charged twice for my subscription this month! Please fix it today.",
        "The export button crashes the app every time I click it.",
        "It would be nice to have a dark mode.",
    ]
    for email in emails:
        print(f"STEP: {email}")
        print("   result:", classify(email), "\n")


if __name__ == "__main__":
    main()

# Try: remove format=SCHEMA and ask for JSON in words only -- watch how often it breaks.
