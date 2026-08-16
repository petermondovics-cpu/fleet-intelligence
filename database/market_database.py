import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

class MarketDatabase:
    def __init__(self, db_name: str = "fleet.db"):
        self.db_path = Path(db_name)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS scrape_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            provider_count INTEGER NOT NULL DEFAULT 0,
            offer_count INTEGER NOT NULL DEFAULT 0,
            diagnostics_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS market_current_offers (
            offer_key TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            brand TEXT,
            model TEXT,
            trim TEXT,
            fuel_type TEXT,
            monthly_fee INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            mileage INTEGER NOT NULL,
            url TEXT NOT NULL,
            raw_title TEXT,
            identity_status TEXT NOT NULL,
            identity_method TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            last_seen_run_id INTEGER,
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS offer_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            offer_key TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            provider TEXT NOT NULL,
            brand TEXT,
            model TEXT,
            trim TEXT,
            fuel_type TEXT,
            monthly_fee INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            mileage INTEGER NOT NULL,
            url TEXT NOT NULL,
            raw_title TEXT,
            identity_status TEXT NOT NULL,
            identity_method TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_market_current_provider
            ON market_current_offers(provider);
        CREATE INDEX IF NOT EXISTS idx_market_current_vehicle
            ON market_current_offers(brand, model, duration, mileage);
        CREATE INDEX IF NOT EXISTS idx_offer_snapshots_offer_key
            ON offer_snapshots(offer_key);
        CREATE INDEX IF NOT EXISTS idx_offer_snapshots_run_id
            ON offer_snapshots(run_id);
        """)
        self.connection.commit()

    def start_run(self) -> int:
        cursor = self.connection.execute(
            "INSERT INTO scrape_runs(started_at, status) VALUES (?, ?)",
            (self._now(), "RUNNING"),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        provider_count: int,
        offer_count: int,
        diagnostics: dict,
    ):
        self.connection.execute(
            """
            UPDATE scrape_runs
            SET completed_at=?, status=?, provider_count=?,
                offer_count=?, diagnostics_json=?
            WHERE id=?
            """,
            (
                self._now(),
                status,
                provider_count,
                offer_count,
                json.dumps(diagnostics, ensure_ascii=False),
                run_id,
            ),
        )
        self.connection.commit()

    def close(self):
        self.connection.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
