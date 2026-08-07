import re

from playwright.sync_api import Page


class ArvalParser:

    def parse_title(self, page: Page) -> str:
        return page.locator("h1 span").inner_text().strip()

    def parse_monthly_fee(self, page: Page) -> int:
        """
        Returns the monthly fee as an integer.
        Example:
            '192312 FT' -> 192312
        """

        text = page.locator("span.PricePrimary").first.inner_text().strip()

        digits = re.sub(r"\D", "", text)

        return int(digits)

    def parse_duration(self, page: Page) -> int:
        """
        Returns the lease duration in months.
        Example:
            '60 hónap' -> 60
        """

        text = (
            page.locator("p.OfferConfigurationTitle")
            .filter(has_text="Időtartam")
            .locator("span.value")
            .inner_text()
            .strip()
        )

        digits = re.sub(r"\D", "", text)

        return int(digits)