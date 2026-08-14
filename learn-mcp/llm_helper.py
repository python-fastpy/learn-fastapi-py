"""LLM helper — connects to TR Orchestrator (Azure OpenAI).

Usage:
    from llm_helper import get_llm
    llm = get_llm()                   # default: gpt-4o
    llm = get_llm(model="gpt-4-1")   # specific model

Run directly to test the connection:
    uv run python llm_helper.py

EXPECTED OUTPUT:
  === LLM Helper Connection Test ===

  [1] Loading .env ...
      ORCHESTRATOR_ENDPOINT = https://llmorch-ha.int.thomsonreuters.com

  [2] Acquiring Azure AD token ...
      Token acquired (first 20 chars): eyJ0eXAiOiJKV1QiLCJh...

  [3] Testing gpt-4o ...
      Response: Hello! How can I help you today?

  All good — llm_helper is working.

Requires .env with: ORCHESTRATOR_ENDPOINT, LEON_ORCHESTRATOR_API_KEY,
LEON_ORCHESTRATOR_TENANT_ID, LEON_ORCHESTRATOR_CLIENT_ID,
LEON_ORCHESTRATOR_CLIENT_SECRET
"""

import asyncio
import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from langchain_openai import AzureChatOpenAI

load_dotenv()

_ASSET_ID = os.getenv("ORCHESTRATOR_ASSET_ID", "209289")
_PREFIX = f"a{_ASSET_ID}"

MODELS = {
    "gpt-4o": "gpt-4o-2024-08-06",
    "gpt-4-1": "gpt-4.1-2025-04-14",
    "gpt-5-4": "gpt-5-4-2026-03-05",
    "o4-mini": "o4-mini-2025-04-16",
}

_cached_token: str | None = None


def _get_token() -> str:
    global _cached_token
    if _cached_token:
        return _cached_token
    cred = ClientSecretCredential(
        tenant_id=os.environ["LEON_ORCHESTRATOR_TENANT_ID"],
        client_id=os.environ["LEON_ORCHESTRATOR_CLIENT_ID"],
        client_secret=os.environ["LEON_ORCHESTRATOR_CLIENT_SECRET"],
    )
    scope = os.getenv("LEON_ORCHESTRATOR_RESOURCE", "https://cognitiveservices.azure.com/.default")
    _cached_token = cred.get_token(scope).token
    return _cached_token


def get_llm(model: str = "gpt-4o", temperature: float = 0.05) -> AzureChatOpenAI:
    """Return AzureChatOpenAI wired to TR Orchestrator."""
    deployment = MODELS.get(model)
    if not deployment:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODELS)}")

    profile_key = f"{_PREFIX}-{deployment}"
    token = _get_token()
    api_key = os.environ["LEON_ORCHESTRATOR_API_KEY"]

    return AzureChatOpenAI(
        azure_endpoint=os.environ["ORCHESTRATOR_ENDPOINT"],
        azure_deployment=f"{profile_key}/deployments/{deployment}",
        api_version="2025-01-01-preview",
        api_key=api_key,
        temperature=temperature,
        default_headers={
            "Authorization": f"Bearer {token}",
            "api-key": api_key,
            "x-tr-chat-profile-name": os.getenv("ORCHESTRATOR_CHAT_PROFILE", f"{_PREFIX}-Lynx-Editor-Online-NonProd"),
            "x-tr-user-sensitivity": "blind",
            "x-tr-userid": "Lynx-Editor-Online",
            "x-tr-sessionid": "learn-mcp",
            "x-tr-asset-id": _ASSET_ID,
            "x-tr-authorization": "abc",
            "x-tr-llm-profile-key": profile_key,
        },
    )


# ============================================================================
# Run directly to test the connection: uv run python llm_helper.py
# ============================================================================

async def _test():
    print("=== LLM Helper Connection Test ===\n")

    # Step 1: Check .env loaded
    print("[1] Loading .env ...")
    endpoint = os.getenv("ORCHESTRATOR_ENDPOINT")
    if not endpoint:
        print("    MISSING: ORCHESTRATOR_ENDPOINT not set. Create .env from .env.example")
        return
    print(f"    ORCHESTRATOR_ENDPOINT = {endpoint}\n")

    # Step 2: Get Azure AD token
    print("[2] Acquiring Azure AD token ...")
    try:
        token = _get_token()
        print(f"    Token acquired (first 20 chars): {token[:20]}...\n")
    except Exception as e:
        print(f"    FAILED: {e}\n")
        return

    # Step 3: Call LLM
    print("[3] Testing gpt-4o ...")
    try:
        llm = get_llm(model="gpt-4o")
        response = await llm.ainvoke([{"role": "user", "content": "Say hello in one sentence."}])
        print(f"    Response: {response.content}\n")
    except Exception as e:
        print(f"    FAILED: {e}\n")
        return

    print("All good — llm_helper is working.")


if __name__ == "__main__":
    asyncio.run(_test())
