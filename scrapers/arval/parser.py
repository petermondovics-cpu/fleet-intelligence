import re

from playwright.sync_api import Page


class ArvalParser:

    def _configuration_value(self, page: Page, label: str) -> str:
        return (
            page.locator("p.OfferConfigurationTitle")
            .filter(has_text=label)
            .locator("span.value")
            .inner_text()
            .strip()
        )

    def parse_title(self, page: Page) -> str:
        return page.locator("h1 span").inner_text().strip()

    def parse_monthly_fee(self, page: Page) -> int:
        locator = page.locator("span.PricePrimary").first

        if locator.count() == 0:
            raise ValueError("Monthly fee not found")

        text = locator.inner_text().strip()

        digits = re.sub(r"\D", "", text)

        if not digits:
            raise ValueError(f"Invalid monthly fee: '{text}'")

        return int(digits)

    def parse_duration(self, page: Page) -> int:
        text = self._configuration_value(page, "Időtartam")

        digits = re.sub(r"\D", "", text)

        return int(digits)

    def parse_mileage(self, page: Page) -> int:
        text = self._configuration_value(page, "Futásteljesítmény")

        digits = re.sub(r"\D", "", text)

        return int(digits)

    def parse_fuel_type(self, page: Page) -> str:
        text = (
            page.locator("div.label-wrapper")
            .filter(has_text="Üzemanyag")
            .locator("b.equipment-value")
            .inner_text()
            .strip()
        )

        mapping = {
            "Benzin Plug-in hibrid": "PHEV",
            "Plug-in hibrid": "PHEV",
            "Elektromos": "EV",
            "Dízel": "Diesel",
            "Benzin": "Petrol",
            "Hibrid": "Hybrid",
        }

        return mapping.get(text, text)