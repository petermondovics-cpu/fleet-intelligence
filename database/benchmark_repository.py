import json
from dataclasses import dataclass
from typing import Optional, Tuple

from database.benchmark_database import (
    BenchmarkDatabase,
)


@dataclass(frozen=True)
class PersistedBenchmarkResult:
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

    blocker_count: int
    diagnostic: str

    observed_at: str


class BenchmarkRepository:
    """
    Benchmark Repository V1.

    Persists one observation for every batch-evaluated market pair.
    Historical benchmark results are append-only.
    """

    def __init__(
        self,
        db_name: str = "fleet.db",
    ):
        self.db = BenchmarkDatabase(
            db_name
        )

    def start_run(
        self,
        *,
        candidate_count: int,
    ) -> int:
        return self.db.start_run(
            candidate_count=candidate_count
        )

    def save_result(
        self,
        *,
        run_id: int,
        pair,
        bridge_result,
    ) -> int:

        payload = None

        if (
            bridge_result.response
            is not None
        ):
            payload = (
                bridge_result
                .response
                .to_dict()
            )

        blockers = (
            payload.get(
                "blockers",
                (),
            )
            if payload
            else ()
        )

        left_price = (
            payload.get(
                "left_offer",
                {},
            ).get(
                "price",
                {},
            )
            if payload
            else {}
        )

        right_price = (
            payload.get(
                "right_offer",
                {},
            ).get(
                "price",
                {},
            )
            if payload
            else {}
        )

        comparison_status = (
            payload.get("status")
            if payload
            else None
        )

        price_allowed = bool(
            payload.get(
                "price_comparison_allowed",
                False,
            )
            if payload
            else False
        )

        price_winner = (
            payload.get(
                "price_winner"
            )
            if payload
            else None
        )

        cursor = (
            self.db.connection.execute(
                """
                INSERT INTO benchmark_results(
                    run_id,
                    pair_key,
                    group_key,
                    pair_status,

                    brand,
                    model,
                    fuel_type,

                    left_provider,
                    right_provider,

                    left_offer_id,
                    right_offer_id,

                    bridge_status,
                    comparison_status,

                    price_comparison_allowed,
                    price_winner,

                    left_advertised_monthly_fee_huf,
                    right_advertised_monthly_fee_huf,

                    left_comparable_monthly_fee_huf,
                    right_comparable_monthly_fee_huf,

                    blocker_count,
                    blockers_json,
                    response_json,

                    diagnostic,
                    observed_at
                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    run_id,
                    pair.pair_key,
                    pair.group_key,
                    pair.pair_status,

                    pair.brand,
                    pair.model,
                    pair.fuel_type,

                    pair.left_provider,
                    pair.right_provider,

                    pair.left_offer_id,
                    pair.right_offer_id,

                    bridge_result.status,
                    comparison_status,

                    1 if price_allowed else 0,
                    price_winner,

                    left_price.get(
                        "advertised_monthly_fee_huf"
                    ),
                    right_price.get(
                        "advertised_monthly_fee_huf"
                    ),

                    left_price.get(
                        "comparable_monthly_fee_huf"
                    ),
                    right_price.get(
                        "comparable_monthly_fee_huf"
                    ),

                    len(blockers),
                    json.dumps(
                        blockers,
                        ensure_ascii=False,
                        default=str,
                    ),
                    (
                        json.dumps(
                            payload,
                            ensure_ascii=False,
                            default=str,
                        )
                        if payload
                        else None
                    ),

                    bridge_result.diagnostic,
                    self.db._now(),
                ),
            )
        )

        self.db.connection.commit()

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

        self.db.finish_run(
            run_id,
            status=status,
            evaluated_count=evaluated_count,
            failed_count=failed_count,
            price_comparable_count=price_comparable_count,
            diagnostic=diagnostic,
        )

    def latest_results(
        self,
    ) -> Tuple[
        PersistedBenchmarkResult,
        ...
    ]:

        row = (
            self.db.connection.execute(
                """
                SELECT MAX(id)
                FROM benchmark_runs
                WHERE status != 'RUNNING'
                """
            )
            .fetchone()
        )

        if (
            row is None
            or row[0] is None
        ):
            return ()

        run_id = int(
            row[0]
        )

        rows = (
            self.db.connection.execute(
                """
                SELECT
                    id,
                    run_id,
                    pair_key,
                    group_key,
                    pair_status,
                    brand,
                    model,
                    fuel_type,
                    left_provider,
                    right_provider,
                    bridge_status,
                    comparison_status,
                    price_comparison_allowed,
                    price_winner,
                    blocker_count,
                    diagnostic,
                    observed_at
                FROM benchmark_results
                WHERE run_id = ?
                ORDER BY
                    brand,
                    model,
                    fuel_type,
                    pair_key
                """,
                (run_id,),
            )
            .fetchall()
        )

        return tuple(
            PersistedBenchmarkResult(
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
                price_comparison_allowed=bool(
                    row[
                        "price_comparison_allowed"
                    ]
                ),
                price_winner=row["price_winner"],
                blocker_count=row["blocker_count"],
                diagnostic=row["diagnostic"],
                observed_at=row["observed_at"],
            )
            for row in rows
        )

    def close(self):
        self.db.close()
