from exporters.excel_exporter import ExcelExporter
from exporters.json_exporter import JsonExporter
from scrapers.arval.scraper import ArvalScraper


class ScraperManager:

    def run(self):

        scraper = ArvalScraper()

        offers = scraper.collect()

        print(f"\nCollected {len(offers)} offers")

        JsonExporter().export(
            offers,
            "arval.json",
        )

        ExcelExporter().export(
            offers,
            "arval.xlsx",
        )