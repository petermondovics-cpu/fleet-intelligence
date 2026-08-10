from exporters.excel_exporter import ExcelExporter
from exporters.json_exporter import JsonExporter
from scrapers.arval.scraper import ArvalScraper
from database.database import Database


class ScraperManager:

    def run(self):

        scraper = ArvalScraper()

        offers = scraper.collect()

        JsonExporter().export(offers, "arval.json")
        ExcelExporter().export(offers, "arval.xlsx")

        repo = OfferRepository()
        repo.save_all(offers)
        repo.close()