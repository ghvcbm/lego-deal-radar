"""Client for the Rebrickable LEGO API."""

from __future__ import annotations

from collections.abc import Iterator
from urllib.parse import quote, urlencode

from .config import required_env
from .http import APIError, request_json

ARCHITECTURE_THEME_NAME = "Architecture"


class RebrickableClient:
    """Read LEGO set data from Rebrickable."""

    base_url = "https://rebrickable.com/api/v3/lego"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or required_env("REBRICKABLE_API_KEY")

    def _get(self, path: str, **query: str | int) -> dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        return self._get_url(url, **query)

    def _get_url(self, url: str, **query: str | int) -> dict:
        if query:
            url = f"{url}?{urlencode({key: value for key, value in query.items() if value != ''})}"
        return request_json(
            url,
            headers={"Authorization": f"key {self.api_key}"},
        )

    def _paginate(self, path: str, **query: str | int) -> Iterator[dict]:
        """Yield every result from a Rebrickable paginated endpoint."""
        page = 1
        while True:
            response = self._get(path, page=page, **query)
            results = response.get("results")
            if not isinstance(results, list):
                raise APIError("Rebrickable returned an invalid paginated response.")
            yield from (result for result in results if isinstance(result, dict))

            next_url = response.get("next")
            if not next_url:
                break
            page += 1

    def find_architecture_theme(self) -> dict:
        """Find the theme whose name is exactly ``Architecture``."""
        for theme in self._paginate(
            "themes/",
            search=ARCHITECTURE_THEME_NAME,
            page_size=100,
        ):
            if theme.get("name") == ARCHITECTURE_THEME_NAME:
                return theme
        raise APIError(f'Rebrickable theme "{ARCHITECTURE_THEME_NAME}" was not found.')

        def get_architecture_sets(self) -> list[dict]:
            """Retrieve all sets belonging to the exact Architecture theme."""
            theme = self.find_architecture_theme()
            theme_id = theme.get("id")

            if not isinstance(theme_id, int):
                raise APIError("Rebrickable returned an invalid Architecture theme ID.")

            return list(
                self._paginate(
                    "sets/",
                    theme_id=theme_id,
                    page_size=1000,
                )
            )
    def get_set(self, set_number: str) -> dict:
        """Return details for one LEGO set."""
        return self._get(f"sets/{quote(set_number, safe='')}/")

    def search_sets(self, search: str, page_size: int = 10) -> dict:
        """Search LEGO sets by name or number."""
        return self._get("sets/", search=search, page_size=page_size)
