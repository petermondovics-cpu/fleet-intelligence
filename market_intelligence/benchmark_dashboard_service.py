from dataclasses import asdict, dataclass
from typing import Dict, Optional, Tuple

from market_intelligence.benchmark_read_repository import BenchmarkReadRepository

@dataclass(frozen=True)
class BenchmarkDashboardData:
    run: Optional[dict]
    results: Tuple[dict, ...]
    pair_count: int
    evaluated_count: int
    failed_count: int
    price_comparable_count: int
    blocked_count: int
    blocker_counts: Dict[str, int]
    comparison_status_counts: Dict[str, int]
    pair_status_counts: Dict[str, int]
    groups: Tuple[str, ...]
    providers: Tuple[str, ...]
    brands: Tuple[str, ...]
    models: Tuple[str, ...]

class BenchmarkDashboardService:
    def __init__(self, repository=None):
        self.repository = repository or BenchmarkReadRepository()

    def load(self) -> BenchmarkDashboardData:
        run = self.repository.latest_run()
        results = (
            self.repository.results_for_run(run.id)
            if run is not None
            else ()
        )

        blocker_counts = {}
        comparison_status_counts = {}
        pair_status_counts = {}

        for row in results:
            cstatus = row.comparison_status or "UNKNOWN"
            comparison_status_counts[cstatus] = (
                comparison_status_counts.get(cstatus, 0) + 1
            )

            pstatus = row.pair_status or "UNKNOWN"
            pair_status_counts[pstatus] = (
                pair_status_counts.get(pstatus, 0) + 1
            )

            for blocker in row.blockers:
                code = blocker.get("code") or "UNKNOWN_BLOCKER"
                blocker_counts[code] = blocker_counts.get(code, 0) + 1

        price_comparable_count = sum(
            1 for row in results if row.price_comparison_allowed
        )
        evaluated_count = sum(
            1 for row in results if row.bridge_status == "EVALUATED"
        )

        return BenchmarkDashboardData(
            run=asdict(run) if run is not None else None,
            results=tuple(asdict(row) for row in results),
            pair_count=len(results),
            evaluated_count=evaluated_count,
            failed_count=len(results) - evaluated_count,
            price_comparable_count=price_comparable_count,
            blocked_count=len(results) - price_comparable_count,
            blocker_counts=dict(
                sorted(
                    blocker_counts.items(),
                    key=lambda item: (-item[1], item[0]),
                )
            ),
            comparison_status_counts=dict(
                sorted(comparison_status_counts.items())
            ),
            pair_status_counts=dict(
                sorted(pair_status_counts.items())
            ),
            groups=tuple(sorted({r.group_key for r in results if r.group_key})),
            providers=tuple(sorted({
                p for r in results
                for p in (r.left_provider, r.right_provider)
                if p
            })),
            brands=tuple(sorted({r.brand for r in results if r.brand})),
            models=tuple(sorted({r.model for r in results if r.model})),
        )
