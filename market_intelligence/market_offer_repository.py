from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional, Tuple

@dataclass(frozen=True)
class MarketOfferRow:
    id: str
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    monthly_fee: Optional[int]
    duration: Optional[int]
    mileage: Optional[int]
    url: Optional[str]
    identity_status: Optional[str] = None
    identity_method: Optional[str] = None
    last_seen_at: Optional[str] = None

class MarketOfferRepository:
    def __init__(self, db_name: str = "fleet.db"):
        self.db_path = Path(db_name)

    def list_offers(self) -> Tuple[MarketOfferRow, ...]:
        if not self.db_path.exists():
            return ()

        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row

        try:
            if self._table_exists(connection, "market_current_offers"):
                rows = connection.execute(
                    """
                    SELECT
                        offer_key AS id,
                        provider,
                        brand,
                        model,
                        trim,
                        fuel_type,
                        monthly_fee,
                        duration,
                        mileage,
                        url,
                        identity_status,
                        identity_method,
                        last_seen_at
                    FROM market_current_offers
                    WHERE active = 1
                    ORDER BY provider, brand, model, trim, duration, mileage, monthly_fee
                    """
                ).fetchall()

                return tuple(
                    MarketOfferRow(
                        id=str(row["id"]),
                        provider=row["provider"] or "UNKNOWN",
                        brand=row["brand"],
                        model=row["model"],
                        trim=row["trim"],
                        fuel_type=row["fuel_type"],
                        monthly_fee=row["monthly_fee"],
                        duration=row["duration"],
                        mileage=row["mileage"],
                        url=row["url"],
                        identity_status=row["identity_status"],
                        identity_method=row["identity_method"],
                        last_seen_at=row["last_seen_at"],
                    )
                    for row in rows
                )

            if self._table_exists(connection, "offers"):
                rows = connection.execute(
                    """
                    SELECT id, provider, brand, model, trim, fuel_type,
                           monthly_fee, duration, mileage, url
                    FROM offers
                    ORDER BY provider, brand, model, trim, monthly_fee
                    """
                ).fetchall()

                return tuple(
                    MarketOfferRow(
                        id=str(row["id"]),
                        provider=row["provider"] or "UNKNOWN",
                        brand=row["brand"],
                        model=row["model"],
                        trim=row["trim"],
                        fuel_type=row["fuel_type"],
                        monthly_fee=row["monthly_fee"],
                        duration=row["duration"],
                        mileage=row["mileage"],
                        url=row["url"],
                        identity_status=None,
                        identity_method="LEGACY",
                        last_seen_at=None,
                    )
                    for row in rows
                )

            return ()
        finally:
            connection.close()

    @staticmethod
    def _table_exists(connection, table: str) -> bool:
        return connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name=?
            LIMIT 1
            """,
            (table,),
        ).fetchone() is not None
