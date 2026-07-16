"""Optional OpenAI-compatible hosted chat for Streamlit Cloud and other remotes."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


class HostedLLMError(RuntimeError):
    """A user-actionable hosted language-model failure."""


@dataclass(frozen=True)
class HostedLLMConfig:
    api_key: str
    base_url: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key.strip() and self.model.strip())


def _secret_or_env(name: str, secrets: dict | None = None) -> str | None:
    if secrets:
        value = secrets.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    value = os.environ.get(name)
    if value is not None and value.strip():
        return value.strip()
    return None


def load_hosted_config(secrets: dict | None = None) -> HostedLLMConfig | None:
    """Load optional hosted chat settings from Streamlit secrets or environment variables.

    Recognised names:
    - HOSTED_LLM_API_KEY (required)
    - HOSTED_LLM_BASE_URL (default: https://api.openai.com/v1)
    - HOSTED_LLM_MODEL (required when the API key is set)
    """
    api_key = _secret_or_env("HOSTED_LLM_API_KEY", secrets)
    if not api_key:
        return None
    base_url = _secret_or_env("HOSTED_LLM_BASE_URL", secrets) or "https://api.openai.com/v1"
    model = _secret_or_env("HOSTED_LLM_MODEL", secrets)
    if not model:
        return None
    return HostedLLMConfig(api_key=api_key, base_url=base_url.rstrip("/"), model=model)


def hosted_status(secrets: dict | None = None) -> tuple[bool, str | None]:
    config = load_hosted_config(secrets)
    if config is None:
        return False, None
    return True, config.model


def chat_hosted(
    system_prompt: str,
    user_prompt: str,
    *,
    config: HostedLLMConfig | None = None,
    secrets: dict | None = None,
    timeout: float = 120.0,
    temperature: float = 0,
    max_tokens: int = 350,
) -> str:
    cfg = config or load_hosted_config(secrets)
    if cfg is None or not cfg.configured:
        raise HostedLLMError(
            "Hosted language-model settings are incomplete. "
            "Set HOSTED_LLM_API_KEY, HOSTED_LLM_BASE_URL, and HOSTED_LLM_MODEL."
        )
    payload = {
        "model": cfg.model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        f"{cfg.base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise HostedLLMError(f"Hosted model returned HTTP {exc.code}: {detail}") from exc
    except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError, IndexError) as exc:
        raise HostedLLMError(f"Hosted model request failed: {exc}") from exc
