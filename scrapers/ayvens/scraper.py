from playwright.sync_api import sync_playwright, Page

from scrapers.ayvens.parser import AyvensParser

AYVENS_URL = "https://autotartosberlet.ayvens.com/"


class AyvensScraper:

    def collect(self):

        with sync_playwright() as p:

            browser = p.chromium.launch(headless=False)

            page = browser.new_page()

            urls = self.collect_offer_urls(page)

            if urls:
                self.collect_offer(page, urls[0])

            browser.close()

            return urls

    def collect_offer_urls(self, page: Page) -> list[str]:

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

            href = cards.nth(i).get_attribute("href")

            if href:
                urls.append(
                    "https://autotartosberlet.ayvens.com" + href
                )

        print(f"Found {len(urls)} offers")

        return urls

    def collect_offer(self, page: Page, url: str):

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
        print(f"Monthly fee: {monthly_fee:,} Ft")
        print(f"Duration: {duration} months")
        print(f"Mileage: {mileage:,} km/year")
        print(f"Fuel: {fuel_type}")