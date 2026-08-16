from pathlib import Path
import sqlite3
import tempfile

from database.market_repository import MarketRepository
from market_intelligence.market_offer_repository import MarketOfferRepository
from market_intelligence.market_vehicle_normalizer import MarketVehicleNormalizer
from models.offer import Offer

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
        norm = MarketVehicleNormalizer()

        run1 = repo.start_run()
        arval = norm.normalize(
            mk(
                "Arval",
                "BYD ATTO 2",
                192312,
                60,
                "https://www.arval.hu/x/tartos-berleti-ajantlat/byd-atto-2",
            )
        )
        ayvens = norm.normalize(
            mk(
                "Ayvens",
                "BYD ATTO 2 DM-i",
                189990,
                48,
                "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i",
            )
        )
        repo.save_provider_offers(run1, "Arval", (arval,))
        repo.save_provider_offers(run1, "Ayvens", (ayvens,))
        repo.finish_run(
            run1,
            status="COMPLETED",
            provider_count=2,
            offer_count=2,
            diagnostics={},
        )

        current = MarketOfferRepository(db_path).list_offers()
        assert len(current) == 2

        run2 = repo.start_run()
        changed = norm.normalize(
            mk(
                "Ayvens",
                "BYD ATTO 2 DM-i",
                179990,
                48,
                "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i",
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

        current2 = MarketOfferRepository(db_path).list_offers()
        ayvens_rows = [r for r in current2 if r.provider == "Ayvens"]
        arval_rows = [r for r in current2 if r.provider == "Arval"]

        assert len(ayvens_rows) == 1
        assert ayvens_rows[0].monthly_fee == 179990
        assert len(arval_rows) == 1

        con = sqlite3.connect(db_path)
        snapshot_count = con.execute(
            "SELECT COUNT(*) FROM offer_snapshots"
        ).fetchone()[0]
        current_count = con.execute(
            "SELECT COUNT(*) FROM market_current_offers"
        ).fetchone()[0]
        con.close()
        repo.close()

        assert snapshot_count == 3
        assert current_count == 2

        print(
            "TEST PASSED - UNIFIED MARKET PERSISTENCE "
            "DEDUPLICATES CURRENT OFFERS AND PRESERVES "
            "APPEND-ONLY PRICE HISTORY."
        )

if __name__ == "__main__":
    main()
