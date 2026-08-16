from dataclasses import dataclass
from typing import List

from models.offer import Offer

from comparison.engine import ComparisonEngine
from benchmark.engine import BenchmarkEngine
from positioning.engine import MarketPositioningEngine
from ranking.engine import RankingEngine
from contract_normalization.engine import (
    ContractNormalizationEngine,
)


@dataclass
class MarketIntelligenceResult:

    offers_count: int
    benchmark_count: int
    comparison_count: int

    comparable_comparisons: int
    non_comparable_comparisons: int

    benchmark_results: list
    positioning_results: list
    ranking_results: list
    normalization_results: list

    # ------------------------------------------------
    # CONTRACT NORMALIZATION V3 METRICS
    # ------------------------------------------------

    normalized_comparisons: int
    estimated_normalizations: int

    term_normalizations_required: int
    mileage_normalizations_required: int
    term_and_mileage_normalizations_required: int

    unsupported_normalizations: int


class MarketIntelligenceEngine:

    def __init__(self):

        self.comparison_engine = (
            ComparisonEngine()
        )

        self.benchmark_engine = (
            BenchmarkEngine()
        )

        self.positioning_engine = (
            MarketPositioningEngine()
        )

        self.ranking_engine = (
            RankingEngine()
        )

        self.normalization_engine = (
            ContractNormalizationEngine()
        )

    def analyze(
        self,
        offers: List[Offer],
    ) -> MarketIntelligenceResult:

        # ------------------------------------------------
        # COMPARISON
        # ------------------------------------------------

        comparisons = (
            self.comparison_engine.compare(
                offers
            )
        )

        comparable_comparisons = sum(
            1
            for comparison in comparisons
            if comparison.contract_comparable
        )

        non_comparable_comparisons = (
            len(comparisons)
            - comparable_comparisons
        )

        # ------------------------------------------------
        # BENCHMARK
        # ------------------------------------------------

        benchmark_results = (
            self.benchmark_engine.build(
                offers,
                comparisons,
            )
        )

        # ------------------------------------------------
        # MARKET POSITIONING
        # ------------------------------------------------

        positioning_results = (
            self.positioning_engine.build(
                offers,
                comparisons,
            )
        )

        # ------------------------------------------------
        # PROVIDER RANKING
        # ------------------------------------------------

        ranking_results = (
            self.ranking_engine.rank(
                comparisons
            )
        )

        # ------------------------------------------------
        # CONTRACT NORMALIZATION
        # ------------------------------------------------

        normalization_results = (
            self.normalization_engine.normalize_all(
                comparisons
            )
        )

        # ------------------------------------------------
        # NORMALIZATION METRICS
        # ------------------------------------------------

        normalized_comparisons = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == "NORMALIZED"
            )
        )

        estimated_normalizations = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == "NORMALIZATION_ESTIMATED"
            )
        )

        term_normalizations_required = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == "NEEDS_TERM_NORMALIZATION"
            )
        )

        mileage_normalizations_required = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == "NEEDS_MILEAGE_NORMALIZATION"
            )
        )

        term_and_mileage_normalizations_required = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == (
                    "NEEDS_TERM_AND_MILEAGE_NORMALIZATION"
                )
            )
        )

        unsupported_normalizations = sum(
            1
            for result in normalization_results
            if (
                result.normalization_status
                == "NORMALIZATION_UNSUPPORTED"
            )
        )

        # ------------------------------------------------
        # RESULT
        # ------------------------------------------------

        return MarketIntelligenceResult(

            offers_count=len(
                offers
            ),

            benchmark_count=len(
                benchmark_results
            ),

            comparison_count=len(
                comparisons
            ),

            comparable_comparisons=(
                comparable_comparisons
            ),

            non_comparable_comparisons=(
                non_comparable_comparisons
            ),

            benchmark_results=(
                benchmark_results
            ),

            positioning_results=(
                positioning_results
            ),

            ranking_results=(
                ranking_results
            ),

            normalization_results=(
                normalization_results
            ),

            normalized_comparisons=(
                normalized_comparisons
            ),

            estimated_normalizations=(
                estimated_normalizations
            ),

            term_normalizations_required=(
                term_normalizations_required
            ),

            mileage_normalizations_required=(
                mileage_normalizations_required
            ),

            term_and_mileage_normalizations_required=(
                term_and_mileage_normalizations_required
            ),

            unsupported_normalizations=(
                unsupported_normalizations
            ),
        )