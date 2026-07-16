"""Small client for Ollama's local HTTP application programming interface."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5-coder:3b"


class OllamaError(RuntimeError):
    """A user-actionable local Ollama failure."""


@dataclass(frozen=True)
class OllamaStatus:
    available: bool
    models: tuple[str, ...] = ()
    error: str | None = None


def _request(path: str, payload: dict | None = None, timeout: float = 3.0, base_url: str = DEFAULT_BASE_URL) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def status(base_url: str = DEFAULT_BASE_URL) -> OllamaStatus:
    try:
        payload = _request("/api/tags", base_url=base_url)
        models = tuple(sorted(item["name"] for item in payload.get("models", []) if item.get("name")))
        return OllamaStatus(True, models)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
        return OllamaStatus(False, error=str(exc))


def chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 120.0,
    num_predict: int = 350,
    temperature: float = 0,
) -> str:
    payload = {
        "model": model,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    try:
        response = _request("/api/chat", payload, timeout, base_url)
        return response["message"]["content"].strip()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OllamaError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except (OSError, urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
        raise OllamaError(
            "Ollama is unavailable. Start it, then run "
            f"`ollama pull {model}` and retry. Original error: {exc}"
        ) from exc


def setup_instructions(model: str = DEFAULT_MODEL) -> str:
    return (
        "Install Ollama for Windows from https://ollama.com/download/windows, then run:\n"
        f"  ollama pull {model}\n"
        "  ollama serve\n"
        "The assistant never installs Ollama or downloads models automatically."
    )
