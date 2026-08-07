from typing import Optional

from playwright.sync_api import sync_playwright, Page

from models.offer import Offer
from scrapers.arval.cookies import accept_cookies
from scrapers.arval.parser import ArvalParser

ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/ajanlat-hosszu-tavu-igenyekre"


class ArvalScraper:

    def collect(self) -> list[Offer]:

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            urls = self.collect_offer_urls(page)

            offers = []

            # Egyelőre csak az első ajánlatot dolgozzuk fel
            for url in urls[:1]:

                offer = self.collect_offer(page, url)

                if offer:
                    offers.append(offer)

            browser.close()

            return offers

    def collect_offer_urls(self, page: Page) -> list[str]:

        page.goto(
            ARVAL_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        accept_cookies(page)

        page.wait_for_timeout(2000)

        cards = page.locator("a.is-result-list")

        urls = []

        for i in range(cards.count()):

            href = cards.nth(i).get_attribute("href")

            if href:
                urls.append("https://www.arval.hu" + href)

        print(f"Found {len(urls)} offers")

        return urls

    def collect_offer(self, page: Page, url: str) -> Optional[Offer]:

        print(f"\nOpening: {url}")

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(1500)

        page.pause()

        parser = ArvalParser()

        title = parser.parse_title(page)
        monthly_fee = parser.parse_monthly_fee(page)

        print(f"Title: {title}")
        print(f"Monthly fee: {monthly_fee:,} Ft") 

        duration = parser.parse_duration(page)

        print(f"Title: {title}")
        print(f"Monthly fee: {monthly_fee} Ft")
        print(f"Duration: {duration} months")  

        return Offer(
            provider="Arval",
            brand="",
            model="",
            trim=title,
            fuel_type="",
            monthly_fee=0,
            duration=0,
            mileage=0,
            url=url,
        )