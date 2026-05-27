"""Small HTTP client used by the CLI."""

from __future__ import annotations

from typing import Any

import httpx


class CliHttpError(RuntimeError):
    """Raised when the CLI cannot complete an HTTP request."""


class PrimeSwarmHttpClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.transport = transport

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def create_run(
        self,
        question: str,
        *,
        source_path: str | None = None,
        use_web_search: bool = False,
        top_k: int = 4,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"question": question, "top_k": top_k, "use_web_search": use_web_search}
        if source_path:
            payload["source_path"] = source_path
        return self._request("POST", "/v1/runs", json=payload)

    def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout, transport=self.transport) as client:
                response = client.request(method, path, headers=headers, json=json)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            detail = _error_detail(exc.response)
            raise CliHttpError(f"{exc.response.status_code}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise CliHttpError(str(exc)) from exc

        if not isinstance(payload, dict):
            raise CliHttpError("response was not a JSON object")
        return payload


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text
    if isinstance(payload, dict) and "detail" in payload:
        return str(payload["detail"])
    return str(payload)
