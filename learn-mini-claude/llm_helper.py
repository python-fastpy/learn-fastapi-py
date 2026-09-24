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

_ASSET_ID = os.getenv("ORCHESTRATOR_ASSET_ID", "209485")
_PREFIX = f"a{_ASSET_ID}"

# Deployment suffixes. The full LLM profile key is f"a{asset}-{suffix}",
# e.g. "a209485-gpt-4-1-2025-04-14" -- which is what the orchestrator
# provisions per asset. Only models provisioned for YOUR asset will work;
# everything else 401s.
MODELS = {
    "gpt-4-1": "gpt-4-1-2025-04-14",
    "gpt-4o": "gpt-4o-2024-08-06",
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
    # NOT the generic cognitiveservices scope -- the TR orchestrator has its
    # own Azure AD app registration, and the wrong scope yields a token that
    # authenticates fine but is rejected with 401 at the orchestrator.
    scope = os.getenv(
        "LEON_ORCHESTRATOR_RESOURCE",
        "api://db568b5e-3e0e-4457-afea-32b03c6888ef/.default",
    )
    _cached_token = cred.get_token(scope).token
    return _cached_token


def get_llm(model: str = "gpt-4-1", temperature: float = 0.05) -> AzureChatOpenAI:
    """Return AzureChatOpenAI wired to TR Orchestrator.

    The deployment path is unusual -- it nests the bare deployment name
    under the full profile key:
        {profile_key}/deployments/{deployment}
    which resolves to
        /openai/deployments/a209485-gpt-4-1-2025-04-14/deployments/gpt-4-1-2025-04-14/chat/completions
    Every other arrangement returns 404 or 401.
    """
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
            "x-tr-chat-profile-name": os.getenv("ORCHESTRATOR_CHAT_PROFILE", f"{_PREFIX}-raia-nonprod"),
            "x-tr-user-sensitivity": "blind",
            "x-tr-userid": os.getenv("ORCHESTRATOR_USER_ID", "Reuters-Assistant"),
            "x-tr-sessionid": "learn-mini-claude",
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
    print("[3] Testing gpt-4-1 ...")
    try:
        llm = get_llm(model="gpt-4-1")
        response = await llm.ainvoke([{"role": "user", "content": "Say hello in one sentence."}])
        print(f"    Response: {response.content}\n")
    except Exception as e:
        print(f"    FAILED: {e}\n")
        return

    print("All good — llm_helper is working.")


if __name__ == "__main__":
    asyncio.run(_test())
