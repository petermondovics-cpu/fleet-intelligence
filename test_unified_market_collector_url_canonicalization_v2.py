from pathlib import Path
import tempfile

from database.market_repository import (
    MarketRepository,
)
from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
)
from market_intelligence.market_vehicle_normalizer import (
    MarketVehicleNormalizer,
)
from market_intelligence.unified_market_collector import (
    UnifiedMarketCollector,
)
from models.offer import Offer


BAD_ARVAL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

GOOD_ARVAL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


class FakeScraper:
    def __init__(
        self,
        offers,
    ):
        self.offers = tuple(
            offers
        )

    def collect(self):
        return list(
            self.offers
        )


def offer(
    provider,
    url,
    fee,
    duration,
):
    return Offer(
        provider=provider,
        brand="",
        model=(
            "BYD ATTO 2"
            if provider == "Arval"
            else "BYD ATTO 2 DM-i"
        ),
        trim="",
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=20000,
        url=url,
        raw_title=(
            "BYD ATTO 2"
            if provider == "Arval"
            else "BYD ATTO 2 DM-i"
        ),
    )


def main():

    print("=" * 100)
    print("UNIFIED MARKET COLLECTOR URL CANONICALIZATION V2")
    print("=" * 100)

    with tempfile.TemporaryDirectory() as tmp:

        db_path = str(
            Path(tmp)
            / "fleet_test.db"
        )

        repository = (
            MarketRepository(
                db_path
            )
        )

        collector = (
            UnifiedMarketCollector(
                repository=repository,
                normalizer=(
                    MarketVehicleNormalizer()
                ),
                scrapers=(
                    (
                        "Arval",
                        FakeScraper(
                            (
                                offer(
                                    "Arval",
                                    BAD_ARVAL,
                                    192312,
                                    60,
                                ),
                            )
                        ),
                    ),
                    (
                        "Ayvens",
                        FakeScraper(
                            (
                                offer(
                                    "Ayvens",
                                    AYVENS,
                                    189990,
                                    48,
                                ),
                            )
                        ),
                    ),
                ),
            )
        )

        result = collector.run()

        assert result.status == "COMPLETED"
        assert result.total_offers == 2

        rows = (
            MarketOfferRepository(
                db_path
            )
            .list_offers()
        )

        arval = next(
            row
            for row in rows
            if row.provider == "Arval"
        )

        ayvens = next(
            row
            for row in rows
            if row.provider == "Ayvens"
        )

        assert arval.url == GOOD_ARVAL
        assert ayvens.url == AYVENS

        # Commercial evidence survives unchanged.
        assert (
            arval.monthly_fee
            == 192312
        )
        assert arval.duration == 60
        assert arval.mileage == 20000

        # Persistence key must be based on canonical URL,
        # not the duplicated legacy URL.
        assert BAD_ARVAL not in arval.url

        collector.close()

    print(
        "TEST PASSED - UNIFIED MARKET COLLECTION "
        "CANONICALIZES ARVAL URLS BEFORE NORMALIZATION "
        "AND PERSISTENCE, WHILE AYVENS IS UNTOUCHED."
    )


if __name__ == "__main__":
    main()
