from dataclasses import dataclass
from typing import Dict, Tuple

from database.market_repository import MarketRepository
from market_intelligence.market_vehicle_normalizer import (
    MarketVehicleNormalizer,
)
from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper


@dataclass(frozen=True)
class ProviderCollectionResult:
    provider: str
    status: str
    raw_count: int
    normalized_count: int
    diagnostic: str = ""


@dataclass(frozen=True)
class UnifiedMarketCollectionResult:
    run_id: int
    status: str
    provider_results: Tuple[
        ProviderCollectionResult,
        ...
    ]
    total_offers: int


class UnifiedMarketCollector:
    """
    Unified Market Collector V2b.

    Route policy:
    - provider-resolved Offer.url is persisted as observed;
    - no generic Arval path-shape canonicalization occurs here;
    - the Arval scraper/route resolver is responsible for proving a live
      exact-offer route before an Offer reaches this layer.
    """

    def __init__(
        self,
        *,
        repository=None,
        normalizer=None,
        scrapers=None,
    ):
        self.repository = (
            repository
            or MarketRepository()
        )

        self.normalizer = (
            normalizer
            or MarketVehicleNormalizer()
        )

        self.scrapers = (
            scrapers
            or (
                (
                    "Arval",
                    ArvalScraper(),
                ),
                (
                    "Ayvens",
                    AyvensScraper(),
                ),
            )
        )

    def run(
        self,
    ) -> UnifiedMarketCollectionResult:

        run_id = (
            self.repository
            .start_run()
        )

        results = []
        diagnostics: Dict[
            str,
            str,
        ] = {}

        total = 0
        successful = 0

        try:

            for provider, scraper in self.scrapers:

                try:

                    raw_offers = tuple(
                        scraper.collect()
                    )

                    normalized = tuple(
                        self.normalizer.normalize(
                            offer
                        )
                        for offer in raw_offers
                    )

                    saved = (
                        self.repository
                        .save_provider_offers(
                            run_id,
                            provider,
                            normalized,
                        )
                    )

                    successful += 1
                    total += saved

                    results.append(
                        ProviderCollectionResult(
                            provider=provider,
                            status="COLLECTED",
                            raw_count=len(
                                raw_offers
                            ),
                            normalized_count=saved,
                        )
                    )

                except Exception as exc:

                    message = (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    )

                    diagnostics[
                        provider
                    ] = message

                    results.append(
                        ProviderCollectionResult(
                            provider=provider,
                            status="FAILED",
                            raw_count=0,
                            normalized_count=0,
                            diagnostic=message,
                        )
                    )

            if successful == len(
                self.scrapers
            ):
                status = "COMPLETED"

            elif successful > 0:
                status = "PARTIAL"

            else:
                status = "FAILED"

            self.repository.finish_run(
                run_id,
                status=status,
                provider_count=successful,
                offer_count=total,
                diagnostics=diagnostics,
            )

            return (
                UnifiedMarketCollectionResult(
                    run_id=run_id,
                    status=status,
                    provider_results=tuple(
                        results
                    ),
                    total_offers=total,
                )
            )

        except Exception as exc:

            try:
                self.repository.finish_run(
                    run_id,
                    status="FAILED",
                    provider_count=successful,
                    offer_count=total,
                    diagnostics={
                        **diagnostics,
                        "_orchestrator": (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    },
                )
            finally:
                raise

    def close(
        self,
    ):
        self.repository.close()
