"""LLM helper — connects to TR Orchestrator (Azure OpenAI).

Usage:
    from llm_helper import get_llm
    llm = get_llm()                   # default: gpt-4o
    llm = get_llm(model="gpt-4-1")   # specific model

Requires .env with: ORCHESTRATOR_ENDPOINT, LEON_ORCHESTRATOR_API_KEY,
LEON_ORCHESTRATOR_TENANT_ID, LEON_ORCHESTRATOR_CLIENT_ID,
LEON_ORCHESTRATOR_CLIENT_SECRET
"""

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
