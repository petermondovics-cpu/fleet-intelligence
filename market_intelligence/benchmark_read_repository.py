import json
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Optional, Tuple

@dataclass(frozen=True)
class BenchmarkRunRow:
    id: int
    started_at: str
    completed_at: Optional[str]
    status: str
    candidate_count: int
    evaluated_count: int
    failed_count: int
    price_comparable_count: int
    diagnostic: str

@dataclass(frozen=True)
class BenchmarkResultRow:
    id: int
    run_id: int
    pair_key: str
    group_key: str
    pair_status: str
    brand: Optional[str]
    model: Optional[str]
    fuel_type: Optional[str]
    left_provider: str
    right_provider: str
    bridge_status: str
    comparison_status: Optional[str]
    price_comparison_allowed: bool
    price_winner: Optional[str]
    left_advertised_monthly_fee_huf: Optional[int]
    right_advertised_monthly_fee_huf: Optional[int]
    left_comparable_monthly_fee_huf: Optional[int]
    right_comparable_monthly_fee_huf: Optional[int]
    blocker_count: int
    blockers: Tuple[dict, ...]
    response: Optional[dict]
    diagnostic: str
    observed_at: str

class BenchmarkReadRepository:
    def __init__(self, db_name: str = "fleet.db"):
        self.db_path = Path(db_name)

    def latest_run(self) -> Optional[BenchmarkRunRow]:
        if not self.db_path.exists():
            return None
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            if not self._table_exists(con, "benchmark_runs"):
                return None
            row = con.execute(
                """
                SELECT id, started_at, completed_at, status,
                       candidate_count, evaluated_count, failed_count,
                       price_comparable_count, diagnostic
                FROM benchmark_runs
                WHERE status != 'RUNNING'
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            return BenchmarkRunRow(
                id=row["id"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                status=row["status"],
                candidate_count=row["candidate_count"],
                evaluated_count=row["evaluated_count"],
                failed_count=row["failed_count"],
                price_comparable_count=row["price_comparable_count"],
                diagnostic=row["diagnostic"],
            )
        finally:
            con.close()

    def results_for_run(self, run_id: int) -> Tuple[BenchmarkResultRow, ...]:
        if not self.db_path.exists():
            return ()
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            if not self._table_exists(con, "benchmark_results"):
                return ()
            rows = con.execute(
                """
                SELECT id, run_id, pair_key, group_key, pair_status,
                       brand, model, fuel_type,
                       left_provider, right_provider,
                       bridge_status, comparison_status,
                       price_comparison_allowed, price_winner,
                       left_advertised_monthly_fee_huf,
                       right_advertised_monthly_fee_huf,
                       left_comparable_monthly_fee_huf,
                       right_comparable_monthly_fee_huf,
                       blocker_count, blockers_json, response_json,
                       diagnostic, observed_at
                FROM benchmark_results
                WHERE run_id = ?
                ORDER BY brand, model, fuel_type, pair_key
                """,
                (run_id,),
            ).fetchall()
            return tuple(self._result_row(row) for row in rows)
        finally:
            con.close()

    def latest_results(self) -> Tuple[BenchmarkResultRow, ...]:
        run = self.latest_run()
        if run is None:
            return ()
        return self.results_for_run(run.id)

    @staticmethod
    def _result_row(row) -> BenchmarkResultRow:
        blockers = ()
        raw_blockers = row["blockers_json"]
        if raw_blockers:
            try:
                value = json.loads(raw_blockers)
                if isinstance(value, list):
                    blockers = tuple(
                        item for item in value if isinstance(item, dict)
                    )
            except Exception:
                blockers = ()

        response = None
        raw_response = row["response_json"]
        if raw_response:
            try:
                value = json.loads(raw_response)
                if isinstance(value, dict):
                    response = value
            except Exception:
                response = None

        return BenchmarkResultRow(
            id=row["id"],
            run_id=row["run_id"],
            pair_key=row["pair_key"],
            group_key=row["group_key"],
            pair_status=row["pair_status"],
            brand=row["brand"],
            model=row["model"],
            fuel_type=row["fuel_type"],
            left_provider=row["left_provider"],
            right_provider=row["right_provider"],
            bridge_status=row["bridge_status"],
            comparison_status=row["comparison_status"],
            price_comparison_allowed=bool(row["price_comparison_allowed"]),
            price_winner=row["price_winner"],
            left_advertised_monthly_fee_huf=row["left_advertised_monthly_fee_huf"],
            right_advertised_monthly_fee_huf=row["right_advertised_monthly_fee_huf"],
            left_comparable_monthly_fee_huf=row["left_comparable_monthly_fee_huf"],
            right_comparable_monthly_fee_huf=row["right_comparable_monthly_fee_huf"],
            blocker_count=row["blocker_count"],
            blockers=blockers,
            response=response,
            diagnostic=row["diagnostic"],
            observed_at=row["observed_at"],
        )

    @staticmethod
    def _table_exists(con, table: str) -> bool:
        return con.execute(
            """
            SELECT 1 FROM sqlite_master
            WHERE type='table' AND name=?
            LIMIT 1
            """,
            (table,),
        ).fetchone() is not None
