from dataclasses import asdict, dataclass
from statistics import median
from typing import Dict, Optional, Tuple

from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
    MarketOfferRow,
)


@dataclass(frozen=True)
class MarketOverview:
    offers: Tuple[dict, ...]
    offer_count: int
    provider_count: int
    average_monthly_fee_huf: Optional[int]
    median_monthly_fee_huf: Optional[int]
    providers: Tuple[str, ...]
    brands: Tuple[str, ...]
    models: Tuple[str, ...]
    fuel_types: Tuple[str, ...]
    durations: Tuple[int, ...]
    mileages: Tuple[int, ...]
    offers_by_provider: Dict[str, int]
    offers_by_fuel_type: Dict[str, int]


class MarketOverviewService:
    """
    Market Overview V1.

    Important:
    - This layer reports only facts persisted in the existing offers table.
    - It does not invent evidence/comparability statuses that are not stored.
    - Evidence completeness and blocker analytics belong to a later
      evidence-aware market persistence layer.
    """

    def __init__(self, repository=None):
        self.repository = repository or MarketOfferRepository()

    def load(self) -> MarketOverview:
        rows = self.repository.list_offers()

        fees = [
            row.monthly_fee
            for row in rows
            if row.monthly_fee is not None
        ]

        providers = self._unique_text(rows, "provider")
        brands = self._unique_text(rows, "brand")
        models = self._unique_text(rows, "model")
        fuel_types = self._unique_text(rows, "fuel_type")

        durations = tuple(sorted({
            row.duration
            for row in rows
            if row.duration is not None
        }))

        mileages = tuple(sorted({
            row.mileage
            for row in rows
            if row.mileage is not None
        }))

        offers_by_provider = self._counts(rows, "provider")
        offers_by_fuel_type = self._counts(rows, "fuel_type")

        average_fee = (
            round(sum(fees) / len(fees))
            if fees
            else None
        )

        median_fee = (
            round(median(fees))
            if fees
            else None
        )

        return MarketOverview(
            offers=tuple(asdict(row) for row in rows),
            offer_count=len(rows),
            provider_count=len(providers),
            average_monthly_fee_huf=average_fee,
            median_monthly_fee_huf=median_fee,
            providers=providers,
            brands=brands,
            models=models,
            fuel_types=fuel_types,
            durations=durations,
            mileages=mileages,
            offers_by_provider=offers_by_provider,
            offers_by_fuel_type=offers_by_fuel_type,
        )

    @staticmethod
    def _unique_text(rows, field):
        return tuple(sorted({
            value
            for row in rows
            if (value := getattr(row, field, None))
        }))

    @staticmethod
    def _counts(rows, field):
        counts = {}

        for row in rows:
            value = getattr(row, field, None) or "UNKNOWN"
            counts[value] = counts.get(value, 0) + 1

        return dict(sorted(counts.items()))
