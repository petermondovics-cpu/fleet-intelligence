from dataclasses import dataclass
from typing import Optional, Tuple

from database.benchmark_repository import (
    BenchmarkRepository,
)
from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    PAIR_EVALUATED,
    MarketPairFullComparisonBridge,
)


BATCH_COMPLETED = "COMPLETED"
BATCH_PARTIAL = "PARTIAL"
BATCH_FAILED = "FAILED"


@dataclass(frozen=True)
class BenchmarkPairExecution:
    pair_key: str
    group_key: str
    bridge_status: str
    comparison_status: Optional[str]
    price_comparison_allowed: bool
    price_winner: Optional[str]
    diagnostic: str
    stage_timings: Tuple[Tuple[str, float], ...] = ()


@dataclass(frozen=True)
class BenchmarkBatchResult:
    run_id: int
    status: str

    candidate_count: int
    evaluated_count: int
    failed_count: int
    price_comparable_count: int

    executions: Tuple[
        BenchmarkPairExecution,
        ...
    ]


class BenchmarkBatchEngine:
    """
    Automatic Benchmark Batch Engine V1.

    Workflow
    --------
    MarketMatchEngine
      -> full_comparison_candidate pairs
      -> MarketPairFullComparisonBridge
      -> BenchmarkRepository

    Safety
    ------
    - non-candidate pairs are skipped;
    - one pair failure does not abort the whole batch;
    - bridge results are persisted even when evaluation fails;
    - only the FullComparison response may mark a pair price-comparable;
    - the batch engine never derives its own price winner;
    - optional group_key / max_pairs filters make controlled live runs possible.
    """

    def __init__(
        self,
        *,
        match_engine=None,
        bridge=None,
        repository=None,
    ):

        self.match_engine = (
            match_engine
            or MarketMatchEngine()
        )

        self.bridge = (
            bridge
            or MarketPairFullComparisonBridge()
        )

        self.repository = (
            repository
            or BenchmarkRepository()
        )

    def run(
        self,
        *,
        headless: bool = False,
        group_key: Optional[str] = None,
        max_pairs: Optional[int] = None,
    ) -> BenchmarkBatchResult:

        pairs = tuple(
            pair
            for pair in (
                self.match_engine.build()
            )
            if (
                pair.full_comparison_candidate
                and (
                    group_key is None
                    or pair.group_key
                    == group_key
                )
            )
        )

        if (
            max_pairs is not None
            and max_pairs >= 0
        ):
            pairs = pairs[
                :max_pairs
            ]

        run_id = (
            self.repository
            .start_run(
                candidate_count=len(
                    pairs
                )
            )
        )

        executions = []

        evaluated_count = 0
        failed_count = 0
        price_comparable_count = 0

        for pair in pairs:

            try:
                bridge_result = (
                    self.bridge
                    .evaluate(
                        pair,
                        headless=headless,
                    )
                )

            except Exception as exc:
                bridge_result = (
                    _SyntheticBridgeFailure(
                        pair_key=pair.pair_key,
                        status="BRIDGE_EXCEPTION",
                        response=None,
                        diagnostic=(
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    )
                )

            self.repository.save_result(
                run_id=run_id,
                pair=pair,
                bridge_result=bridge_result,
            )

            payload = (
                bridge_result
                .response
                .to_dict()
                if (
                    bridge_result.response
                    is not None
                )
                else None
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

            if (
                bridge_result.status
                == PAIR_EVALUATED
            ):
                evaluated_count += 1
            else:
                failed_count += 1

            if price_allowed:
                price_comparable_count += 1

            executions.append(
                BenchmarkPairExecution(
                    pair_key=pair.pair_key,
                    group_key=pair.group_key,
                    bridge_status=(
                        bridge_result.status
                    ),
                    comparison_status=(
                        comparison_status
                    ),
                    price_comparison_allowed=(
                        price_allowed
                    ),
                    price_winner=(
                        price_winner
                    ),
                    diagnostic=(
                        bridge_result
                        .diagnostic
                    ),
                    stage_timings=tuple(
                        getattr(
                            bridge_result,
                            "stage_timings",
                            (),
                        )
                    ),
                )
            )

        if not pairs:
            batch_status = (
                BATCH_COMPLETED
            )
            diagnostic = (
                "No full-comparison candidate "
                "pairs matched the batch filter."
            )

        elif (
            evaluated_count
            == len(pairs)
        ):
            batch_status = (
                BATCH_COMPLETED
            )
            diagnostic = ""

        elif evaluated_count > 0:
            batch_status = (
                BATCH_PARTIAL
            )
            diagnostic = (
                "At least one market pair "
                "could not be evaluated."
            )

        else:
            batch_status = (
                BATCH_FAILED
            )
            diagnostic = (
                "No market pair completed "
                "full comparison evaluation."
            )

        self.repository.finish_run(
            run_id,
            status=batch_status,
            evaluated_count=evaluated_count,
            failed_count=failed_count,
            price_comparable_count=(
                price_comparable_count
            ),
            diagnostic=diagnostic,
        )

        return BenchmarkBatchResult(
            run_id=run_id,
            status=batch_status,
            candidate_count=len(pairs),
            evaluated_count=evaluated_count,
            failed_count=failed_count,
            price_comparable_count=(
                price_comparable_count
            ),
            executions=tuple(
                executions
            ),
        )

    def close(self):
        self.repository.close()


@dataclass(frozen=True)
class _SyntheticBridgeFailure:
    pair_key: str
    status: str
    response: Optional[object]
    diagnostic: str
