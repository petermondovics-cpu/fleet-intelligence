from dataclasses import dataclass
from typing import List

from models.offer import Offer
from matching.vehicle_matcher import VehicleMatcher
from matching.contract_matcher import ContractMatcher


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


class ComparisonEngine:

    def __init__(self):

        self.vehicle_matcher = (
            VehicleMatcher()
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

                for offer_a in providers[
                    provider_a
                ]:

                    for offer_b in providers[
                        provider_b
                    ]:

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
                        # Csak akkor dobjuk el az ajánlatot,
                        # ha a márka vagy a modell sem egyezik.
                        #
                        # Az eltérő hajtásláncot nem dobjuk el,
                        # mert ez lehet potential match / adatminőségi
                        # probléma.
                        # ------------------------------------------------

                        if (
                            vehicle_match.match_type
                            == "NO_MATCH"
                        ):
                            continue

                        if (
                            vehicle_match.match_type
                            == "MODEL_MATCH_POWERTRAIN_MISMATCH"
                        ):

                            print(
                                "⚠️ Vehicle: "
                                "POTENTIAL MATCH"
                            )

                            print(
                                f"Reason: "
                                f"powertrain mismatch "
                                f"({vehicle_match.confidence}%)"
                            )

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
                            price_difference * 12
                        )

                        # ------------------------------------------------
                        # PRICE DIFFERENCE %
                        #
                        # A drágább ajánlathoz viszonyítunk.
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
                        # PRICE WINNER
                        #
                        # Csak összehasonlítható szerződés esetén
                        # nevezünk meg valódi árgyőztest.
                        # ------------------------------------------------

                        if (
                            contract_match.comparable
                            and vehicle_match.match_type
                            == "EXACT_MATCH"
                        ):

                            price_winner = (
                                cheapest.provider
                            )

                            price_winner_is_valid = True

                        else:

                            price_winner = (
                                "NOT_COMPARABLE"
                            )

                            price_winner_is_valid = False

                        # ------------------------------------------------
                        # BEST PROVIDER
                        #
                        # A meglévő kompatibilitás miatt megtartjuk:
                        # ez egyszerűen a kisebb havi díjú ajánlat.
                        #
                        # Ez NEM ugyanaz, mint a valid price winner.
                        # ------------------------------------------------

                        best_provider = (
                            cheapest.provider
                        )

                        best_monthly_fee = (
                            cheapest.monthly_fee
                        )

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
                            )
                        )

        return results