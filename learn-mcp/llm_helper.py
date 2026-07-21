"""Reusable LLM helper -- mirrors the skills repo's TR Orchestrator setup.

Usage in any lesson:
    from llm_helper import get_llm
    llm = get_llm()                       # default: gpt-4o
    llm = get_llm(model="gpt-4-1")       # specific model

Returns a langchain ChatOpenAI (AzureOpenAI-backed) instance ready for
MCP tool functions that need LLM capabilities.

Env vars loaded from .env (same as sphinx_leon-assistant-skills):
    ORCHESTRATOR_ENDPOINT, LEON_ORCHESTRATOR_API_KEY,
    LEON_ORCHESTRATOR_TENANT_ID, LEON_ORCHESTRATOR_CLIENT_ID,
    LEON_ORCHESTRATOR_CLIENT_SECRET, LEON_ORCHESTRATOR_RESOURCE
"""

import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from langchain_openai import AzureChatOpenAI

load_dotenv()

_ASSET_ID = os.getenv("ORCHESTRATOR_ASSET_ID", "209289")
_PREFIX = f"a{_ASSET_ID}"

_DEPLOYMENTS = {
    "gpt-4o": {
        "deployment": f"{_PREFIX}-gpt-4o-2024-08-06/deployments/gpt-4o-2024-08-06",
        "profile_key": f"{_PREFIX}-gpt-4o-2024-08-06",
        "api_version": "2025-01-01-preview",
    },
    "gpt-4-1": {
        "deployment": f"{_PREFIX}-gpt-4-1/deployments/gpt-4-1",
        "profile_key": f"{_PREFIX}-gpt-4-1",
        "api_version": "2025-01-01-preview",
    },
    "o4-mini": {
        "deployment": f"{_PREFIX}-o4-mini-2025-04-16/deployments/o4-mini-2025-04-16",
        "profile_key": f"{_PREFIX}-o4-mini-2025-04-16",
        "api_version": "2024-12-01-preview",
    },
}

_token_cache: dict = {}


def _get_azure_token() -> str:
    """Generate Azure AD token via client credentials (cached)."""
    if "token" in _token_cache:
        return _token_cache["token"]

    credential = ClientSecretCredential(
        tenant_id=os.environ["LEON_ORCHESTRATOR_TENANT_ID"],
        client_id=os.environ["LEON_ORCHESTRATOR_CLIENT_ID"],
        client_secret=os.environ["LEON_ORCHESTRATOR_CLIENT_SECRET"],
    )
    resource = os.getenv(
        "LEON_ORCHESTRATOR_RESOURCE",
        "https://cognitiveservices.azure.com/.default",
    )
    result = credential.get_token(resource)
    _token_cache["token"] = result.token
    return result.token


def get_llm(model: str = "gpt-4o", temperature: float = 0.05) -> AzureChatOpenAI:
    """Return a LangChain AzureChatOpenAI wired to the TR Orchestrator.

    Args:
        model: One of "gpt-4o", "gpt-4-1", "o4-mini".
        temperature: Sampling temperature (ignored for reasoning models).

    Returns:
        AzureChatOpenAI instance ready for use in MCP tool functions.
    """
    endpoint = os.environ["ORCHESTRATOR_ENDPOINT"]
    api_key = os.environ["LEON_ORCHESTRATOR_API_KEY"]
    token = _get_azure_token()

    dep = _DEPLOYMENTS.get(model)
    if not dep:
        raise ValueError(
            f"Unknown model '{model}'. Choose from: {list(_DEPLOYMENTS)}"
        )

    default_headers = {
        "Authorization": f"Bearer {token}",
        "api-key": api_key,
        "x-tr-chat-profile-name": os.getenv(
            "ORCHESTRATOR_CHAT_PROFILE",
            f"{_PREFIX}-Lynx-Editor-Online-NonProd",
        ),
        "x-tr-user-sensitivity": "blind",
        "x-tr-userid": "Lynx-Editor-Online",
        "x-tr-sessionid": "learn-mcp",
        "x-tr-asset-id": _ASSET_ID,
        "x-tr-authorization": "abc",
        "x-tr-llm-profile-key": dep["profile_key"],
    }

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=dep["deployment"],
        api_version=dep["api_version"],
        api_key=api_key,
        temperature=temperature,
        default_headers=default_headers,
    )
