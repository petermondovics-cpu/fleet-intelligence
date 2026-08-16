from pathlib import Path
import tempfile

from database.market_repository import MarketRepository
from market_intelligence.market_offer_repository import MarketOfferRepository
from market_intelligence.market_vehicle_normalizer import MarketVehicleNormalizer
from market_intelligence.unified_market_collector import UnifiedMarketCollector
from models.offer import Offer

class FakeScraper:
    def __init__(self, offers=None, error=None):
        self.offers = offers or ()
        self.error = error

    def collect(self):
        if self.error:
            raise self.error
        return list(self.offers)

def mk(provider, title, fee, duration, url):
    return Offer(
        provider=provider,
        brand="",
        model=title,
        trim="",
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=20000,
        url=url,
        raw_title=title,
    )

def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "fleet_test.db")
        repo = MarketRepository(db_path)

        collector = UnifiedMarketCollector(
            repository=repo,
            normalizer=MarketVehicleNormalizer(),
            scrapers=(
                (
                    "Arval",
                    FakeScraper((
                        mk(
                            "Arval",
                            "BYD ATTO 2",
                            192312,
                            60,
                            "https://www.arval.hu/tartos-berleti-ajantlat/byd-atto-2",
                        ),
                    )),
                ),
                (
                    "Ayvens",
                    FakeScraper((
                        mk(
                            "Ayvens",
                            "BYD ATTO 2 DM-i",
                            189990,
                            48,
                            "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i",
                        ),
                    )),
                ),
            ),
        )

        result = collector.run()
        assert result.status == "COMPLETED"
        assert result.total_offers == 2

        rows = MarketOfferRepository(db_path).list_offers()
        assert {r.provider for r in rows} == {"Arval", "Ayvens"}

        collector.close()

        print(
            "TEST PASSED - UNIFIED MARKET COLLECTOR "
            "PERSISTS BOTH PROVIDERS INTO ONE MARKET RUN."
        )

if __name__ == "__main__":
    main()
