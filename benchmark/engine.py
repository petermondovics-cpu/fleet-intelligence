from dataclasses import dataclass
from typing import Dict, List

from models.offer import Offer
from comparison.engine import ComparisonResult


@dataclass
class BenchmarkResult:

    brand: str
    model: str

    providers: List[str]
    offers: List[Offer]

    fuel_types: List[str]

    lowest_monthly_fee: int
    lowest_provider: str

    lowest_duration: int
    lowest_mileage: int

    comparison_available: bool
    valid_price_winner: str

    vehicle_confidence: int
    vehicle_match_type: str

    contract_comparable: bool
    contract_difference: str

    data_quality_warning: bool


class BenchmarkEngine:

    def build(
        self,
        offers: List[Offer],
        comparisons: List[ComparisonResult],
    ) -> List[BenchmarkResult]:

        groups: Dict[str, List[Offer]] = {}

        for offer in offers:

            key = self._vehicle_key(
                offer
            )

            if key not in groups:
                groups[key] = []

            groups[key].append(
                offer
            )

        results = []

        for key, group in groups.items():

            sorted_offers = sorted(
                group,
                key=lambda offer: offer.monthly_fee,
            )

            cheapest = sorted_offers[0]

            providers = sorted(
                {
                    offer.provider
                    for offer in group
                }
            )

            fuel_types = sorted(
                {
                    offer.fuel_type
                    for offer in group
                }
            )

            matching_comparisons = [
                comparison
                for comparison in comparisons
                if self._comparison_matches_group(
                    comparison,
                    group,
                )
            ]

            comparison_available = (
                len(matching_comparisons) > 0
            )

            # ------------------------------------------------
            # SINGLE PROVIDER
            #
            # Nincs összehasonlítási alap.
            # Ez nem ugyanaz, mint egy nem összehasonlítható
            # több-szolgáltatós ajánlat.
            # ------------------------------------------------

            if len(providers) == 1:

                valid_price_winner = (
                    "SINGLE_PROVIDER"
                )

                vehicle_confidence = 100

                vehicle_match_type = (
                    "SINGLE_PROVIDER"
                )

                contract_comparable = False

                contract_difference = ""

            # ------------------------------------------------
            # MULTI PROVIDER
            # ------------------------------------------------

            elif matching_comparisons:

                valid_winners = [
                    comparison
                    for comparison in matching_comparisons
                    if comparison.price_winner_is_valid
                ]

                if valid_winners:

                    winner = valid_winners[0]

                    valid_price_winner = (
                        winner.price_winner
                    )

                    vehicle_confidence = (
                        winner.vehicle_confidence
                    )

                    vehicle_match_type = (
                        winner.vehicle_match_type
                    )

                    contract_comparable = (
                        winner.contract_comparable
                    )

                    contract_difference = (
                        winner.contract_difference
                    )

                else:

                    comparison = (
                        matching_comparisons[0]
                    )

                    valid_price_winner = (
                        "NOT_COMPARABLE"
                    )

                    vehicle_confidence = (
                        comparison.vehicle_confidence
                    )

                    vehicle_match_type = (
                        comparison.vehicle_match_type
                    )

                    contract_comparable = (
                        comparison.contract_comparable
                    )

                    contract_difference = (
                        comparison.contract_difference
                    )

            # ------------------------------------------------
            # MULTI PROVIDER WITHOUT MATCH
            # ------------------------------------------------

            else:

                valid_price_winner = (
                    "NOT_COMPARABLE"
                )

                vehicle_confidence = 0

                vehicle_match_type = (
                    "NO_VALID_COMPARISON"
                )

                contract_comparable = False

                contract_difference = ""

            # ------------------------------------------------
            # DATA QUALITY
            # ------------------------------------------------

            data_quality_warning = any(
                self._has_quality_warning(
                    offer
                )
                for offer in group
            )

            results.append(
                BenchmarkResult(

                    brand=(
                        cheapest.brand
                    ),

                    model=(
                        cheapest.model
                    ),

                    providers=providers,

                    offers=sorted_offers,

                    fuel_types=fuel_types,

                    lowest_monthly_fee=(
                        cheapest.monthly_fee
                    ),

                    lowest_provider=(
                        cheapest.provider
                    ),

                    lowest_duration=(
                        cheapest.duration
                    ),

                    lowest_mileage=(
                        cheapest.mileage
                    ),

                    comparison_available=(
                        comparison_available
                    ),

                    valid_price_winner=(
                        valid_price_winner
                    ),

                    vehicle_confidence=(
                        vehicle_confidence
                    ),

                    vehicle_match_type=(
                        vehicle_match_type
                    ),

                    contract_comparable=(
                        contract_comparable
                    ),

                    contract_difference=(
                        contract_difference
                    ),

                    data_quality_warning=(
                        data_quality_warning
                    ),
                )
            )

        return sorted(
            results,
            key=lambda result: (
                result.brand,
                result.model,
            ),
        )

    # ------------------------------------------------
    # VEHICLE IDENTITY
    # ------------------------------------------------

    def _vehicle_key(
        self,
        offer: Offer,
    ) -> str:

        brand = (
            offer.brand
            .strip()
            .upper()
        )

        model = (
            offer.model
            .strip()
            .upper()
        )

        model_aliases = {
            "COMBO CARGO": "COMBO",
            "SCROSS": "S-CROSS",
        }

        model = model_aliases.get(
            model,
            model,
        )

        return (
            f"{brand}|{model}"
        )

    # ------------------------------------------------
    # COMPARISON → BENCHMARK
    # ------------------------------------------------

    def _comparison_matches_group(
        self,
        comparison: ComparisonResult,
        offers: List[Offer],
    ) -> bool:

        comparison_ids = {
            id(offer)
            for offer in comparison.offers
        }

        group_ids = {
            id(offer)
            for offer in offers
        }

        return comparison_ids.issubset(
            group_ids
        )

    # ------------------------------------------------
    # DATA QUALITY
    # ------------------------------------------------

    def _has_quality_warning(
        self,
        offer: Offer,
    ) -> bool:

        return (
            getattr(
                offer,
                "quality_confidence",
                100,
            )
            < 100
        )