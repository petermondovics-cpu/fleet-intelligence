from typing import Optional

from playwright.sync_api import Page, sync_playwright

from core.scraper_plugin import ScraperPlugin
from models.offer import Offer
from scrapers.ayvens.parser import AyvensParser


AYVENS_URL = "https://autotartosberlet.ayvens.com/"


class AyvensScraper(ScraperPlugin):

    name = "ayvens"

    def collect(self) -> list[Offer]:

        with sync_playwright() as p:

            browser = p.chromium.launch(
                headless=False
            )

            page = browser.new_page()

            urls = self.collect_offer_urls(page)

            offers = []

            for url in urls:

                try:

                    offer = self.collect_offer(
                        page,
                        url,
                    )

                    if offer:
                        offers.append(offer)

                except Exception as e:

                    print(f"❌ Failed: {url}")
                    print(e)

                    continue

            browser.close()

            print(
                f"\nAyvens collected "
                f"{len(offers)} offers"
            )

            return offers

    def collect_offer_urls(
        self,
        page: Page,
    ) -> list[str]:

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(3000)

        cards = (
            page.locator("div.card-container")
            .locator("xpath=ancestor::a[1]")
        )

        urls = []

        for i in range(cards.count()):

            href = cards.nth(i).get_attribute(
                "href"
            )

            if href:

                if href.startswith("http"):
                    urls.append(href)
                else:
                    urls.append(
                        "https://autotartosberlet.ayvens.com"
                        + href
                    )

        print(
            f"Found {len(urls)} Ayvens offers"
        )

        return urls

    def collect_offer(
        self,
        page: Page,
        url: str,
    ) -> Optional[Offer]:

        print(f"\nOpening: {url}")

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(2000)

        parser = AyvensParser()

        title = parser.parse_title(page)
        model = parser.parse_model(page)
        monthly_fee = parser.parse_monthly_fee(page)
        duration = parser.parse_duration(page)
        mileage = parser.parse_mileage(page)
        fuel_type = parser.parse_fuel_type(page)

        print(f"Title: {title}")
        print(f"Model: {model}")
        print(
            f"Monthly fee: "
            f"{monthly_fee:,} Ft"
        )
        print(
            f"Duration: "
            f"{duration} months"
        )
        print(
            f"Mileage: "
            f"{mileage:,} km/year"
        )
        print(f"Fuel: {fuel_type}")

        return Offer(
            provider="Ayvens",
            brand="",
            model=title,
            trim=model,
            fuel_type=fuel_type,
            monthly_fee=monthly_fee,
            duration=duration,
            mileage=mileage,
            url=url,
        )