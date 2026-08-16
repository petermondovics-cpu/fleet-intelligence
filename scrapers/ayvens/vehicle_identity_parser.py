import re

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

        if locator.count() == 0:
            raise ValueError(
                "Ayvens trim/version text not found."
            )

        trim = (
            locator.first
            .inner_text()
            .strip()
        )

        if not trim:
            raise ValueError(
                "Ayvens trim/version text is empty."
            )

        return trim
