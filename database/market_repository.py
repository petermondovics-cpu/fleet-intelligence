import hashlib
from typing import Iterable

from database.market_database import MarketDatabase
from market_intelligence.market_vehicle_normalizer import NormalizedMarketOffer

class MarketRepository:
    def __init__(self, db_name: str = "fleet.db"):
        self.db = MarketDatabase(db_name)

    def start_run(self) -> int:
        return self.db.start_run()

    def save_provider_offers(
        self,
        run_id: int,
        provider: str,
        offers: Iterable[NormalizedMarketOffer],
    ) -> int:
        items = tuple(offers)
        now = self.db._now()
        con = self.db.connection

        try:
            con.execute("BEGIN")
            con.execute(
                "UPDATE market_current_offers SET active=0 WHERE provider=?",
                (provider,),
            )

            for offer in items:
                key = self.offer_key(offer)

                con.execute(
                    """
                    INSERT INTO offer_snapshots(
                        run_id, offer_key, observed_at, provider,
                        brand, model, trim, fuel_type,
                        monthly_fee, duration, mileage, url,
                        raw_title, identity_status, identity_method
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id, key, now, offer.provider,
                        offer.brand, offer.model, offer.trim, offer.fuel_type,
                        offer.monthly_fee, offer.duration, offer.mileage,
                        offer.url, offer.raw_title,
                        offer.identity_status, offer.identity_method,
                    ),
                )

                con.execute(
                    """
                    INSERT INTO market_current_offers(
                        offer_key, provider, brand, model, trim, fuel_type,
                        monthly_fee, duration, mileage, url, raw_title,
                        identity_status, identity_method,
                        first_seen_at, last_seen_at, last_seen_run_id, active
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(offer_key) DO UPDATE SET
                        brand=excluded.brand,
                        model=excluded.model,
                        trim=excluded.trim,
                        fuel_type=excluded.fuel_type,
                        monthly_fee=excluded.monthly_fee,
                        duration=excluded.duration,
                        mileage=excluded.mileage,
                        url=excluded.url,
                        raw_title=excluded.raw_title,
                        identity_status=excluded.identity_status,
                        identity_method=excluded.identity_method,
                        last_seen_at=excluded.last_seen_at,
                        last_seen_run_id=excluded.last_seen_run_id,
                        active=1
                    """,
                    (
                        key, offer.provider, offer.brand, offer.model,
                        offer.trim, offer.fuel_type, offer.monthly_fee,
                        offer.duration, offer.mileage, offer.url,
                        offer.raw_title, offer.identity_status,
                        offer.identity_method, now, now, run_id,
                    ),
                )

            con.commit()
        except Exception:
            con.rollback()
            raise

        return len(items)

    def finish_run(self, run_id: int, **kwargs):
        self.db.finish_run(run_id, **kwargs)

    def close(self):
        self.db.close()

    @staticmethod
    def offer_key(offer: NormalizedMarketOffer) -> str:
        parts = (
            offer.provider or "",
            offer.brand or "",
            offer.model or "",
            offer.trim or "",
            offer.fuel_type or "",
            str(offer.duration),
            str(offer.mileage),
            offer.url or "",
        )
        raw = "|".join(v.strip().casefold() for v in parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
