import re
from urllib.parse import urlsplit

from playwright.sync_api import Page


class AyvensVehicleIdentityParser:
    """
    Vehicle identity parser for Ayvens detail pages.

    Goal:
        brand = manufacturer
        model = model line
        trim  = advertised version / derivative

    This parser is evidence-first and uses only page text / URL structure.
    """

    API_ROOT = "https://autotartosberlet.ayvens.com/api/cars"

    def parse_brand(
        self,
        page: Page,
    ) -> str:

        # Prefer breadcrumb manufacturer.
        breadcrumbs = page.locator(
            "li.breadcrumbs-item"
        )

        values = []

        for i in range(
            breadcrumbs.count()
        ):
            try:
                text = (
                    breadcrumbs.nth(i)
                    .inner_text()
                    .strip()
                )
            except Exception:
                continue

            if text:
                values.append(text)

        # Expected breadcrumb sequence:
        # Főoldal / Tartós bérlet ajánlatok / BRAND / MODEL
        if len(values) >= 3:
            return values[-2]

        # Fallback from URL:
        # /opel/astra
        parts = [
            part
            for part in page.url.split("/")
            if part
        ]

        if len(parts) >= 2:
            brand = parts[-2]
            return brand.replace("-", " ").title()

        raise ValueError(
            "Ayvens brand could not be resolved."
        )

    def parse_model_name(
        self,
        page: Page,
    ) -> str:

        breadcrumbs = page.locator(
            "li.breadcrumbs-item"
        )

        values = []

        for i in range(
            breadcrumbs.count()
        ):
            try:
                text = (
                    breadcrumbs.nth(i)
                    .inner_text()
                    .strip()
                )
            except Exception:
                continue

            if text:
                values.append(text)

        if len(values) >= 4:
            return values[-1]

        parts = [
            part
            for part in page.url.split("?")[0].split("/")
            if part
        ]

        if len(parts) >= 2:
            model = parts[-1]
            return (
                model
                .replace("-", " ")
                .strip()
                .title()
            )

        raise ValueError(
            "Ayvens model name could not be resolved."
        )

    def parse_trim(
        self,
        page: Page,
    ) -> str:

        locator = page.locator(
            "div.font-size-18px.fw-400.font-source.color-blue"
        )

        if locator.count() > 0:
            trim = (
                locator.first
                .inner_text()
                .strip()
            )

            if trim:
                return trim

        trim = self._parse_api_configuration(page)

        if trim:
            return trim

        raise ValueError(
            "Ayvens trim/version text not found in the exact-offer "
            "DOM or explicit provider API configuration."
        )

    def _parse_api_configuration(
        self,
        page: Page,
    ) -> str | None:
        api_url = self._api_url_from_offer(page.url)

        if api_url is None:
            return None

        try:
            response = page.request.get(
                api_url,
                timeout=60000,
            )

            if not response.ok:
                return None

            payload = response.json()
        except Exception:
            return None

        if not isinstance(payload, dict):
            return None

        data = payload.get("data")

        if not isinstance(data, dict):
            return None

        configuration = data.get("configuration")

        if not isinstance(configuration, str):
            return None

        return configuration.strip() or None

    @classmethod
    def _api_url_from_offer(
        cls,
        url: str,
    ) -> str | None:
        parsed = urlsplit(url or "")

        if parsed.hostname != "autotartosberlet.ayvens.com":
            return None

        parts = tuple(
            part
            for part in parsed.path.split("/")
            if part
        )

        if len(parts) != 2:
            return None

        return f"{cls.API_ROOT}/{parts[0]}/{parts[1]}"
