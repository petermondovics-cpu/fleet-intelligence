from pathlib import Path
import sqlite3
import tempfile

from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
)
from market_intelligence.market_overview_service import (
    MarketOverviewService,
)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "market_test.db"

        con = sqlite3.connect(db_path)
        con.execute(
            """
            CREATE TABLE offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT,
                brand TEXT,
                model TEXT,
                trim TEXT,
                fuel_type TEXT,
                monthly_fee INTEGER,
                duration INTEGER,
                mileage INTEGER,
                url TEXT
            )
            """
        )

        con.executemany(
            """
            INSERT INTO offers(
                provider, brand, model, trim, fuel_type,
                monthly_fee, duration, mileage, url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    "Arval", "BYD", "ATTO 2", "BOOST", "PHEV",
                    192312, 60, 20000, "https://example.test/arval"
                ),
                (
                    "Ayvens", "BYD", "ATTO 2 DM-i", "Active", "PHEV",
                    189990, 48, 20000, "https://example.test/ayvens"
                ),
                (
                    "Ayvens", "Opel", "Combo", "Base", "DIESEL",
                    140990, 48, 20000, "https://example.test/opel"
                ),
            ),
        )
        con.commit()
        con.close()

        service = MarketOverviewService(
            MarketOfferRepository(str(db_path))
        )

        result = service.load()

        assert result.offer_count == 3
        assert result.provider_count == 2
        assert result.median_monthly_fee_huf == 189990
        assert result.offers_by_provider == {
            "Arval": 1,
            "Ayvens": 2,
        }
        assert result.offers_by_fuel_type == {
            "DIESEL": 1,
            "PHEV": 2,
        }

        print("MARKET OVERVIEW V1 TEST PASSED")
        print("Offers:", result.offer_count)
        print("Providers:", result.provider_count)
        print("Average fee:", result.average_monthly_fee_huf)
        print("Median fee:", result.median_monthly_fee_huf)


if __name__ == "__main__":
    main()
