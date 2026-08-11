from core import ScraperPlugin


class TestScraper(ScraperPlugin):
    name = "test-scraper"

    def collect(self):
        return []


def main():
    scraper = TestScraper()

    print("Scraper name:")
    print(scraper.name)

    print("\nScraper category:")
    print(scraper.category)

    print("\nCollected offers:")
    print(scraper.collect())

    print("\nExecuted through plugin interface:")
    print(scraper.execute())


if __name__ == "__main__":
    main()