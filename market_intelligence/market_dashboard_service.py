from dataclasses import asdict, dataclass
from statistics import median
from typing import Dict, Optional, Tuple

from market_intelligence.market_offer_repository import (
    MarketOfferRepository,
)
from market_intelligence.market_history_repository import (
    MarketHistoryRepository,
)


@dataclass(frozen=True)
class MarketDashboardData:
    offers: Tuple[dict, ...]
    history: Tuple[dict, ...]
    changes: Tuple[dict, ...]
    offer_count: int
    provider_count: int
    average_monthly_fee_huf: Optional[int]
    median_monthly_fee_huf: Optional[int]
    provider_metrics: Dict[str, dict]
    fuel_counts: Dict[str, int]
    brands: Tuple[str, ...]
    models: Tuple[str, ...]
    providers: Tuple[str, ...]


class MarketDashboardService:
    """
    Market Intelligence Dashboard Service V1.

    Uses persisted current-market rows and append-only price snapshots.
    Does not infer comparability or evidence completeness that is not stored.
    """

    def __init__(
        self,
        offer_repository=None,
        history_repository=None,
    ):
        self.offers_repo = (
            offer_repository
            or MarketOfferRepository()
        )
        self.history_repo = (
            history_repository
            or MarketHistoryRepository()
        )

    def load(self) -> MarketDashboardData:
        offers = self.offers_repo.list_offers()
        history = self.history_repo.price_history()
        changes = self.history_repo.latest_changes()

        fees = [
            row.monthly_fee
            for row in offers
            if row.monthly_fee is not None
        ]

        providers = tuple(sorted({
            row.provider
            for row in offers
            if row.provider
        }))

        brands = tuple(sorted({
            row.brand
            for row in offers
            if row.brand
        }))

        models = tuple(sorted({
            row.model
            for row in offers
            if row.model
        }))

        provider_metrics = {}

        for provider in providers:
            rows = [
                row
                for row in offers
                if row.provider == provider
            ]
            pfees = [
                row.monthly_fee
                for row in rows
                if row.monthly_fee is not None
            ]

            provider_metrics[provider] = {
                "offer_count": len(rows),
                "average_monthly_fee_huf": (
                    round(sum(pfees) / len(pfees))
                    if pfees else None
                ),
                "median_monthly_fee_huf": (
                    round(median(pfees))
                    if pfees else None
                ),
                "min_monthly_fee_huf": (
                    min(pfees)
                    if pfees else None
                ),
                "max_monthly_fee_huf": (
                    max(pfees)
                    if pfees else None
                ),
            }

        fuel_counts = {}
        for row in offers:
            key = row.fuel_type or "UNKNOWN"
            fuel_counts[key] = fuel_counts.get(key, 0) + 1

        return MarketDashboardData(
            offers=tuple(asdict(row) for row in offers),
            history=tuple(asdict(row) for row in history),
            changes=tuple(asdict(row) for row in changes),
            offer_count=len(offers),
            provider_count=len(providers),
            average_monthly_fee_huf=(
                round(sum(fees) / len(fees))
                if fees else None
            ),
            median_monthly_fee_huf=(
                round(median(fees))
                if fees else None
            ),
            provider_metrics=provider_metrics,
            fuel_counts=dict(sorted(fuel_counts.items())),
            brands=brands,
            models=models,
            providers=providers,
        )
