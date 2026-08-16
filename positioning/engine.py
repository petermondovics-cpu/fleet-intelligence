from dataclasses import dataclass
from typing import Dict, List

from comparison.engine import ComparisonResult
from models.offer import Offer

from matching.vehicle_variant import (
    VehicleVariantMatcher,
)


@dataclass
class MarketPositionResult:

    brand: str
    model: str

    # ------------------------------------------------
    # VEHICLE VARIANT
    # ------------------------------------------------

    variant_key: str
    variant_confidence: int
    variant_match_type: str

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

    # ------------------------------------------------
    # MARKET POSITIONING
    # ------------------------------------------------

    position_type: str

    nominal_price_position: str

    price_winner: str
    price_winner_is_valid: bool

    data_quality_warning: bool
    data_quality_reason: str


class MarketPositioningEngine:

    def __init__(self):

        self.variant_matcher = (
            VehicleVariantMatcher()
        )

    # ------------------------------------------------
    # BUILD
    # ------------------------------------------------

    def build(
        self,
        offers: List[Offer],
        comparisons: List[ComparisonResult],
    ) -> List[MarketPositionResult]:

        groups: Dict[
            str,
            List[Offer],
        ] = {}

        # ------------------------------------------------
        # BUILD VARIANT-AWARE GROUPS
        # ------------------------------------------------

        for offer in offers:

            vehicle_key = (
                self._vehicle_key(
                    offer
                )
            )

            variant = (
                self.variant_matcher.extract(
                    offer
                )
            )

            variant_key = (
                variant.variant_key
            )

            if not variant_key:

                variant_key = "UNKNOWN"

            key = (
                f"{vehicle_key}|"
                f"{variant_key}"
            )

            if key not in groups:

                groups[key] = []

            groups[key].append(
                offer
            )

        results = []

        # ------------------------------------------------
        # NORMAL VARIANT GROUPS
        # ------------------------------------------------

        for group in groups.values():

            providers = sorted(
                {
                    offer.provider
                    for offer in group
                }
            )

            # A single-provider variant is not
            # market positioning.
            if len(providers) < 2:

                continue

            result = (
                self._build_position(
                    group,
                    comparisons,
                )
            )

            if result is not None:

                results.append(
                    result
                )

        # ------------------------------------------------
        # POTENTIAL MATCHES
        #
        # Example:
        #
        # ATTO 3 PHEV
        # vs
        # ATTO 3 EV
        #
        # They are separate variant groups, but the
        # comparison engine explicitly identifies them
        # as a potential match.
        # ------------------------------------------------

        potential_pairs = set()

        for comparison in comparisons:

            if (
                comparison.vehicle_match_type
                != "MODEL_MATCH_POWERTRAIN_MISMATCH"
            ):

                continue

            if len(comparison.offers) < 2:

                continue

            pair_ids = tuple(
                sorted(
                    id(offer)
                    for offer in comparison.offers
                )
            )

            if pair_ids in potential_pairs:

                continue

            potential_pairs.add(
                pair_ids
            )

            result = (
                self._build_position(
                    comparison.offers,
                    comparisons,
                    force_potential=True,
                )
            )

            if result is not None:

                results.append(
                    result
                )

        # ------------------------------------------------
        # SORT
        # ------------------------------------------------

        return sorted(
            results,
            key=lambda result: (
                result.brand,
                result.model,
                result.variant_key,
            ),
        )

    # ------------------------------------------------
    # BUILD POSITION
    # ------------------------------------------------

    def _build_position(
        self,
        group: List[Offer],
        comparisons: List[ComparisonResult],
        force_potential: bool = False,
    ) -> MarketPositionResult | None:

        if not group:

            return None

        providers = sorted(
            {
                offer.provider
                for offer in group
            }
        )

        if (
            len(providers) < 2
            and not force_potential
        ):

            return None

        # ------------------------------------------------
        # SORT OFFERS
        # ------------------------------------------------

        sorted_offers = sorted(
            group,
            key=lambda offer: offer.monthly_fee,
        )

        cheapest = sorted_offers[0]

        most_expensive = (
            sorted_offers[-1]
        )

        # ------------------------------------------------
        # VARIANT INFORMATION
        # ------------------------------------------------

        extracted_variants = [
            self.variant_matcher.extract(
                offer
            )
            for offer in group
        ]

        variant_keys = {
            variant.variant_key
            for variant in extracted_variants
            if variant.variant_key
        }

        if len(variant_keys) == 1:

            variant_key = next(
                iter(variant_keys)
            )

        elif len(variant_keys) == 0:

            variant_key = "UNKNOWN"

        else:

            variant_key = (
                "MULTIPLE_VARIANTS"
            )

        variant_confidence = min(
            (
                variant.variant_confidence
                for variant
                in extracted_variants
            ),
            default=0,
        )

        variant_match_types = {
            variant.variant_match_type
            for variant
            in extracted_variants
        }

        if len(variant_match_types) == 1:

            variant_match_type = next(
                iter(variant_match_types)
            )

        else:

            variant_match_type = (
                "MULTIPLE_VARIANTS"
            )

        # ------------------------------------------------
        # COMPARISON INFORMATION
        # ------------------------------------------------

        matching_comparisons = [
            comparison
            for comparison in comparisons
            if self._comparison_matches_group(
                comparison,
                group,
            )
        ]

        matching_comparisons = sorted(
            matching_comparisons,
            key=lambda comparison: (
                comparison.vehicle_match_type
                != "EXACT_MATCH",

                comparison.variant_match_type
                != "EXACT_VARIANT",

                not comparison.contract_comparable,
            ),
        )

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

            comparison_variant_confidence = (
                comparison.variant_confidence
            )

            comparison_variant_match_type = (
                comparison.variant_match_type
            )

        else:

            comparison = None

            vehicle_confidence = 0

            vehicle_match_type = (
                "NO_VALID_COMPARISON"
            )

            contract_comparable = False

            contract_difference = ""

            comparison_variant_confidence = (
                variant_confidence
            )

            comparison_variant_match_type = (
                variant_match_type
            )

        # ------------------------------------------------
        # POSITION TYPE
        # ------------------------------------------------

        if (
            force_potential
            or
            vehicle_match_type
            == "MODEL_MATCH_POWERTRAIN_MISMATCH"
        ):

            position_type = (
                "POTENTIAL_MATCH"
            )

        elif (
            contract_comparable
            and
            comparison_variant_match_type
            == "EXACT_VARIANT"
        ):

            position_type = (
                "DIRECT_COMPARISON"
            )

        else:

            position_type = (
                "NEAR_COMPARISON"
            )

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

        elif (
            comparison_variant_match_type
            == "VARIANT_POWER_MISMATCH"
        ):

            data_quality_warning = True

            data_quality_reason = (
                "Vehicle variant power "
                "mismatch between offers."
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
        # VALID PRICE WINNER
        # ------------------------------------------------

        valid_price_comparison = (
            vehicle_match_type
            == "EXACT_MATCH"
            and
            comparison_variant_match_type
            == "EXACT_VARIANT"
            and
            contract_comparable
        )

        if valid_price_comparison:

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

        # ------------------------------------------------
        # RESULT
        # ------------------------------------------------

        return MarketPositionResult(

            brand=(
                cheapest.brand
            ),

            model=(
                cheapest.model
            ),

            variant_key=(
                variant_key
            ),

            variant_confidence=(
                comparison_variant_confidence
            ),

            variant_match_type=(
                comparison_variant_match_type
            ),

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
            for offer
            in comparison.offers
        }

        group_ids = {
            id(offer)
            for offer
            in offers
        }

        return (
            comparison_ids.issubset(
                group_ids
            )
        )