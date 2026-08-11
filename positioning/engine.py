from dataclasses import dataclass
from typing import Dict, List

from comparison.engine import ComparisonResult
from models.offer import Offer


@dataclass
class MarketPositionResult:

    brand: str
    model: str

    offers: List[Offer]
    providers: List[str]

    vehicle_confidence: int
    vehicle_match_type: str

    contract_comparable: bool
    contract_difference: str

    lowest_monthly_fee: int
    lowest_provider: str

    highest_monthly_fee: int
    highest_provider: str

    price_difference: int
    price_difference_percent: float

    # Market positioning
    position_type: str

    nominal_price_position: str

    price_winner: str
    price_winner_is_valid: bool

    data_quality_warning: bool
    data_quality_reason: str


class MarketPositioningEngine:

    def build(
        self,
        offers: List[Offer],
        comparisons: List[ComparisonResult],
    ) -> List[MarketPositionResult]:

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

        for group in groups.values():

            providers = sorted(
                {
                    offer.provider
                    for offer in group
                }
            )

            # ------------------------------------------------
            # SINGLE PROVIDER
            #
            # Nem piaci positioning.
            # ------------------------------------------------

            if len(providers) < 2:
                continue

            sorted_offers = sorted(
                group,
                key=lambda offer: offer.monthly_fee,
            )

            cheapest = sorted_offers[0]
            most_expensive = sorted_offers[-1]

            matching_comparisons = [
                comparison
                for comparison in comparisons
                if self._comparison_matches_group(
                    comparison,
                    group,
                )
            ]

            # ------------------------------------------------
            # COMPARISON INFORMATION
            # ------------------------------------------------

            if matching_comparisons:

                comparison = (
                    matching_comparisons[0]
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

            else:

                vehicle_confidence = 0

                vehicle_match_type = (
                    "NO_VALID_COMPARISON"
                )

                contract_comparable = False

                contract_difference = ""

            # ------------------------------------------------
            # DATA QUALITY
            # ------------------------------------------------

            data_quality_warning = False
            data_quality_reason = ""

            if (
                vehicle_match_type
                == "MODEL_MATCH_POWERTRAIN_MISMATCH"
            ):

                data_quality_warning = True

                data_quality_reason = (
                    "Powertrain classification "
                    "mismatch between offers."
                )

            # ------------------------------------------------
            # POSITION TYPE
            # ------------------------------------------------

            if (
                vehicle_match_type
                == "MODEL_MATCH_POWERTRAIN_MISMATCH"
            ):

                position_type = (
                    "POTENTIAL_MATCH"
                )

            elif contract_comparable:

                position_type = (
                    "DIRECT_COMPARISON"
                )

            else:

                position_type = (
                    "NEAR_COMPARISON"
                )

            # ------------------------------------------------
            # NOMINAL PRICE
            # ------------------------------------------------

            price_difference = (
                most_expensive.monthly_fee
                - cheapest.monthly_fee
            )

            highest_price = (
                most_expensive.monthly_fee
            )

            if highest_price > 0:

                price_difference_percent = round(
                    (
                        price_difference
                        / highest_price
                        * 100
                    ),
                    2,
                )

            else:

                price_difference_percent = 0.0

            # ------------------------------------------------
            # PRICE WINNER
            #
            # Only valid for DIRECT_COMPARISON.
            # ------------------------------------------------

            if contract_comparable:

                price_winner = (
                    cheapest.provider
                )

                price_winner_is_valid = True

                nominal_price_position = (
                    f"{cheapest.provider}"
                    " - LOWER_PRICE"
                )

            else:

                price_winner = (
                    "NOT_COMPARABLE"
                )

                price_winner_is_valid = False

                nominal_price_position = (
                    f"{cheapest.provider}"
                    " - LOWER_NOMINAL_PRICE"
                )

            results.append(
                MarketPositionResult(

                    brand=cheapest.brand,

                    model=cheapest.model,

                    offers=sorted_offers,

                    providers=providers,

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

                    lowest_monthly_fee=(
                        cheapest.monthly_fee
                    ),

                    lowest_provider=(
                        cheapest.provider
                    ),

                    highest_monthly_fee=(
                        most_expensive.monthly_fee
                    ),

                    highest_provider=(
                        most_expensive.provider
                    ),

                    price_difference=(
                        price_difference
                    ),

                    price_difference_percent=(
                        price_difference_percent
                    ),

                    position_type=(
                        position_type
                    ),

                    nominal_price_position=(
                        nominal_price_position
                    ),

                    price_winner=(
                        price_winner
                    ),

                    price_winner_is_valid=(
                        price_winner_is_valid
                    ),

                    data_quality_warning=(
                        data_quality_warning
                    ),

                    data_quality_reason=(
                        data_quality_reason
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
    # COMPARISON → POSITIONING
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