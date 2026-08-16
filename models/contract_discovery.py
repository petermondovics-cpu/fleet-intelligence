from dataclasses import dataclass
from typing import List, Tuple

from playwright.sync_api import Page


@dataclass(frozen=True)
class DiscoveredContract:
    duration: int
    mileage: int


class ContractDiscoveryEngine:
    """
    Provider-neutral contract discovery.

    Discovery is deliberately conservative:
    only values that are visibly present on the page and
    look like contract values are returned.

    It does not invent a contract matrix.
    """

    def discover(
        self,
        page: Page,
    ) -> List[DiscoveredContract]:

        durations = self.discover_durations(page)
        mileages = self.discover_mileages(page)

        contracts = []

        for duration in durations:
            for mileage in mileages:
                contracts.append(
                    DiscoveredContract(
                        duration=duration,
                        mileage=mileage,
                    )
                )

        return contracts

    def discover_durations(
        self,
        page: Page,
    ) -> List[int]:

        values = set()

        selectors = [
            "p.OfferConfigurationTitle",
            "button",
            "label",
            "[role='option']",
            "[role='radio']",
            "[role='button']",
            "p",
            "span",
            "div",
        ]

        for selector in selectors:

            locators = page.locator(selector)

            for i in range(
                locators.count()
            ):

                item = locators.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = item.inner_text().strip()

                except Exception:
                    continue

                duration = self._extract_duration(
                    text
                )

                if duration is not None:
                    values.add(duration)

        return sorted(values)

    def discover_mileages(
        self,
        page: Page,
    ) -> List[int]:

        values = set()

        selectors = [
            "p.OfferConfigurationTitle",
            "button",
            "label",
            "[role='option']",
            "[role='radio']",
            "[role='button']",
            "p",
            "span",
            "div",
        ]

        for selector in selectors:

            locators = page.locator(selector)

            for i in range(
                locators.count()
            ):

                item = locators.nth(i)

                try:
                    if not item.is_visible():
                        continue

                    text = item.inner_text().strip()

                except Exception:
                    continue

                mileage = self._extract_mileage(
                    text
                )

                if mileage is not None:
                    values.add(mileage)

        return sorted(values)

    @staticmethod
    def _extract_duration(
        text: str,
    ) -> int | None:

        import re

        match = re.search(
            r"(?<!\d)(\d{2})\s*(?:hónap|hó)\b",
            text.lower(),
        )

        if not match:
            return None

        value = int(
            match.group(1)
        )

        # Contract durations are expected to be
        # realistic leasing terms, not arbitrary numbers.
        if value < 12 or value > 84:
            return None

        return value

    @staticmethod
    def _extract_mileage(
        text: str,
    ) -> int | None:

        import re

        if (
            "km/év" not in text.lower()
            and "km / év" not in text.lower()
        ):
            return None

        match = re.search(
            r"(?<!\d)(\d{1,3}(?:[.\s,]\d{3})+|\d{4,6})(?!\d)",
            text,
        )

        if not match:
            return None

        value = int(
            re.sub(
                r"\D",
                "",
                match.group(1),
            )
        )

        if value < 5000 or value > 100000:
            return None

        return value


def format_contracts(
    contracts: List[DiscoveredContract],
) -> List[Tuple[int, int]]:

    return [
        (
            contract.duration,
            contract.mileage,
        )
        for contract in contracts
    ]
