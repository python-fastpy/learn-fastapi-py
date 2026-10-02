"""A real LLM connector -- raw HTTP, no SDK wrapper.

Every other piece of this project is built from scratch, with nothing
hidden behind a framework -- the model call underneath lesson 08 is raw
HTTP too, for the same reason. The only non-trivial part is the Azure AD
token; everything else is just `requests.post(url, headers=..., json=...)`.

Usage:
    from llm_client import call_llm
    message = call_llm(messages, tools=TOOL_SCHEMAS)
    # -> the raw "message" dict from choices[0].message: has "content"
    #    and/or "tool_calls", exactly as the wire response shaped it

Run directly to test the connection:
    uv run python llm_client.py

Requires .env with the same TR Orchestrator credentials as learn-mcp:
ORCHESTRATOR_ENDPOINT, LEON_ORCHESTRATOR_API_KEY, LEON_ORCHESTRATOR_TENANT_ID,
LEON_ORCHESTRATOR_CLIENT_ID, LEON_ORCHESTRATOR_CLIENT_SECRET.
"""

import os
from functools import cache

import requests
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

load_dotenv()

ASSET_ID = "209289"
DEPLOYMENT = "gpt-4o-2024-08-06"
URL = (
    f"https://llmorch-ha.int.thomsonreuters.com/openai/deployments/a{ASSET_ID}-{DEPLOYMENT}"
    f"/deployments/{DEPLOYMENT}/chat/completions?api-version=2025-01-01-preview"
)


@cache
def _token() -> str:
    """Azure AD token for the orchestrator. Cached -- fetched once per process."""
    cred = ClientSecretCredential(
        tenant_id=os.environ["LEON_ORCHESTRATOR_TENANT_ID"],
        client_id=os.environ["LEON_ORCHESTRATOR_CLIENT_ID"],
        client_secret=os.environ["LEON_ORCHESTRATOR_CLIENT_SECRET"],
    )
    scope = os.getenv("LEON_ORCHESTRATOR_RESOURCE", "https://cognitiveservices.azure.com/.default")
    return cred.get_token(scope).token


def _headers() -> dict:
    api_key = os.environ["LEON_ORCHESTRATOR_API_KEY"]
    return {
        "api-key": api_key,
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
        "x-tr-chat-profile-name": f"a{ASSET_ID}-Lynx-Editor-Online-NonProd",
        "x-tr-user-sensitivity": "blind",
        "x-tr-userid": "Lynx-Editor-Online",
        "x-tr-sessionid": "learn-agents",
        "x-tr-asset-id": ASSET_ID,
        "x-tr-authorization": "abc",
        "x-tr-llm-profile-key": f"a{ASSET_ID}-{DEPLOYMENT}",
    }


def call_llm(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """POSTs the conversation (+ optional tool schemas) and returns the raw
    `message` dict the model produced -- `content`, or `tool_calls`, or both."""
    payload: dict = {"messages": messages}
    if tools:
        payload["tools"] = tools
    response = requests.post(URL, headers=_headers(), json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]


if __name__ == "__main__":
    print("=== LLM client connection test ===\n")
    if not os.getenv("LEON_ORCHESTRATOR_API_KEY"):
        print("MISSING: LEON_ORCHESTRATOR_API_KEY not set. Create .env from .env.example")
    else:
        message = call_llm([{"role": "user", "content": "Say hello in one short sentence."}])
        print("model replied:", message["content"])
        print("\nAll good -- llm_client is working.")
