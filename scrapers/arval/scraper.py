from playwright.sync_api import sync_playwright

from models.offer import Offer
from scrapers.arval.cookies import accept_cookies
from scrapers.arval.parser import ArvalParser

ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/ajanlat-hosszu-tavu-igenyekre"


class ArvalScraper:

    def collect(self) -> list[Offer]:

        offers = []

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            page.goto(
                ARVAL_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            accept_cookies(page)

            page.wait_for_timeout(2000)

            cards = page.locator("a.is-result-list")

            count = cards.count()

            print(f"Found {count} offers")

            for i in range(count):

                href = cards.nth(i).get_attribute("href")

                if href:

                    offers.append(
                        Offer(
                            provider="Arval",
                            brand="",
                            model="",
                            trim="",
                            fuel_type="",
                            monthly_fee=0,
                            duration=0,
                            mileage=0,
                            url="https://www.arval.hu" + href,
                        )
                    )

            if offers:

                print()
                print("Opening first offer...")
                print(offers[0].url)

                page.goto(
                    offers[0].url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(2000)

                parser = ArvalParser()

                title = parser.parse_title(page)

                print()
                print("=" * 60)
                print(f"Title: {title}")
                print("=" * 60)

                #page.pause()

            browser.close()

        return offers