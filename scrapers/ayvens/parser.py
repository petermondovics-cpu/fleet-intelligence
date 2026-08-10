import re

from playwright.sync_api import Page


class AyvensParser:

    def parse_title(self, page: Page) -> str:
        return (
            page.locator("h2.fw-500.font-size-28px")
            .first
            .inner_text()
            .strip()
        )

    def parse_model(self, page: Page) -> str:
        return (
            page.locator("div.font-size-18px.fw-400.font-source.color-blue")
            .first
            .inner_text()
            .strip()
        )

    def parse_monthly_fee(self, page: Page) -> int:

        text = (
            page.locator("div.font-size-40px.fw-500.whitespace-nowrap")
            .first
            .inner_text()
            .strip()
        )

        digits = re.sub(r"\D", "", text)

        return int(digits)

    def parse_duration(self, page: Page) -> int:

    text = (
        page.locator("p.font-size-16px.font-source.color-\\#757777")
        .first
        .inner_text()
        .strip()
    )

    match = re.search(r"(\d+)\s*hónap", text)

    return int(match.group(1))


def parse_mileage(self, page: Page) -> int:

    text = (
        page.locator("p.font-size-16px.font-source.color-\\#757777")
        .first
        .inner_text()
        .strip()
    )

    match = re.search(r"([\d\.]+)\s*km/év", text)

    return int(match.group(1).replace(".", "")) 

def parse_fuel_type(self, page: Page) -> str:

    text = (
        page.locator("strong.fw-700")
        .first
        .inner_text()
        .strip()
    )

    mapping = {
        "100% elektromos": "EV",
        "Elektromos": "EV",
        "Plug-in hibrid": "PHEV",
        "Hibrid": "Hybrid",
        "Benzin": "Petrol",
        "Dízel": "Diesel",
    }

    return mapping.get(text, text)    