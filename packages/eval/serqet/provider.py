"""Provider routing. OpenRouter credentials never travel to another host."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol
from urllib import error as urlerror
from urllib import request as urlrequest

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

PROVIDERS = {
    "openrouter": {"url": OPENROUTER_URL, "env": "OPENROUTER_API_KEY"},
    "openai": {"url": OPENAI_URL, "env": "OPENAI_API_KEY"},
}

_SECRET = re.compile(
    r"(sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+|OPENROUTER_API_KEY|OPENAI_API_KEY)",
)


class Transport(Protocol):
    def post(
        self,
        url: str,
        body: bytes,
        headers: dict[str, str],
        timeout: float,
    ) -> tuple[int, dict[str, Any]]:
        """Return the HTTP status and a JSON object. Do not log headers."""


class UrllibTransport:
    def post(
        self,
        url: str,
        body: bytes,
        headers: dict[str, str],
        timeout: float,
    ) -> tuple[int, dict[str, Any]]:
        req = urlrequest.Request(url, data=body, headers=headers, method="POST")
        try:
            with urlrequest.urlopen(req, timeout=timeout) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
                status = int(getattr(response, "status", 200))
        except urlerror.HTTPError as exc:
            payload = _error_payload(exc.read())
            return int(exc.code), payload
        except urlerror.URLError as exc:
            return 0, {"error": {"message": redact(str(exc.reason)), "type": "transport"}}
        if not isinstance(payload, dict):
            return status, {"error": {"message": "provider response was not an object"}}
        return status, redact_value(payload)


def credential(provider: str) -> str | None:
    spec = PROVIDERS.get(provider)
    if spec is None:
        return None
    value = os.environ.get(spec["env"])
    if value:
        return value
    return None


def endpoint(provider: str) -> str:
    spec = PROVIDERS.get(provider)
    if spec is None:
        raise ValueError(f"unknown provider {provider}")
    return str(spec["url"])


def redact(text: str) -> str:
    return _SECRET.sub("[redacted]", text)


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in {"authorization", "api_key", "api-key", "x-api-key"}:
                redacted[key] = "[redacted]"
            else:
                redacted[key] = redact_value(item)
        return redacted
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    return value


def _error_payload(raw: bytes) -> dict[str, Any]:
    text = redact(raw.decode("utf-8", errors="replace")[:500])
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"error": {"message": text or "provider error"}}
    if isinstance(parsed, dict):
        return redact_value(parsed)
    return {"error": {"message": text or "provider error"}}
