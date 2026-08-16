from pathlib import Path
import json
import tempfile

from database.benchmark_database import BenchmarkDatabase
from market_intelligence.benchmark_dashboard_service import BenchmarkDashboardService
from market_intelligence.benchmark_read_repository import BenchmarkReadRepository

def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "benchmark_dashboard_test.db")
        db = BenchmarkDatabase(db_path)

        run_id = db.start_run(candidate_count=2)

        blockers_1 = [
            {
                "code": "CONTRACT_NORMALIZATION_INCOMPLETE",
                "severity": "EVIDENCE",
                "message": "Duration differs.",
            },
            {
                "code": "SERVICE_EVIDENCE_INCOMPLETE",
                "severity": "EVIDENCE",
                "message": "Services unresolved.",
            },
        ]
        blockers_2 = [
            {
                "code": "CONTRACT_NORMALIZATION_INCOMPLETE",
                "severity": "EVIDENCE",
                "message": "Duration differs.",
            }
        ]

        rows = [
            (
                "PAIR::1", "BYD::ATTO 2::PHEV", "NORMALIZABLE_PAIR",
                "BYD", "ATTO 2", "PHEV", "L1", "R1",
                192312, 189990, blockers_1,
            ),
            (
                "PAIR::2", "OPEL::COMBO::DIESEL", "NORMALIZABLE_PAIR",
                "OPEL", "COMBO", "DIESEL", "L2", "R2",
                135782, 140990, blockers_2,
            ),
        ]

        for (
            pair_key, group_key, pair_status,
            brand, model, fuel, left_id, right_id,
            left_fee, right_fee, blockers
        ) in rows:
            db.connection.execute(
                """
                INSERT INTO benchmark_results(
                    run_id, pair_key, group_key, pair_status,
                    brand, model, fuel_type,
                    left_provider, right_provider,
                    left_offer_id, right_offer_id,
                    bridge_status, comparison_status,
                    price_comparison_allowed, price_winner,
                    left_advertised_monthly_fee_huf,
                    right_advertised_monthly_fee_huf,
                    left_comparable_monthly_fee_huf,
                    right_comparable_monthly_fee_huf,
                    blocker_count, blockers_json, response_json,
                    diagnostic, observed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, pair_key, group_key, pair_status,
                    brand, model, fuel,
                    "Arval", "Ayvens",
                    left_id, right_id,
                    "EVALUATED", "INSUFFICIENT_EVIDENCE",
                    0, None,
                    left_fee, right_fee,
                    None, None,
                    len(blockers), json.dumps(blockers),
                    json.dumps({
                        "status": "INSUFFICIENT_EVIDENCE",
                        "price_comparison_allowed": False,
                        "price_winner": None,
                    }),
                    "ok", db._now(),
                ),
            )

        db.connection.commit()
        db.finish_run(
            run_id,
            status="COMPLETED",
            evaluated_count=2,
            failed_count=0,
            price_comparable_count=0,
            diagnostic="",
        )

        data = BenchmarkDashboardService(
            BenchmarkReadRepository(db_path)
        ).load()

        assert data.pair_count == 2
        assert data.evaluated_count == 2
        assert data.failed_count == 0
        assert data.price_comparable_count == 0
        assert data.blocked_count == 2
        assert data.blocker_counts["CONTRACT_NORMALIZATION_INCOMPLETE"] == 2
        assert data.blocker_counts["SERVICE_EVIDENCE_INCOMPLETE"] == 1
        assert data.comparison_status_counts["INSUFFICIENT_EVIDENCE"] == 2

        db.close()

        print(
            "TEST PASSED - BENCHMARK DASHBOARD SERVICE "
            "AGGREGATES LATEST BATCH KPI, BLOCKERS AND "
            "PAIR RESULTS WITHOUT RECOMPUTING COMPARABILITY."
        )

if __name__ == "__main__":
    main()
