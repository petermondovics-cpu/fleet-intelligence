from dataclasses import dataclass
from typing import List, Optional

from comparison.engine import ComparisonResult
from contract_evidence.engine import ContractEvidenceEngine
from contract_normalization.engine import (
    ContractNormalizationEngine,
    ContractNormalizationResult,
)
from comparison.normalized_vehicle_identity import (
    NormalizedVehicleComparabilityEngine,
)


@dataclass(frozen=True)
class ContractNormalizationBridgeResult:
    """
    Contract-normalization output attached to the richer comparison stack.

    final_price_comparison_ready is deliberately stricter than
    ContractNormalizationResult.normalized_price_available:
    contract normalization alone never proves service/equipment/financial
    comparability.
    """

    normalization: ContractNormalizationResult
    evidence: dict
    final_price_comparison_ready: bool


class ContractNormalizationBridge:
    """
    Bridge V1 from EvidenceAwareCompositeOffer to the existing
    ContractEvidenceEngine + ContractNormalizationEngine V4.

    Safety rules:
    - only observed Offer objects supplied in observed_offer_pool are evidence;
    - quote-request slider metadata is never accepted as Offer evidence;
    - no synthetic correction factor is invented;
    - normalized prices may be calculated diagnostically even when another
      comparison barrier still blocks final price ranking;
    - this class itself never declares a price winner.
    """

    def __init__(self):
        self.evidence_engine = ContractEvidenceEngine()
        self.normalization_engine = ContractNormalizationEngine()
        self.identity_engine = NormalizedVehicleComparabilityEngine()

    def normalize(
        self,
        left,
        right,
        observed_offer_pool: Optional[List] = None,
        other_barriers_passed: bool = False,
    ) -> ContractNormalizationBridgeResult:

        comparison = self._comparison_result(
            left,
            right,
        )

        pool = list(
            observed_offer_pool or []
        )

        # Ensure the two compared observed offers are available to the
        # evidence engine without duplicating object references.
        for offer in (
            left.composite.offer,
            right.composite.offer,
        ):
            if not any(
                existing is offer
                for existing in pool
            ):
                pool.append(offer)

        evidence = (
            self.evidence_engine
            .find_for_comparison(
                comparison,
                pool,
            )
        )

        # ContractEvidenceEngine stores an observed pair in the order
        # in which the offers appeared in the evidence pool. The V4
        # normalization engine, however, requires evidence.source_*
        # to describe the actual comparison offer being normalized.
        #
        # Therefore orient each evidence record toward the matching
        # comparison offer. This changes direction only; it does not
        # invent any price relationship.
        evidence = self._orient_evidence(
            comparison,
            evidence,
        )

        normalization = (
            self.normalization_engine
            .normalize_with_evidence(
                comparison,
                evidence,
            )
        )

        final_ready = (
            other_barriers_passed
            and normalization.normalized_price_available
        )

        return ContractNormalizationBridgeResult(
            normalization=normalization,
            evidence=evidence,
            final_price_comparison_ready=final_ready,
        )

    def _orient_evidence(
        self,
        comparison: ComparisonResult,
        evidence: dict,
    ) -> dict:
        """
        Orient TERM/MILEAGE evidence so source_* is the observed
        comparison contract to be normalized and target_* is the
        other observed contract used as the target.

        Example:
            evidence engine discovers Arval 48 -> 60
            comparison contains Arval 60 vs Ayvens 48

        The normalization engine needs:
            Arval 60 -> 48

        Reversing the observed pair is mathematically valid because
        both endpoint prices were observed. No interpolation or
        synthetic factor is introduced.
        """

        result = dict(evidence or {})

        for key in (
            "term_evidence",
            "mileage_evidence",
        ):
            item = result.get(key)

            if not item:
                continue

            provider = item.get("provider")

            comparison_offer = next(
                (
                    offer
                    for offer in comparison.offers
                    if offer.provider == provider
                ),
                None,
            )

            if comparison_offer is None:
                result[key] = None
                continue

            if key == "term_evidence":
                source_matches = (
                    comparison_offer.duration
                    == item.get("source_duration")
                    and comparison_offer.mileage
                    == item.get("source_mileage")
                )

                target_matches = (
                    comparison_offer.duration
                    == item.get("target_duration")
                    and comparison_offer.mileage
                    == item.get("target_mileage")
                )

            else:
                source_matches = (
                    comparison_offer.mileage
                    == item.get("source_mileage")
                    and comparison_offer.duration
                    == item.get("source_duration")
                )

                target_matches = (
                    comparison_offer.mileage
                    == item.get("target_mileage")
                    and comparison_offer.duration
                    == item.get("target_duration")
                )

            if source_matches:
                continue

            if not target_matches:
                # Evidence does not describe the comparison offer
                # in either direction. Reject it rather than guessing.
                result[key] = None
                continue

            reversed_item = dict(item)

            reversed_item["source_duration"] = item.get(
                "target_duration"
            )
            reversed_item["target_duration"] = item.get(
                "source_duration"
            )
            reversed_item["source_mileage"] = item.get(
                "target_mileage"
            )
            reversed_item["target_mileage"] = item.get(
                "source_mileage"
            )
            reversed_item["source_monthly_fee"] = item.get(
                "target_monthly_fee"
            )
            reversed_item["target_monthly_fee"] = item.get(
                "source_monthly_fee"
            )

            source_fee = reversed_item.get(
                "source_monthly_fee"
            )
            target_fee = reversed_item.get(
                "target_monthly_fee"
            )

            if (
                source_fee is None
                or target_fee is None
                or source_fee <= 0
                or target_fee <= 0
            ):
                result[key] = None
                continue

            reversed_item["factor"] = round(
                target_fee / source_fee,
                6,
            )

            result[key] = reversed_item

        return result

    def _comparison_result(
        self,
        left,
        right,
    ) -> ComparisonResult:

        left_offer = left.composite.offer
        right_offer = right.composite.offer

        pair = (
            self.identity_engine
            .normalize_pair(
                left,
                right,
            )
        )

        contract_comparable = (
            left_offer.duration
            == right_offer.duration
            and left_offer.mileage
            == right_offer.mileage
        )

        duration_difference = abs(
            left_offer.duration
            - right_offer.duration
        )

        mileage_difference = abs(
            left_offer.mileage
            - right_offer.mileage
        )

        duration_similarity = (
            self._duration_similarity(
                duration_difference
            )
        )

        mileage_similarity = (
            self._mileage_similarity(
                mileage_difference
            )
        )

        contract_similarity = round(
            duration_similarity * 0.60
            + mileage_similarity * 0.40
        )

        fee_difference = abs(
            left_offer.monthly_fee
            - right_offer.monthly_fee
        )

        lower = min(
            left_offer.monthly_fee,
            right_offer.monthly_fee,
        )

        price_difference_percent = (
            round(
                fee_difference
                / lower
                * 100,
                2,
            )
            if lower > 0
            else 0.0
        )

        return ComparisonResult(
            brand=pair.left_brand,
            model=pair.left_model,
            fuel_type_a=pair.left_fuel,
            fuel_type_b=pair.right_fuel,
            vehicle_confidence=100,
            vehicle_match_type="NORMALIZED_IDENTITY_MATCH",
            contract_comparable=contract_comparable,
            contract_difference=(
                self._contract_difference(
                    left_offer,
                    right_offer,
                )
            ),
            duration_similarity=duration_similarity,
            mileage_similarity=mileage_similarity,
            contract_similarity=contract_similarity,
            offers=[
                left_offer,
                right_offer,
            ],
            best_provider=(
                left_offer.provider
                if (
                    left_offer.monthly_fee
                    <= right_offer.monthly_fee
                )
                else right_offer.provider
            ),
            best_monthly_fee=min(
                left_offer.monthly_fee,
                right_offer.monthly_fee,
            ),
            price_difference=fee_difference,
            annual_saving=fee_difference * 12,
            price_winner=(
                (
                    left_offer.provider
                    if (
                        left_offer.monthly_fee
                        < right_offer.monthly_fee
                    )
                    else right_offer.provider
                )
                if contract_comparable
                else "NOT_COMPARABLE"
            ),
            price_winner_is_valid=contract_comparable,
            price_difference_percent=price_difference_percent,
            variant_confidence=100,
            variant_match_type="NORMALIZED_VARIANT_CONTEXT",
            variant_key_a=(
                f"{pair.left_brand}|"
                f"{pair.left_model}|"
                f"{pair.left_fuel}"
            ),
            variant_key_b=(
                f"{pair.right_brand}|"
                f"{pair.right_model}|"
                f"{pair.right_fuel}"
            ),
        )

    @staticmethod
    def _contract_difference(
        a,
        b,
    ) -> str:

        parts = []

        if a.duration != b.duration:
            parts.append(
                f"Duration differs: "
                f"{a.duration} vs "
                f"{b.duration} months."
            )

        if a.mileage != b.mileage:
            parts.append(
                f"Mileage differs: "
                f"{a.mileage:,} vs "
                f"{b.mileage:,} km/year."
            )

        return "; ".join(parts)

    @staticmethod
    def _duration_similarity(
        difference: int,
    ) -> int:

        if difference == 0:
            return 100
        if difference <= 12:
            return 85
        if difference <= 24:
            return 70
        if difference <= 36:
            return 55
        return 40

    @staticmethod
    def _mileage_similarity(
        difference: int,
    ) -> int:

        if difference == 0:
            return 100
        if difference <= 5000:
            return 90
        if difference <= 10000:
            return 80
        if difference <= 15000:
            return 70
        return 60
