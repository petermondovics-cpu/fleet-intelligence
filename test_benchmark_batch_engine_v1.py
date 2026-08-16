from pathlib import Path
from types import SimpleNamespace
import tempfile

from database.benchmark_repository import (
    BenchmarkRepository,
)
from market_intelligence.benchmark_batch_engine import (
    BATCH_PARTIAL,
    BenchmarkBatchEngine,
)
from market_intelligence.market_match_engine import (
    MarketOfferPair,
)


def pair(
    suffix,
    *,
    candidate=True,
):
    return MarketOfferPair(
        pair_key=f"PAIR::{suffix}",
        group_key=f"BYD::ATTO 2::PHEV::{suffix}",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        left_provider="Arval",
        right_provider="Ayvens",
        left_offer_id=f"L::{suffix}",
        right_offer_id=f"R::{suffix}",
        left_monthly_fee=192312,
        right_monthly_fee=189990,
        left_duration=60,
        right_duration=48,
        left_mileage=20000,
        right_mileage=20000,
        left_trim=None,
        right_trim="Active 166 HP",
        left_url="https://example.test/arval",
        right_url="https://example.test/ayvens",
        contract_exact=False,
        duration_exact=False,
        mileage_exact=True,
        trim_exact=False,
        pair_status="NORMALIZABLE_PAIR",
        full_comparison_candidate=candidate,
        price_comparison_allowed=False,
        diagnostic="Test pair.",
    )


class FakeMatchEngine:
    def build(self):
        return (
            pair("OK"),
            pair("FAIL"),
            pair(
                "SKIP",
                candidate=False,
            ),
        )


class FakeResponse:
    def __init__(
        self,
        *,
        allowed,
        winner,
        status,
    ):
        self.allowed = allowed
        self.winner = winner
        self.status = status

    def to_dict(self):
        return {
            "api_version": "comparison.v1",
            "status": self.status,
            "price_comparison_allowed": self.allowed,
            "price_winner": self.winner,
            "left_offer": {
                "provider": "Arval",
                "price": {
                    "advertised_monthly_fee_huf": 192312,
                    "comparable_monthly_fee_huf": None,
                },
            },
            "right_offer": {
                "provider": "Ayvens",
                "price": {
                    "advertised_monthly_fee_huf": 189990,
                    "comparable_monthly_fee_huf": None,
                },
            },
            "blockers": (
                {
                    "code": "CONTRACT_NORMALIZATION_INCOMPLETE",
                    "severity": "EVIDENCE",
                    "message": "Duration differs.",
                },
            ),
        }


class FakeBridge:
    def evaluate(
        self,
        pair,
        *,
        headless=False,
    ):
        if pair.pair_key.endswith(
            "FAIL"
        ):
            return SimpleNamespace(
                pair_key=pair.pair_key,
                status="LOAD_FAILED",
                response=None,
                diagnostic="Synthetic load failure.",
            )

        return SimpleNamespace(
            pair_key=pair.pair_key,
            status="EVALUATED",
            response=FakeResponse(
                allowed=False,
                winner=None,
                status="INSUFFICIENT_EVIDENCE",
            ),
            diagnostic="Synthetic evaluation completed.",
        )


def main():

    with tempfile.TemporaryDirectory() as tmp:

        db_path = str(
            Path(tmp)
            / "benchmark_test.db"
        )

        repository = (
            BenchmarkRepository(
                db_path
            )
        )

        engine = BenchmarkBatchEngine(
            match_engine=FakeMatchEngine(),
            bridge=FakeBridge(),
            repository=repository,
        )

        result = engine.run(
            headless=True
        )

        assert (
            result.status
            == BATCH_PARTIAL
        )

        assert (
            result.candidate_count
            == 2
        )

        assert (
            result.evaluated_count
            == 1
        )

        assert (
            result.failed_count
            == 1
        )

        assert (
            result.price_comparable_count
            == 0
        )

        # The non-candidate pair must never enter the batch.
        assert all(
            "SKIP" not in execution.pair_key
            for execution in result.executions
        )

        persisted = (
            repository
            .latest_results()
        )

        assert len(
            persisted
        ) == 2

        evaluated = [
            row
            for row in persisted
            if (
                row.bridge_status
                == "EVALUATED"
            )
        ]

        failed = [
            row
            for row in persisted
            if (
                row.bridge_status
                != "EVALUATED"
            )
        ]

        assert len(evaluated) == 1
        assert len(failed) == 1

        assert (
            evaluated[0]
            .comparison_status
            == "INSUFFICIENT_EVIDENCE"
        )

        assert (
            evaluated[0]
            .price_comparison_allowed
            is False
        )

        assert (
            evaluated[0]
            .price_winner
            is None
        )

        engine.close()

        print(
            "TEST PASSED - BENCHMARK BATCH ENGINE "
            "EVALUATES ONLY FULL-COMPARISON CANDIDATES, "
            "PERSISTS SUCCESS + FAILURE RESULTS, "
            "CONTINUES AFTER PAIR FAILURE, AND NEVER "
            "FABRICATES PRICE COMPARABILITY."
        )


if __name__ == "__main__":
    main()
