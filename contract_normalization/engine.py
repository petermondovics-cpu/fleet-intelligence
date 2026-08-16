from dataclasses import dataclass
from typing import Dict, List, Optional

from comparison.engine import ComparisonResult
from models.offer import Offer


@dataclass
class ContractNormalizationResult:
    brand: str
    model: str
    provider_a: str
    provider_b: str
    duration_a: int
    duration_b: int
    mileage_a: int
    mileage_b: int
    duration_difference: int
    mileage_difference: int
    duration_similarity: int
    mileage_similarity: int
    contract_similarity: int
    normalization_status: str
    normalization_method: str
    normalized_monthly_fee_a: Optional[int]
    normalized_monthly_fee_b: Optional[int]
    normalized_price_available: bool
    normalization_reason: str

    normalization_confidence: int
    normalization_factor_a: Optional[float]
    normalization_factor_b: Optional[float]
    normalization_evidence: str

    normalization_quality: str

    term_normalization_available: bool
    term_normalization_factor_a: Optional[float]
    term_normalization_factor_b: Optional[float]
    term_normalization_confidence: int
    term_normalization_evidence: str

    mileage_normalization_available: bool
    mileage_normalization_factor_a: Optional[float]
    mileage_normalization_factor_b: Optional[float]
    mileage_normalization_confidence: int
    mileage_normalization_evidence: str


class ContractNormalizationEngine:
    """
    V4 contract normalization.

    Directly comparable contracts use nominal prices.
    Different contract dimensions are normalized only when
    provider-specific observed evidence supports the change.

    Flat evidence remains backward compatible:
    - differing duration -> term evidence
    - differing mileage -> mileage evidence

    When both dimensions differ, term and mileage evidence may
    belong to different providers. Each provider is normalized
    independently toward the common target contract.
    """

    def normalize(
        self,
        comparison: ComparisonResult,
    ) -> ContractNormalizationResult:

        offer_a = comparison.offers[0]
        offer_b = comparison.offers[1]

        duration_difference = abs(
            offer_a.duration - offer_b.duration
        )
        mileage_difference = abs(
            offer_a.mileage - offer_b.mileage
        )

        duration_similarity = self._duration_similarity(
            duration_difference
        )
        mileage_similarity = self._mileage_similarity(
            mileage_difference
        )
        contract_similarity = round(
            duration_similarity * 0.60
            + mileage_similarity * 0.40
        )

        if duration_difference == 0 and mileage_difference == 0:
            return self._build_result(
                comparison,
                "NORMALIZED",
                "NOMINAL_PRICE",
                offer_a.monthly_fee,
                offer_b.monthly_fee,
                True,
                "Contracts have identical duration and mileage.",
                100,
                1.0,
                1.0,
                "Identical contract structure.",
                "DIRECT",
                True,
                1.0,
                1.0,
                100,
                "Identical contract duration.",
                True,
                1.0,
                1.0,
                100,
                "Identical contract mileage.",
            )

        if duration_difference > 0 and mileage_difference > 0:
            reason = (
                f"Duration differs: {offer_a.duration} vs "
                f"{offer_b.duration} months; "
                f"Mileage differs: {offer_a.mileage:,} vs "
                f"{offer_b.mileage:,} km/year."
            )
            return self._build_result(
                comparison,
                "NEEDS_TERM_AND_MILEAGE_NORMALIZATION",
                "NONE",
                None,
                None,
                False,
                reason,
                0,
                None,
                None,
                "",
                "INSUFFICIENT_EVIDENCE",
                False,
                None,
                None,
                0,
                "",
                False,
                None,
                None,
                0,
                "",
            )

        if duration_difference > 0:
            return self._build_result(
                comparison,
                "NEEDS_TERM_NORMALIZATION",
                "NONE",
                None,
                None,
                False,
                (
                    f"Duration differs: {offer_a.duration} vs "
                    f"{offer_b.duration} months."
                ),
                0,
                None,
                None,
                "",
                "INSUFFICIENT_EVIDENCE",
                False,
                None,
                None,
                0,
                "",
                True,
                1.0,
                1.0,
                100,
                "Mileage already identical.",
            )

        return self._build_result(
            comparison,
            "NEEDS_MILEAGE_NORMALIZATION",
            "NONE",
            None,
            None,
            False,
            (
                f"Mileage differs: {offer_a.mileage:,} vs "
                f"{offer_b.mileage:,} km/year."
            ),
            0,
            None,
            None,
            "",
            "INSUFFICIENT_EVIDENCE",
            True,
            1.0,
            1.0,
            100,
            "Contract duration already identical.",
            False,
            None,
            None,
            0,
            "",
        )

    def normalize_with_evidence(
        self,
        comparison: ComparisonResult,
        evidence: Dict,
    ) -> ContractNormalizationResult:

        base = self.normalize(comparison)

        if base.normalization_status == "NORMALIZED":
            return base

        term_evidence = evidence.get("term_evidence")
        mileage_evidence = evidence.get("mileage_evidence")

        # Backward-compatible flat evidence classification.
        if (
            term_evidence is None
            and mileage_evidence is None
            and self._contains_contract_evidence(evidence)
        ):
            sd = evidence.get("source_duration")
            td = evidence.get("target_duration")
            sm = evidence.get("source_mileage")
            tm = evidence.get("target_mileage")

            if sd is not None and td is not None and sd != td:
                term_evidence = evidence
            elif sm is not None and tm is not None and sm != tm:
                mileage_evidence = evidence

        term_result = None
        mileage_result = None

        if term_evidence is not None:
            term_result = self._apply_term_evidence(
                comparison, term_evidence
            )

        if mileage_evidence is not None:
            mileage_result = self._apply_mileage_evidence(
                comparison, mileage_evidence
            )

        if term_result is None and mileage_result is None:
            return base

        return self._combine_results(
            base,
            term_result,
            mileage_result,
        )

    def _apply_term_evidence(
        self,
        comparison: ComparisonResult,
        evidence: Dict,
    ) -> Optional[dict]:

        offer_a, offer_b = comparison.offers[:2]

        provider = evidence.get("provider")
        source_duration = evidence.get("source_duration")
        target_duration = evidence.get("target_duration")
        source_mileage = evidence.get("source_mileage")
        target_mileage = evidence.get("target_mileage")
        source_fee = evidence.get("source_monthly_fee")
        target_fee = evidence.get("target_monthly_fee")
        sample_size = evidence.get("sample_size", 0)

        if not provider or source_duration is None or target_duration is None:
            return None
        if source_fee is None or target_fee is None:
            return None
        if source_fee <= 0 or target_fee <= 0 or sample_size <= 0:
            return None

        if offer_a.provider == provider:
            offer = offer_a
            is_a = True
        elif offer_b.provider == provider:
            offer = offer_b
            is_a = False
        else:
            return None

        if offer.duration != source_duration:
            return None

        # Term evidence must not cross a mileage dimension.
        if source_mileage is not None or target_mileage is not None:
            if source_mileage is None or target_mileage is None:
                return None
            if offer.mileage != source_mileage:
                return None
            if source_mileage != target_mileage:
                return None
        elif offer_a.mileage != offer_b.mileage:
            return None

        factor = round(target_fee / source_fee, 6)
        estimated = round(offer.monthly_fee * factor)
        confidence = self._evidence_confidence(sample_size)

        text = (
            f"Observed provider term factor: {provider}, "
            f"{source_duration} -> {target_duration} months, "
            f"{source_fee:,} -> {target_fee:,} Ft, "
            f"sample size: {sample_size}."
        )

        if is_a:
            return {
                "normalized_a": estimated,
                "normalized_b": (
                    offer_b.monthly_fee
                    if (
                        offer_b.duration == target_duration
                        and offer_b.mileage == offer.mileage
                    )
                    else None
                ),
                "factor_a": factor,
                "factor_b": None,
                "confidence": confidence,
                "evidence": text,
            }

        return {
            "normalized_a": (
                offer_a.monthly_fee
                if (
                    offer_a.duration == target_duration
                    and offer_a.mileage == offer.mileage
                )
                else None
            ),
            "normalized_b": estimated,
            "factor_a": None,
            "factor_b": factor,
            "confidence": confidence,
            "evidence": text,
        }

    def _apply_mileage_evidence(
        self,
        comparison: ComparisonResult,
        evidence: Dict,
    ) -> Optional[dict]:

        offer_a, offer_b = comparison.offers[:2]

        provider = evidence.get("provider")
        source_mileage = evidence.get("source_mileage")
        target_mileage = evidence.get("target_mileage")
        source_duration = evidence.get("source_duration")
        target_duration = evidence.get("target_duration")
        source_fee = evidence.get("source_monthly_fee")
        target_fee = evidence.get("target_monthly_fee")
        sample_size = evidence.get("sample_size", 0)

        if not provider or source_mileage is None or target_mileage is None:
            return None
        if source_fee is None or target_fee is None:
            return None
        if source_fee <= 0 or target_fee <= 0 or sample_size <= 0:
            return None

        if offer_a.provider == provider:
            offer = offer_a
            is_a = True
        elif offer_b.provider == provider:
            offer = offer_b
            is_a = False
        else:
            return None

        if offer.mileage != source_mileage:
            return None

        # Mileage evidence must not cross a duration dimension.
        if source_duration is not None or target_duration is not None:
            if source_duration is None or target_duration is None:
                return None
            if offer.duration != source_duration:
                return None
        elif offer_a.duration != offer_b.duration:
            return None

        factor = round(target_fee / source_fee, 6)
        estimated = round(offer.monthly_fee * factor)
        confidence = self._evidence_confidence(sample_size)

        text = (
            f"Observed provider mileage factor: {provider}, "
            f"{source_mileage:,} -> {target_mileage:,} km/year, "
            f"{source_fee:,} -> {target_fee:,} Ft, "
            f"sample size: {sample_size}."
        )

        if is_a:
            return {
                "normalized_a": estimated,
                "normalized_b": (
                    offer_b.monthly_fee
                    if (
                        offer_b.mileage == target_mileage
                        and (
                            target_duration is None
                            or offer_b.duration == target_duration
                        )
                    )
                    else None
                ),
                "factor_a": factor,
                "factor_b": None,
                "confidence": confidence,
                "evidence": text,
            }

        return {
            "normalized_a": (
                offer_a.monthly_fee
                if (
                    offer_a.mileage == target_mileage
                    and (
                        target_duration is None
                        or offer_a.duration == target_duration
                    )
                )
                else None
            ),
            "normalized_b": estimated,
            "factor_a": None,
            "factor_b": factor,
            "confidence": confidence,
            "evidence": text,
        }

    def _combine_results(
        self,
        base: ContractNormalizationResult,
        term_result: Optional[dict],
        mileage_result: Optional[dict],
    ) -> ContractNormalizationResult:

        term_available = term_result is not None
        mileage_available = mileage_result is not None

        term_confidence = (
            term_result["confidence"] if term_result else 0
        )
        mileage_confidence = (
            mileage_result["confidence"] if mileage_result else 0
        )

        term_factor_a = (
            term_result["factor_a"] if term_result else None
        )
        term_factor_b = (
            term_result["factor_b"] if term_result else None
        )
        mileage_factor_a = (
            mileage_result["factor_a"] if mileage_result else None
        )
        mileage_factor_b = (
            mileage_result["factor_b"] if mileage_result else None
        )

        term_evidence = (
            term_result["evidence"] if term_result else ""
        )
        mileage_evidence = (
            mileage_result["evidence"] if mileage_result else ""
        )

        duration_differs = base.duration_difference > 0
        mileage_differs = base.mileage_difference > 0

        # Each provider is moved independently toward the
        # common target contract. Do not multiply unrelated
        # evidence factors from different providers.
        normalized_a = None
        normalized_b = None

        if duration_differs and not mileage_differs:
            if term_result:
                normalized_a = term_result["normalized_a"]
                normalized_b = term_result["normalized_b"]

        elif not duration_differs and mileage_differs:
            if mileage_result:
                normalized_a = mileage_result["normalized_a"]
                normalized_b = mileage_result["normalized_b"]

        elif duration_differs and mileage_differs:
            if term_result and mileage_result:
                normalized_a = (
                    term_result["normalized_a"]
                    if term_result["normalized_a"] is not None
                    else mileage_result["normalized_a"]
                )
                normalized_b = (
                    mileage_result["normalized_b"]
                    if mileage_result["normalized_b"] is not None
                    else term_result["normalized_b"]
                )

        fully_supported = (
            (not duration_differs or term_available)
            and (not mileage_differs or mileage_available)
        )

        normalized_price_available = (
            fully_supported
            and normalized_a is not None
            and normalized_b is not None
        )

        if normalized_price_available:
            status = "NORMALIZATION_ESTIMATED"
            quality = "EVIDENCE_SUPPORTED"
        elif term_available or mileage_available:
            status = "PARTIALLY_NORMALIZED"
            quality = "PARTIALLY_NORMALIZED"
        else:
            status = base.normalization_status
            quality = "INSUFFICIENT_EVIDENCE"

        if term_available and mileage_available:
            method = "OBSERVED_PROVIDER_TERM_AND_MILEAGE_FACTORS"
        elif term_available:
            method = "OBSERVED_PROVIDER_TERM_FACTOR"
        elif mileage_available:
            method = "OBSERVED_PROVIDER_MILEAGE_FACTOR"
        else:
            method = base.normalization_method

        if term_available and mileage_available:
            confidence = min(term_confidence, mileage_confidence)
        elif term_available:
            confidence = term_confidence
        elif mileage_available:
            confidence = mileage_confidence
        else:
            confidence = base.normalization_confidence

        if term_available:
            factor_a = term_factor_a
            factor_b = term_factor_b
        elif mileage_available:
            factor_a = mileage_factor_a
            factor_b = mileage_factor_b
        else:
            factor_a = base.normalization_factor_a
            factor_b = base.normalization_factor_b

        evidence_parts = [
            value for value in (
                term_evidence,
                mileage_evidence,
            )
            if value
        ]

        if normalized_price_available:
            reason = (
                "Estimated using validated "
                "provider-specific evidence."
            )
        elif term_available or mileage_available:
            reason = (
                "Partial normalization available; "
                "not all differing contract dimensions "
                "are supported by evidence."
            )
        else:
            reason = base.normalization_reason

        return ContractNormalizationResult(
            brand=base.brand,
            model=base.model,
            provider_a=base.provider_a,
            provider_b=base.provider_b,
            duration_a=base.duration_a,
            duration_b=base.duration_b,
            mileage_a=base.mileage_a,
            mileage_b=base.mileage_b,
            duration_difference=base.duration_difference,
            mileage_difference=base.mileage_difference,
            duration_similarity=base.duration_similarity,
            mileage_similarity=base.mileage_similarity,
            contract_similarity=base.contract_similarity,
            normalization_status=status,
            normalization_method=method,
            normalized_monthly_fee_a=normalized_a,
            normalized_monthly_fee_b=normalized_b,
            normalized_price_available=normalized_price_available,
            normalization_reason=reason,
            normalization_confidence=confidence,
            normalization_factor_a=factor_a,
            normalization_factor_b=factor_b,
            normalization_evidence=" ".join(evidence_parts),
            normalization_quality=quality,
            term_normalization_available=term_available,
            term_normalization_factor_a=term_factor_a,
            term_normalization_factor_b=term_factor_b,
            term_normalization_confidence=term_confidence,
            term_normalization_evidence=term_evidence,
            mileage_normalization_available=mileage_available,
            mileage_normalization_factor_a=mileage_factor_a,
            mileage_normalization_factor_b=mileage_factor_b,
            mileage_normalization_confidence=mileage_confidence,
            mileage_normalization_evidence=mileage_evidence,
        )

    def _contains_contract_evidence(
        self,
        evidence: Dict,
    ) -> bool:
        required = (
            "provider",
            "source_monthly_fee",
            "target_monthly_fee",
            "sample_size",
        )
        return all(
            key in evidence
            for key in required
        )

    def _evidence_confidence(
        self,
        sample_size: int,
    ) -> int:
        if sample_size <= 0:
            return 0
        if sample_size == 1:
            return 60
        if sample_size <= 4:
            return 70
        if sample_size <= 9:
            return 80
        return 90

    def _build_result(
        self,
        comparison: ComparisonResult,
        normalization_status: str,
        normalization_method: str,
        normalized_monthly_fee_a: Optional[int],
        normalized_monthly_fee_b: Optional[int],
        normalized_price_available: bool,
        normalization_reason: str,
        normalization_confidence: int,
        normalization_factor_a: Optional[float],
        normalization_factor_b: Optional[float],
        normalization_evidence: str,
        normalization_quality: str,
        term_normalization_available: bool,
        term_normalization_factor_a: Optional[float],
        term_normalization_factor_b: Optional[float],
        term_normalization_confidence: int,
        term_normalization_evidence: str,
        mileage_normalization_available: bool,
        mileage_normalization_factor_a: Optional[float],
        mileage_normalization_factor_b: Optional[float],
        mileage_normalization_confidence: int,
        mileage_normalization_evidence: str,
    ) -> ContractNormalizationResult:

        offer_a, offer_b = comparison.offers[:2]

        duration_difference = abs(
            offer_a.duration - offer_b.duration
        )
        mileage_difference = abs(
            offer_a.mileage - offer_b.mileage
        )

        duration_similarity = self._duration_similarity(
            duration_difference
        )
        mileage_similarity = self._mileage_similarity(
            mileage_difference
        )

        return ContractNormalizationResult(
            brand=comparison.brand,
            model=comparison.model,
            provider_a=offer_a.provider,
            provider_b=offer_b.provider,
            duration_a=offer_a.duration,
            duration_b=offer_b.duration,
            mileage_a=offer_a.mileage,
            mileage_b=offer_b.mileage,
            duration_difference=duration_difference,
            mileage_difference=mileage_difference,
            duration_similarity=duration_similarity,
            mileage_similarity=mileage_similarity,
            contract_similarity=round(
                duration_similarity * 0.60
                + mileage_similarity * 0.40
            ),
            normalization_status=normalization_status,
            normalization_method=normalization_method,
            normalized_monthly_fee_a=normalized_monthly_fee_a,
            normalized_monthly_fee_b=normalized_monthly_fee_b,
            normalized_price_available=normalized_price_available,
            normalization_reason=normalization_reason,
            normalization_confidence=normalization_confidence,
            normalization_factor_a=normalization_factor_a,
            normalization_factor_b=normalization_factor_b,
            normalization_evidence=normalization_evidence,
            normalization_quality=normalization_quality,
            term_normalization_available=term_normalization_available,
            term_normalization_factor_a=term_normalization_factor_a,
            term_normalization_factor_b=term_normalization_factor_b,
            term_normalization_confidence=term_normalization_confidence,
            term_normalization_evidence=term_normalization_evidence,
            mileage_normalization_available=mileage_normalization_available,
            mileage_normalization_factor_a=mileage_normalization_factor_a,
            mileage_normalization_factor_b=mileage_normalization_factor_b,
            mileage_normalization_confidence=mileage_normalization_confidence,
            mileage_normalization_evidence=mileage_normalization_evidence,
        )

    def normalize_all(
        self,
        comparisons: List[ComparisonResult],
    ) -> List[ContractNormalizationResult]:
        return [
            self.normalize(comparison)
            for comparison in comparisons
        ]

    def _duration_similarity(
        self,
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

    def _mileage_similarity(
        self,
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
