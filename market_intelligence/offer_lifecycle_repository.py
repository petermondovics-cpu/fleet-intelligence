import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from market_intelligence.exact_offer_lifecycle_resolver import (
    ExactOfferLifecycleResult,
)


@dataclass(frozen=True)
class OfferLifecycleRow:
    id: int
    offer_key: str
    provider: str
    status: str
    checked_url: str
    final_url: Optional[str]
    http_status: Optional[int]
    checked_at: str
    historical_observed_at: Optional[str]
    historical_monthly_fee: Optional[int]
    live_monthly_fee: Optional[int]
    monthly_fee_delta_huf: Optional[int]
    historical_identity: dict
    live_identity: Optional[dict]
    historical_contract: dict
    live_contract: Optional[dict]
    diagnostic: str


class OfferLifecycleRepository:
    """
    Append-only lifecycle persistence V1.

    This repository deliberately does NOT update/delete:
    - offer_snapshots;
    - historical monthly fees;
    - first_seen_at / last_seen_at;
    - market_current_offers.active.

    Lifecycle state is stored as a separate temporal fact.
    Existing market-run logic remains responsible for the current-market
    active flag.
    """

    def __init__(
        self,
        db_name: str = "fleet.db",
    ):
        self.db_path = Path(
            db_name
        )
        self._create_table()

    def save(
        self,
        result: ExactOfferLifecycleResult,
    ) -> int:

        con = sqlite3.connect(
            self.db_path
        )

        try:
            cursor = con.execute(
                """
                INSERT INTO offer_lifecycle_observations(
                    offer_key,
                    provider,
                    status,
                    checked_url,
                    final_url,
                    http_status,
                    checked_at,
                    historical_observed_at,
                    historical_monthly_fee,
                    live_monthly_fee,
                    monthly_fee_delta_huf,
                    historical_identity_json,
                    live_identity_json,
                    historical_contract_json,
                    live_contract_json,
                    diagnostic
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.offer_key,
                    result.provider,
                    result.status,
                    result.checked_url,
                    result.final_url,
                    result.http_status,
                    result.checked_at,
                    result.historical_observed_at,
                    result.historical_monthly_fee,
                    result.live_monthly_fee,
                    result.monthly_fee_delta_huf,
                    json.dumps(
                        result.historical_identity,
                        ensure_ascii=False,
                    ),
                    self._json_or_none(
                        result.live_identity
                    ),
                    json.dumps(
                        result.historical_contract,
                        ensure_ascii=False,
                    ),
                    self._json_or_none(
                        result.live_contract
                    ),
                    result.diagnostic,
                ),
            )

            con.commit()

            return int(
                cursor.lastrowid
            )

        finally:
            con.close()

    def latest_for_offer(
        self,
        offer_key: str,
    ) -> Optional[OfferLifecycleRow]:

        con = sqlite3.connect(
            self.db_path
        )
        con.row_factory = sqlite3.Row

        try:
            row = con.execute(
                """
                SELECT *
                FROM offer_lifecycle_observations
                WHERE offer_key=?
                ORDER BY checked_at DESC, id DESC
                LIMIT 1
                """,
                (
                    offer_key,
                ),
            ).fetchone()

            if row is None:
                return None

            return self._row(
                row
            )

        finally:
            con.close()

    def history_for_offer(
        self,
        offer_key: str,
    ) -> Tuple[
        OfferLifecycleRow,
        ...
    ]:

        con = sqlite3.connect(
            self.db_path
        )
        con.row_factory = sqlite3.Row

        try:
            rows = con.execute(
                """
                SELECT *
                FROM offer_lifecycle_observations
                WHERE offer_key=?
                ORDER BY checked_at, id
                """,
                (
                    offer_key,
                ),
            ).fetchall()

            return tuple(
                self._row(
                    row
                )
                for row in rows
            )

        finally:
            con.close()

    def _create_table(
        self,
    ):
        con = sqlite3.connect(
            self.db_path
        )

        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS offer_lifecycle_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    offer_key TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    checked_url TEXT NOT NULL,
                    final_url TEXT,
                    http_status INTEGER,
                    checked_at TEXT NOT NULL,
                    historical_observed_at TEXT,
                    historical_monthly_fee INTEGER,
                    live_monthly_fee INTEGER,
                    monthly_fee_delta_huf INTEGER,
                    historical_identity_json TEXT NOT NULL,
                    live_identity_json TEXT,
                    historical_contract_json TEXT NOT NULL,
                    live_contract_json TEXT,
                    diagnostic TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_offer_lifecycle_offer
                    ON offer_lifecycle_observations(
                        offer_key,
                        checked_at
                    );

                CREATE INDEX IF NOT EXISTS idx_offer_lifecycle_status
                    ON offer_lifecycle_observations(
                        status,
                        checked_at
                    );
                """
            )

            con.commit()

        finally:
            con.close()

    @classmethod
    def _row(
        cls,
        row,
    ):
        return OfferLifecycleRow(
            id=row["id"],
            offer_key=row["offer_key"],
            provider=row["provider"],
            status=row["status"],
            checked_url=row["checked_url"],
            final_url=row["final_url"],
            http_status=row["http_status"],
            checked_at=row["checked_at"],
            historical_observed_at=row[
                "historical_observed_at"
            ],
            historical_monthly_fee=row[
                "historical_monthly_fee"
            ],
            live_monthly_fee=row[
                "live_monthly_fee"
            ],
            monthly_fee_delta_huf=row[
                "monthly_fee_delta_huf"
            ],
            historical_identity=cls._loads(
                row[
                    "historical_identity_json"
                ]
            ),
            live_identity=cls._loads(
                row[
                    "live_identity_json"
                ]
            ),
            historical_contract=cls._loads(
                row[
                    "historical_contract_json"
                ]
            ),
            live_contract=cls._loads(
                row[
                    "live_contract_json"
                ]
            ),
            diagnostic=row["diagnostic"],
        )

    @staticmethod
    def _loads(
        value,
    ):
        if value is None:
            return None

        try:
            return json.loads(
                value
            )
        except Exception:
            return None

    @staticmethod
    def _json_or_none(
        value,
    ):
        if value is None:
            return None

        return json.dumps(
            value,
            ensure_ascii=False,
        )
