from dataclasses import dataclass
from typing import List, Optional

from comparison.engine import ComparisonResult
from models.offer import Offer


@dataclass
class NormalizationResult:

    brand: str
    model: str

    provider_a: str
    provider_b: str

    contract_comparable: bool

    position_type: str

    nominal_fee_a: int
    nominal_fee_b: int

    normalized_fee_a: Optional[int]
    normalized_fee_b: Optional[int]

    normalized_price_difference: Optional[int]
    normalized_price_difference_percent: Optional[float]

    normalized_price_winner: str
    normalized_price_winner_is_valid: bool

    normalization_status: str
    normalization_method: str


class NormalizationEngine:

    def normalize(
        self,
        comparison: ComparisonResult,
    ) -> NormalizationResult:

        offer_a = comparison.offers[0]
        offer_b = comparison.offers[1]

        # ------------------------------------------------
        # DIRECT COMPARISON
        #
        # Azonos szerződés esetén a nominális havi díj
        # egyben a normalizált havi díj.
        # ------------------------------------------------

        if comparison.contract_comparable:

            normalized_fee_a = (
                offer_a.monthly_fee
            )

            normalized_fee_b = (
                offer_b.monthly_fee
            )

            difference = abs(
                normalized_fee_a
                - normalized_fee_b
            )

            highest_fee = max(
                normalized_fee_a,
                normalized_fee_b,
            )

            if highest_fee > 0:

                difference_percent = round(
                    difference
                    / highest_fee
                    * 100,
                    2,
                )

            else:

                difference_percent = 0.0

            if (
                normalized_fee_a
                < normalized_fee_b
            ):

                winner = offer_a.provider

            elif (
                normalized_fee_b
                < normalized_fee_a
            ):

                winner = offer_b.provider

            else:

                winner = "TIE"

            return NormalizationResult(

                brand=comparison.brand,

                model=comparison.model,

                provider_a=offer_a.provider,

                provider_b=offer_b.provider,

                contract_comparable=True,

                position_type="DIRECT_COMPARISON",

                nominal_fee_a=(
                    offer_a.monthly_fee
                ),

                nominal_fee_b=(
                    offer_b.monthly_fee
                ),

                normalized_fee_a=(
                    normalized_fee_a
                ),

                normalized_fee_b=(
                    normalized_fee_b
                ),

                normalized_price_difference=(
                    difference
                ),

                normalized_price_difference_percent=(
                    difference_percent
                ),

                normalized_price_winner=(
                    winner
                ),

                normalized_price_winner_is_valid=(
                    True
                ),

                normalization_status=(
                    "NORMALIZED"
                ),

                normalization_method=(
                    "NOMINAL_PRICE"
                ),
            )

        # ------------------------------------------------
        # NON-COMPARABLE
        #
        # Egyelőre nincs becsült normalizáció.
        # ------------------------------------------------

        if (
            comparison.vehicle_match_type
            == "MODEL_MATCH_POWERTRAIN_MISMATCH"
        ):

            position_type = (
                "POTENTIAL_MATCH"
            )

        else:

            position_type = (
                "NEAR_COMPARISON"
            )

        return NormalizationResult(

            brand=comparison.brand,

            model=comparison.model,

            provider_a=offer_a.provider,

            provider_b=offer_b.provider,

            contract_comparable=False,

            position_type=position_type,

            nominal_fee_a=(
                offer_a.monthly_fee
            ),

            nominal_fee_b=(
                offer_b.monthly_fee
            ),

            normalized_fee_a=None,

            normalized_fee_b=None,

            normalized_price_difference=None,

            normalized_price_difference_percent=None,

            normalized_price_winner=(
                "NOT_COMPARABLE"
            ),

            normalized_price_winner_is_valid=(
                False
            ),

            normalization_status=(
                "NOT_NORMALIZABLE"
            ),

            normalization_method=(
                "NONE"
            ),
        )

    def normalize_all(
        self,
        comparisons: List[ComparisonResult],
    ) -> List[NormalizationResult]:

        return [
            self.normalize(
                comparison
            )
            for comparison in comparisons
        ]