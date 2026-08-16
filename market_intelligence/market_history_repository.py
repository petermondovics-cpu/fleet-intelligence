from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional, Tuple


@dataclass(frozen=True)
class PriceHistoryRow:
    offer_key: str
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    duration: Optional[int]
    mileage: Optional[int]
    observed_at: str
    monthly_fee: int
    url: str


@dataclass(frozen=True)
class PriceChangeRow:
    offer_key: str
    provider: str
    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]
    duration: Optional[int]
    mileage: Optional[int]
    previous_fee: Optional[int]
    latest_fee: int
    delta_huf: Optional[int]
    delta_percent: Optional[float]
    latest_observed_at: str
    url: str


class MarketHistoryRepository:
    """
    Read-only price-history repository V1.
    """

    def __init__(self, db_name: str = "fleet.db"):
        self.db_path = Path(db_name)

    def price_history(self) -> Tuple[PriceHistoryRow, ...]:
        if not self.db_path.exists():
            return ()

        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row

        try:
            if not self._table_exists(con, "offer_snapshots"):
                return ()

            rows = con.execute(
                """
                SELECT
                    offer_key,
                    provider,
                    brand,
                    model,
                    trim,
                    fuel_type,
                    duration,
                    mileage,
                    observed_at,
                    monthly_fee,
                    url
                FROM offer_snapshots
                ORDER BY offer_key, observed_at
                """
            ).fetchall()

            return tuple(
                PriceHistoryRow(
                    offer_key=row["offer_key"],
                    provider=row["provider"],
                    brand=row["brand"],
                    model=row["model"],
                    trim=row["trim"],
                    fuel_type=row["fuel_type"],
                    duration=row["duration"],
                    mileage=row["mileage"],
                    observed_at=row["observed_at"],
                    monthly_fee=row["monthly_fee"],
                    url=row["url"],
                )
                for row in rows
            )
        finally:
            con.close()

    def latest_changes(self) -> Tuple[PriceChangeRow, ...]:
        history = self.price_history()

        by_key = {}
        for row in history:
            by_key.setdefault(row.offer_key, []).append(row)

        out = []

        for key, rows in by_key.items():
            rows = sorted(rows, key=lambda x: x.observed_at)
            latest = rows[-1]
            previous = rows[-2] if len(rows) >= 2 else None

            prev_fee = previous.monthly_fee if previous else None
            delta = (
                latest.monthly_fee - prev_fee
                if prev_fee is not None
                else None
            )
            delta_pct = (
                round(delta / prev_fee * 100, 2)
                if prev_fee not in (None, 0)
                else None
            )

            out.append(
                PriceChangeRow(
                    offer_key=key,
                    provider=latest.provider,
                    brand=latest.brand,
                    model=latest.model,
                    trim=latest.trim,
                    fuel_type=latest.fuel_type,
                    duration=latest.duration,
                    mileage=latest.mileage,
                    previous_fee=prev_fee,
                    latest_fee=latest.monthly_fee,
                    delta_huf=delta,
                    delta_percent=delta_pct,
                    latest_observed_at=latest.observed_at,
                    url=latest.url,
                )
            )

        return tuple(
            sorted(
                out,
                key=lambda x: (
                    x.provider,
                    x.brand or "",
                    x.model or "",
                ),
            )
        )

    @staticmethod
    def _table_exists(con, table):
        return con.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table' AND name=?
            LIMIT 1
            """,
            (table,),
        ).fetchone() is not None
