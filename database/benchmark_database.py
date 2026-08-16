import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class BenchmarkDatabase:
    """
    Benchmark Persistence V1.

    Stores batch-run metadata and one immutable result row per evaluated
    market pair.

    This database layer does not calculate comparability or price winners.
    It persists decisions already made by the evidence-first comparison
    pipeline.
    """

    def __init__(
        self,
        db_name: str = "fleet.db",
    ):
        self.db_path = Path(db_name)
        self.connection = sqlite3.connect(
            self.db_path
        )
        self.connection.row_factory = (
            sqlite3.Row
        )
        self.create_tables()

    def create_tables(self):
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                started_at TEXT NOT NULL,
                completed_at TEXT,

                status TEXT NOT NULL,

                candidate_count INTEGER NOT NULL DEFAULT 0,
                evaluated_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                price_comparable_count INTEGER NOT NULL DEFAULT 0,

                diagnostic TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS benchmark_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                run_id INTEGER NOT NULL,

                pair_key TEXT NOT NULL,
                group_key TEXT NOT NULL,
                pair_status TEXT NOT NULL,

                brand TEXT,
                model TEXT,
                fuel_type TEXT,

                left_provider TEXT NOT NULL,
                right_provider TEXT NOT NULL,

                left_offer_id TEXT NOT NULL,
                right_offer_id TEXT NOT NULL,

                bridge_status TEXT NOT NULL,
                comparison_status TEXT,

                price_comparison_allowed INTEGER NOT NULL DEFAULT 0,
                price_winner TEXT,

                left_advertised_monthly_fee_huf INTEGER,
                right_advertised_monthly_fee_huf INTEGER,

                left_comparable_monthly_fee_huf INTEGER,
                right_comparable_monthly_fee_huf INTEGER,

                blocker_count INTEGER NOT NULL DEFAULT 0,
                blockers_json TEXT NOT NULL DEFAULT '[]',

                response_json TEXT,

                diagnostic TEXT NOT NULL DEFAULT '',
                observed_at TEXT NOT NULL,

                FOREIGN KEY(run_id)
                    REFERENCES benchmark_runs(id)
            );

            CREATE INDEX IF NOT EXISTS
                idx_benchmark_results_run_id
                ON benchmark_results(run_id);

            CREATE INDEX IF NOT EXISTS
                idx_benchmark_results_pair_key
                ON benchmark_results(pair_key);

            CREATE INDEX IF NOT EXISTS
                idx_benchmark_results_group_key
                ON benchmark_results(group_key);

            CREATE INDEX IF NOT EXISTS
                idx_benchmark_results_comparable
                ON benchmark_results(price_comparison_allowed);

            CREATE INDEX IF NOT EXISTS
                idx_benchmark_results_vehicle
                ON benchmark_results(
                    brand,
                    model,
                    fuel_type
                );
            """
        )

        self.connection.commit()

    def start_run(
        self,
        *,
        candidate_count: int,
    ) -> int:

        cursor = self.connection.execute(
            """
            INSERT INTO benchmark_runs(
                started_at,
                status,
                candidate_count
            )
            VALUES (?, ?, ?)
            """,
            (
                self._now(),
                "RUNNING",
                candidate_count,
            ),
        )

        self.connection.commit()

        return int(
            cursor.lastrowid
        )

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        evaluated_count: int,
        failed_count: int,
        price_comparable_count: int,
        diagnostic: str = "",
    ) -> None:

        self.connection.execute(
            """
            UPDATE benchmark_runs
            SET
                completed_at = ?,
                status = ?,
                evaluated_count = ?,
                failed_count = ?,
                price_comparable_count = ?,
                diagnostic = ?
            WHERE id = ?
            """,
            (
                self._now(),
                status,
                evaluated_count,
                failed_count,
                price_comparable_count,
                diagnostic,
                run_id,
            ),
        )

        self.connection.commit()

    def close(self):
        self.connection.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()
