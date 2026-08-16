from pathlib import Path
import tempfile

from database.market_repository import MarketRepository
from market_intelligence.market_dashboard_service import (
    MarketDashboardService,
)
from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
)
from market_intelligence.market_history_repository import (
    MarketHistoryRepository,
)
from market_intelligence.market_vehicle_normalizer import (
    MarketVehicleNormalizer,
)
from models.offer import Offer


def mk(provider, title, fee, duration, url, fuel="PHEV"):
    return Offer(
        provider=provider,
        brand="",
        model=title,
        trim="",
        fuel_type=fuel,
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
        norm = MarketVehicleNormalizer()

        run1 = repo.start_run()
        rows = (
            norm.normalize(
                mk(
                    "Arval",
                    "BYD ATTO 2",
                    192312,
                    60,
                    "https://example.test/arval",
                )
            ),
            norm.normalize(
                mk(
                    "Ayvens",
                    "BYD ATTO 2 DM-i",
                    189990,
                    48,
                    "https://example.test/ayvens",
                )
            ),
        )

        repo.save_provider_offers(run1, "Arval", (rows[0],))
        repo.save_provider_offers(run1, "Ayvens", (rows[1],))
        repo.finish_run(
            run1,
            status="COMPLETED",
            provider_count=2,
            offer_count=2,
            diagnostics={},
        )

        run2 = repo.start_run()
        changed = norm.normalize(
            mk(
                "Ayvens",
                "BYD ATTO 2 DM-i",
                179990,
                48,
                "https://example.test/ayvens",
            )
        )
        repo.save_provider_offers(run2, "Ayvens", (changed,))
        repo.finish_run(
            run2,
            status="COMPLETED",
            provider_count=1,
            offer_count=1,
            diagnostics={},
        )

        service = MarketDashboardService(
            offer_repository=MarketOfferRepository(db_path),
            history_repository=MarketHistoryRepository(db_path),
        )
        data = service.load()

        assert data.offer_count == 2
        assert data.provider_count == 2
        assert len(data.history) == 3

        ayvens_change = [
            item
            for item in data.changes
            if item["provider"] == "Ayvens"
        ][0]

        assert ayvens_change["previous_fee"] == 189990
        assert ayvens_change["latest_fee"] == 179990
        assert ayvens_change["delta_huf"] == -10000

        repo.close()

        print(
            "TEST PASSED - MARKET DASHBOARD SERVICE "
            "EXPOSES CURRENT MARKET, PROVIDER METRICS, "
            "AND PRICE HISTORY."
        )


if __name__ == "__main__":
    main()
