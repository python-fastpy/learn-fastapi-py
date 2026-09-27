"""LLM helper — connects to TR Orchestrator (Azure OpenAI).

Usage:
    from llm_helper import get_llm
    llm = get_llm()                  # default: gpt-4o
    llm = get_llm(model="gpt-4-1")   # specific model

Run directly to test the connection:
    uv run python llm_helper.py

EXPECTED OUTPUT:
  === LLM Helper Connection Test ===

  [1] endpoint  https://llmorch-ha.int.thomsonreuters.com
  [2] token     eyJ0eXAiOiJKV1QiLCJh...
  [3] gpt-4o    Hello! How can I help you today?

  All good — llm_helper is working.

Requires .env with: ORCHESTRATOR_ENDPOINT, LEON_ORCHESTRATOR_API_KEY,
LEON_ORCHESTRATOR_TENANT_ID, LEON_ORCHESTRATOR_CLIENT_ID,
LEON_ORCHESTRATOR_CLIENT_SECRET
"""

import asyncio
import os
from functools import cache

from azure.identity import ClientSecretCredential
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

ASSET_ID = os.getenv("ORCHESTRATOR_ASSET_ID", "209289")

MODELS = {
    "gpt-4o": "gpt-4o-2024-08-06",
    "gpt-4-1": "gpt-4.1-2025-04-14",
    "gpt-5-4": "gpt-5-4-2026-03-05",
    "o4-mini": "o4-mini-2025-04-16",
}


@cache
def _token() -> str:
    """Azure AD token for the orchestrator. Cached — fetched once per process."""
    cred = ClientSecretCredential(
        tenant_id=os.environ["LEON_ORCHESTRATOR_TENANT_ID"],
        client_id=os.environ["LEON_ORCHESTRATOR_CLIENT_ID"],
        client_secret=os.environ["LEON_ORCHESTRATOR_CLIENT_SECRET"],
    )
    scope = os.getenv("LEON_ORCHESTRATOR_RESOURCE", "https://cognitiveservices.azure.com/.default")
    return cred.get_token(scope).token


def get_llm(model: str = "gpt-4o", temperature: float = 0.05) -> AzureChatOpenAI:
    """Return AzureChatOpenAI wired to TR Orchestrator."""
    if model not in MODELS:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODELS)}")

    deployment = MODELS[model]
    profile_key = f"a{ASSET_ID}-{deployment}"
    api_key = os.environ["LEON_ORCHESTRATOR_API_KEY"]

    return AzureChatOpenAI(
        azure_endpoint=os.environ["ORCHESTRATOR_ENDPOINT"],
        azure_deployment=f"{profile_key}/deployments/{deployment}",
        api_version="2025-01-01-preview",
        api_key=api_key,
        temperature=temperature,
        default_headers={
            "Authorization": f"Bearer {_token()}",
            "api-key": api_key,
            "x-tr-chat-profile-name": os.getenv(
                "ORCHESTRATOR_CHAT_PROFILE", f"a{ASSET_ID}-Lynx-Editor-Online-NonProd"
            ),
            "x-tr-user-sensitivity": "blind",
            "x-tr-userid": "Lynx-Editor-Online",
            "x-tr-sessionid": "learn-mcp",
            "x-tr-asset-id": ASSET_ID,
            "x-tr-authorization": "abc",
            "x-tr-llm-profile-key": profile_key,
        },
    )


# ============================================================================
# Run directly to test the connection: uv run python llm_helper.py
# ============================================================================

async def _test() -> None:
    print("=== LLM Helper Connection Test ===\n")

    endpoint = os.getenv("ORCHESTRATOR_ENDPOINT")
    if not endpoint:
        print("MISSING: ORCHESTRATOR_ENDPOINT not set. Create .env from .env.example")
        return

    print(f"[1] endpoint  {endpoint}")
    try:
        print(f"[2] token     {_token()[:20]}...")
        reply = await get_llm().ainvoke([{"role": "user", "content": "Say hello in one sentence."}])
        print(f"[3] gpt-4o    {reply.content}")
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    print("\nAll good — llm_helper is working.")


if __name__ == "__main__":
    asyncio.run(_test())
