"""Small standard-library HTTP helper used by the API clients."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class APIError(RuntimeError):
    """Raised when an external API request fails."""


def request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> dict:
    """Make a JSON request and return its decoded object."""
    request_headers = {"Accept": "application/json"}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)

    request = Request(
        url,
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers=request_headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise APIError(f"API request failed with HTTP {error.code}: {detail}") from error
    except (URLError, TimeoutError, OSError) as error:
        reason = getattr(error, "reason", str(error))
        raise APIError(f"Could not reach API: {reason}") from error

    if not isinstance(payload, dict):
        raise APIError("API returned an unexpected response.")
    return payload