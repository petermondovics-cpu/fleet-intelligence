from dataclasses import dataclass
from typing import Optional

from comparison.engine import (
    ComparisonEngine,
    ComparisonResult,
)
from contract_normalization.engine import (
    ContractNormalizationEngine,
    ContractNormalizationResult,
)
from models.comparable_offer import (
    COMPARABLE,
    NORMALIZATION_REQUIRED,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
    ComparableOfferEngine,
    ComparableOfferResult,
)
from models.composite_offer import CompositeOffer


PRICE_COMPARABLE = "PRICE_COMPARABLE"
PRICE_NORMALIZED = "PRICE_NORMALIZED"
PRICE_UNAVAILABLE = "PRICE_UNAVAILABLE"


@dataclass(frozen=True)
class CompositeComparisonResult:
    """
    Integrates CompositeOffer comparability with the existing
    ComparisonEngine and ContractNormalizationEngine.

    Safety rule:
    no price winner is produced unless the new comparability
    barrier allows it.
    """

    status: str

    comparability: ComparableOfferResult

    legacy_comparison: Optional[
        ComparisonResult
    ] = None

    normalization: Optional[
        ContractNormalizationResult
    ] = None

    price_winner: Optional[str] = None

    comparable_monthly_fee_a: Optional[int] = None
    comparable_monthly_fee_b: Optional[int] = None

    reason: str = ""


class CompositeComparisonEngine:

    def __init__(self):

        self.comparability_engine = (
            ComparableOfferEngine()
        )

        self.comparison_engine = (
            ComparisonEngine()
        )

        self.normalization_engine = (
            ContractNormalizationEngine()
        )

    def compare(
        self,
        offer_a: CompositeOffer,
        offer_b: CompositeOffer,
    ) -> CompositeComparisonResult:

        # ----------------------------------------------------
        # NEW COMPARABILITY BARRIER
        # ----------------------------------------------------

        comparability = (
            self.comparability_engine.compare(
                offer_a,
                offer_b,
            )
        )

        if comparability.status in {
            NOT_COMPARABLE,
            INSUFFICIENT_EVIDENCE,
        }:

            return CompositeComparisonResult(
                status=PRICE_UNAVAILABLE,
                comparability=comparability,
                reason=(
                    "Price comparison blocked by "
                    "Composite Offer comparability barrier."
                ),
            )

        # ----------------------------------------------------
        # LEGACY COMPARISON
        # ----------------------------------------------------

        legacy_comparison = (
            self._build_legacy_comparison(
                offer_a,
                offer_b,
            )
        )

        # ----------------------------------------------------
        # DIRECT COMPARISON
        # ----------------------------------------------------

        if comparability.status == COMPARABLE:

            fee_a = offer_a.monthly_fee
            fee_b = offer_b.monthly_fee

            return CompositeComparisonResult(
                status=PRICE_COMPARABLE,
                comparability=comparability,
                legacy_comparison=legacy_comparison,
                price_winner=self._winner(
                    offer_a.provider,
                    fee_a,
                    offer_b.provider,
                    fee_b,
                ),
                comparable_monthly_fee_a=fee_a,
                comparable_monthly_fee_b=fee_b,
                reason=(
                    "Composite offers are directly "
                    "comparable."
                ),
            )

        # ----------------------------------------------------
        # NORMALIZATION REQUIRED
        # ----------------------------------------------------

        if (
            comparability.status
            == NORMALIZATION_REQUIRED
        ):

            normalization = (
                self.normalization_engine.normalize(
                    legacy_comparison
                )
            )

            if (
                not normalization
                .normalized_price_available
            ):

                return CompositeComparisonResult(
                    status=PRICE_UNAVAILABLE,
                    comparability=comparability,
                    legacy_comparison=(
                        legacy_comparison
                    ),
                    normalization=normalization,
                    reason=(
                        "Contract normalization is "
                        "required but no normalized "
                        "price is available."
                    ),
                )

            fee_a = (
                normalization
                .normalized_monthly_fee_a
            )

            fee_b = (
                normalization
                .normalized_monthly_fee_b
            )

            return CompositeComparisonResult(
                status=PRICE_NORMALIZED,
                comparability=comparability,
                legacy_comparison=legacy_comparison,
                normalization=normalization,
                price_winner=self._winner(
                    offer_a.provider,
                    fee_a,
                    offer_b.provider,
                    fee_b,
                ),
                comparable_monthly_fee_a=fee_a,
                comparable_monthly_fee_b=fee_b,
                reason=(
                    "Price comparison uses "
                    "Contract Normalization V4."
                ),
            )

        raise ValueError(
            "Unsupported comparability status: "
            f"{comparability.status}"
        )

    def _build_legacy_comparison(
        self,
        offer_a: CompositeOffer,
        offer_b: CompositeOffer,
    ) -> ComparisonResult:

        comparisons = (
            self.comparison_engine.compare(
                [
                    offer_a.offer,
                    offer_b.offer,
                ]
            )
        )

        if len(comparisons) != 1:

            raise ValueError(
                "Legacy ComparisonEngine did not "
                "produce exactly one comparison."
            )

        return comparisons[0]

    @staticmethod
    def _winner(
        provider_a: str,
        fee_a: int,
        provider_b: str,
        fee_b: int,
    ) -> str:

        if fee_a < fee_b:
            return provider_a

        if fee_b < fee_a:
            return provider_b

        return "TIE"
