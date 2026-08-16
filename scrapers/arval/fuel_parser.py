import re
from playwright.sync_api import Page


class ArvalFuelParser:
    """
    Arval fuel parser V2.

    Priority:
    1. Exact "Üzemanyag" field-wrapper relationship.
    2. Exact equipment-label sibling relationship.
    3. Conservative title/URL fallback only when an explicit
       powertrain token is present.

    This avoids accidentally reading the wrong equipment-value from
    another field-wrapper.
    """

    MAPPING = {
        "benzin plug-in hibrid": "PHEV",
        "plug-in hibrid": "PHEV",
        "phev": "PHEV",
        "elektromos": "EV",
        "100% elektromos": "EV",
        "ev": "EV",
        "dízel": "Diesel",
        "dizel": "Diesel",
        "diesel": "Diesel",
        "benzin": "Petrol",
        "petrol": "Petrol",
        "hibrid": "Hybrid",
        "hybrid": "Hybrid",
        "mild-hibrid": "MHEV",
        "mild hybrid": "MHEV",
        "mhev": "MHEV",
    }

    def parse(
        self,
        page: Page,
    ) -> str:

        # ----------------------------------------------------
        # 1. Exact field-wrapper containing equipment-label
        #    whose text is exactly "Üzemanyag"
        # ----------------------------------------------------

        wrappers = page.locator(
            "div.field-wrapper"
        )

        for i in range(wrappers.count()):
            wrapper = wrappers.nth(i)

            label = wrapper.locator(
                "span.equipment-label"
            )

            if label.count() == 0:
                continue

            try:
                label_text = (
                    label.first
                    .inner_text()
                    .strip()
                )
            except Exception:
                continue

            if label_text != "Üzemanyag":
                continue

            value = wrapper.locator(
                "b.equipment-value"
            )

            if value.count() == 0:
                continue

            text = (
                value.first
                .inner_text()
                .strip()
            )

            parsed = self._map_text(
                text
            )

            if parsed is not None:
                return parsed

        # ----------------------------------------------------
        # 2. Sibling fallback from exact label
        # ----------------------------------------------------

        label = page.locator(
            "span.equipment-label"
        ).filter(
            has_text="Üzemanyag"
        )

        for i in range(label.count()):
            candidate = label.nth(i)

            try:
                if (
                    candidate.inner_text().strip()
                    != "Üzemanyag"
                ):
                    continue
            except Exception:
                continue

            wrapper = candidate.locator(
                "xpath=ancestor::div[contains(@class,'field-wrapper')][1]"
            )

            if wrapper.count() == 0:
                continue

            value = wrapper.locator(
                "b.equipment-value"
            )

            if value.count() == 0:
                continue

            text = (
                value.first
                .inner_text()
                .strip()
            )

            parsed = self._map_text(
                text
            )

            if parsed is not None:
                return parsed

        # ----------------------------------------------------
        # 3. Conservative explicit-token fallback
        # ----------------------------------------------------

        title = ""

        h1 = page.locator("h1 span")

        if h1.count() > 0:
            try:
                title = (
                    h1.first
                    .inner_text()
                    .strip()
                )
            except Exception:
                title = ""

        evidence = (
            f"{title} {page.url}"
            .casefold()
        )

        explicit_rules = [
            (
                r"(plug[- ]?in|phev|dm[- ]?i)",
                "PHEV",
            ),
            (
                r"(elektromos|(?:^|[-_/])ev(?:[-_/]|$)|kwh)",
                "EV",
            ),
            (
                r"(dízel|dizel|diesel|dci|tdi)",
                "Diesel",
            ),
            (
                r"(mhev|mild[- ]?hibrid|mild[- ]?hybrid)",
                "MHEV",
            ),
            (
                r"(benzin|petrol|tsi|turbo)",
                "Petrol",
            ),
        ]

        for pattern, result in explicit_rules:
            if re.search(
                pattern,
                evidence,
                flags=re.I,
            ):
                return result

        raise ValueError(
            "Arval fuel type could not be safely resolved."
        )

    def _map_text(
        self,
        text: str,
    ):

        normalized = (
            " ".join(
                text.casefold().split()
            )
        )

        if normalized in self.MAPPING:
            return self.MAPPING[
                normalized
            ]

        # tolerate descriptive strings
        for key, value in self.MAPPING.items():
            if key in normalized:
                return value

        return None
