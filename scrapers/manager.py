from scrapers.arval.scraper import ArvalScraper


class ScraperManager:

    def run(self):

        scraper = ArvalScraper()

        offers = scraper.collect()

        print()

        print(f"Collected {len(offers)} offers")

        for offer in offers[:5]:
            print(offer.url)