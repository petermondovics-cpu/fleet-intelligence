from dataclasses import dataclass
from typing import List, Optional

from models.offer import Offer

from matching.vehicle_matcher import VehicleMatcher
from matching.contract_matcher import ContractMatcher
from matching.vehicle_variant import (
    VehicleVariantMatcher,
)


@dataclass
class ComparisonResult:

    brand: str
    model: str

    fuel_type_a: str
    fuel_type_b: str

    vehicle_confidence: int
    vehicle_match_type: str

    contract_comparable: bool
    contract_difference: str

    duration_similarity: int
    mileage_similarity: int
    contract_similarity: int

    offers: List[Offer]

    best_provider: str
    best_monthly_fee: int

    price_difference: int
    annual_saving: int

    # Price ranking
    price_winner: str
    price_winner_is_valid: bool
    price_difference_percent: float

    # ------------------------------------------------
    # VEHICLE VARIANT V1
    #
    # Defaults are intentional.
    #
    # This keeps backwards compatibility with older
    # tests and code that instantiate ComparisonResult
    # directly.
    # ------------------------------------------------

    variant_confidence: int = 0
    variant_match_type: str = (
        "NO_VARIANT_INFORMATION"
    )

    variant_key_a: Optional[str] = None
    variant_key_b: Optional[str] = None


class ComparisonEngine:

    def __init__(self):

        self.vehicle_matcher = (
            VehicleMatcher()
        )

        self.variant_matcher = (
            VehicleVariantMatcher()
        )

        self.contract_matcher = (
            ContractMatcher()
        )

    def compare(
        self,
        offers: List[Offer],
    ) -> List[ComparisonResult]:

        results = []

        providers = {}

        # ------------------------------------------------
        # GROUP OFFERS BY PROVIDER
        # ------------------------------------------------

        for offer in offers:

            provider = (
                offer.provider
                .strip()
                .lower()
            )

            if provider not in providers:

                providers[provider] = []

            providers[provider].append(
                offer
            )

        provider_names = list(
            providers.keys()
        )

        # ------------------------------------------------
        # PROVIDER PAIRS
        # ------------------------------------------------

        for i in range(
            len(provider_names)
        ):

            for j in range(
                i + 1,
                len(provider_names),
            ):

                provider_a = (
                    provider_names[i]
                )

                provider_b = (
                    provider_names[j]
                )

                # ------------------------------------------------
                # OFFER PAIRS
                # ------------------------------------------------

                for offer_a in providers[
                    provider_a
                ]:

                    for offer_b in providers[
                        provider_b
                    ]:

                        # ------------------------------------------------
                        # VEHICLE IDENTITY
                        # ------------------------------------------------

                        vehicle_match = (
                            self.vehicle_matcher.match(
                                offer_a.brand,
                                offer_a.model,
                                offer_a.fuel_type,
                                offer_b.brand,
                                offer_b.model,
                                offer_b.fuel_type,
                            )
                        )

                        # ------------------------------------------------
                        # VEHICLE MATCH
                        # ------------------------------------------------
                        #
                        # Brand/model mismatch:
                        # completely unrelated vehicle.
                        #
                        # ------------------------------------------------

                        if (
                            vehicle_match.match_type
                            == "NO_MATCH"
                        ):

                            continue

                        # ------------------------------------------------
                        # POWERTRAIN MISMATCH
                        # ------------------------------------------------
                        #
                        # Keep as potential match because this can
                        # represent a data-quality problem.
                        #
                        # Example:
                        #
                        # BYD ATTO 3
                        # Arval = PHEV
                        # Ayvens = EV
                        #
                        # ------------------------------------------------

                        powertrain_mismatch = (
                            vehicle_match.match_type
                            == (
                                "MODEL_MATCH_POWERTRAIN_MISMATCH"
                            )
                        )

                        if powertrain_mismatch:

                            print(
                                "⚠️ Vehicle: "
                                "POTENTIAL MATCH"
                            )

                            print(
                                f"Reason: "
                                f"powertrain mismatch "
                                f"({vehicle_match.confidence}%)"
                            )

                        # ------------------------------------------------
                        # VEHICLE VARIANT
                        # ------------------------------------------------

                        variant_match = (
                            self.variant_matcher.match(
                                offer_a,
                                offer_b,
                            )
                        )

                        # ------------------------------------------------
                        # VARIANT POWER MISMATCH
                        #
                        # Do NOT compare different engine/power variants.
                        #
                        # Example:
                        #
                        # OPEL COMBO 100 HP
                        # vs
                        # OPEL COMBO 130 HP
                        #
                        # These are different concrete variants.
                        # ------------------------------------------------

                        if (
                            variant_match.variant_match_type
                            == "VARIANT_POWER_MISMATCH"
                        ):

                            continue

                        # ------------------------------------------------
                        # POWERTRAIN MISMATCH
                        #
                        # VehicleMatcher already detected this.
                        #
                        # We preserve the comparison as a potential
                        # match even though the variant matcher will
                        # also identify a powertrain difference.
                        # ------------------------------------------------

                        if (
                            variant_match.variant_match_type
                            == "VARIANT_POWERTRAIN_MISMATCH"
                        ):

                            variant_confidence = 0

                            variant_match_type = (
                                "VARIANT_POWERTRAIN_MISMATCH"
                            )

                            variant_key_a = (
                                None
                            )

                            variant_key_b = (
                                None
                            )

                        else:

                            variant_confidence = (
                                variant_match.variant_confidence
                            )

                            variant_match_type = (
                                variant_match.variant_match_type
                            )

                            extracted_a = (
                                self.variant_matcher.extract(
                                    offer_a
                                )
                            )

                            extracted_b = (
                                self.variant_matcher.extract(
                                    offer_b
                                )
                            )

                            variant_key_a = (
                                extracted_a.variant_key
                            )

                            variant_key_b = (
                                extracted_b.variant_key
                            )

                        # ------------------------------------------------
                        # UNKNOWN VARIANT
                        # ------------------------------------------------
                        #
                        # If neither offer contains useful variant
                        # information, we retain the comparison but
                        # explicitly mark the uncertainty.
                        #
                        # ------------------------------------------------

                        variant_information_missing = (
                            variant_match.variant_match_type
                            == "VARIANT_PARTIAL_MATCH"
                            or
                            variant_match.variant_match_type
                            == "NO_VARIANT_INFORMATION"
                        )

                        if (
                            not powertrain_mismatch
                            and
                            variant_information_missing
                        ):

                            variant_confidence = min(
                                variant_confidence,
                                50,
                            )

                        # ------------------------------------------------
                        # CONTRACT MATCH
                        # ------------------------------------------------

                        contract_match = (
                            self.contract_matcher.match(
                                offer_a,
                                offer_b,
                            )
                        )

                        # ------------------------------------------------
                        # PRICE COMPARISON
                        # ------------------------------------------------

                        if (
                            offer_a.monthly_fee
                            <= offer_b.monthly_fee
                        ):

                            cheapest = offer_a

                        else:

                            cheapest = offer_b

                        price_difference = abs(
                            offer_a.monthly_fee
                            - offer_b.monthly_fee
                        )

                        annual_saving = (
                            price_difference
                            * 12
                        )

                        # ------------------------------------------------
                        # PRICE DIFFERENCE %
                        #
                        # Relative to the higher monthly fee.
                        # ------------------------------------------------

                        highest_price = max(
                            offer_a.monthly_fee,
                            offer_b.monthly_fee,
                        )

                        if highest_price > 0:

                            price_difference_percent = (
                                price_difference
                                / highest_price
                                * 100
                            )

                        else:

                            price_difference_percent = 0.0

                        # ------------------------------------------------
                        # VALID PRICE WINNER
                        # ------------------------------------------------
                        #
                        # Requirements:
                        #
                        # 1. Same vehicle identity
                        # 2. Same powertrain
                        # 3. Same concrete variant
                        # 4. Comparable contract
                        #
                        # ------------------------------------------------

                        exact_variant = (
                            variant_match.variant_match_type
                            == "EXACT_VARIANT"
                        )

                        if (
                            contract_match.comparable
                            and
                            vehicle_match.match_type
                            == "EXACT_MATCH"
                            and
                            exact_variant
                        ):

                            price_winner = (
                                cheapest.provider
                            )

                            price_winner_is_valid = (
                                True
                            )

                        else:

                            price_winner = (
                                "NOT_COMPARABLE"
                            )

                            price_winner_is_valid = (
                                False
                            )

                        # ------------------------------------------------
                        # BEST PROVIDER
                        #
                        # Backwards-compatible nominal result.
                        #
                        # This is NOT necessarily a valid price winner.
                        # ------------------------------------------------

                        best_provider = (
                            cheapest.provider
                        )

                        best_monthly_fee = (
                            cheapest.monthly_fee
                        )

                        # ------------------------------------------------
                        # RESULT
                        # ------------------------------------------------

                        results.append(
                            ComparisonResult(

                                brand=(
                                    cheapest.brand
                                ),

                                model=(
                                    cheapest.model
                                ),

                                fuel_type_a=(
                                    offer_a.fuel_type
                                ),

                                fuel_type_b=(
                                    offer_b.fuel_type
                                ),

                                vehicle_confidence=(
                                    vehicle_match.confidence
                                ),

                                vehicle_match_type=(
                                    vehicle_match.match_type
                                ),

                                contract_comparable=(
                                    contract_match.comparable
                                ),

                                contract_difference=(
                                    contract_match.difference
                                ),

                                duration_similarity=(
                                    contract_match
                                    .duration_similarity
                                ),

                                mileage_similarity=(
                                    contract_match
                                    .mileage_similarity
                                ),

                                contract_similarity=(
                                    contract_match
                                    .contract_similarity
                                ),

                                offers=[
                                    offer_a,
                                    offer_b,
                                ],

                                best_provider=(
                                    best_provider
                                ),

                                best_monthly_fee=(
                                    best_monthly_fee
                                ),

                                price_difference=(
                                    price_difference
                                ),

                                annual_saving=(
                                    annual_saving
                                ),

                                price_winner=(
                                    price_winner
                                ),

                                price_winner_is_valid=(
                                    price_winner_is_valid
                                ),

                                price_difference_percent=(
                                    round(
                                        price_difference_percent,
                                        2,
                                    )
                                ),

                                # ------------------------------------------------
                                # VARIANT
                                # ------------------------------------------------

                                variant_confidence=(
                                    variant_confidence
                                ),

                                variant_match_type=(
                                    variant_match_type
                                ),

                                variant_key_a=(
                                    variant_key_a
                                ),

                                variant_key_b=(
                                    variant_key_b
                                ),
                            )
                        )

        return results