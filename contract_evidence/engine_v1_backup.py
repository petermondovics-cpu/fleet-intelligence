from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from models.offer import Offer


@dataclass
class ContractEvidence:
    """
    Observed contract-pricing evidence derived only from offers
    belonging to the same provider and vehicle identity.

    Evidence is deliberately conservative:
    - term evidence requires same mileage
    - mileage evidence requires same duration
    - provider and vehicle identity must match
    - powertrain must match
    """

    evidence_type: str

    provider: str

    brand: str
    model: str

    source_duration: int
    target_duration: int

    source_mileage: int
    target_mileage: int

    source_monthly_fee: int
    target_monthly_fee: int

    sample_size: int

    factor: float

    source_offer: Offer
    target_offer: Offer


class ContractEvidenceEngine:

    def __init__(self):
        pass

    def find_all(
        self,
        offers: List[Offer],
    ) -> List[ContractEvidence]:

        results: List[ContractEvidence] = []

        groups = self._group_offers(
            offers
        )

        for group in groups.values():

            results.extend(
                self._find_group_evidence(
                    group
                )
            )

        return sorted(
            results,
            key=lambda item: (
                item.provider,
                item.brand,
                item.model,
                item.evidence_type,
                item.source_duration,
                item.source_mileage,
                item.target_duration,
                item.target_mileage,
            ),
        )

    def find_for_comparison(
        self,
        comparison,
        offers: List[Offer],
    ) -> Dict[str, Optional[dict]]:

        comparison_offers = comparison.offers

        if len(comparison_offers) < 2:
            return {
                "term_evidence": None,
                "mileage_evidence": None,
            }

        offer_a = comparison_offers[0]
        offer_b = comparison_offers[1]

        all_evidence = self.find_all(
            offers
        )

        term_evidence = self._find_matching_evidence(
            all_evidence,
            offer_a,
            offer_b,
            "TERM",
        )

        mileage_evidence = self._find_matching_evidence(
            all_evidence,
            offer_a,
            offer_b,
            "MILEAGE",
        )

        return {
            "term_evidence": (
                self._to_dict(term_evidence)
                if term_evidence
                else None
            ),
            "mileage_evidence": (
                self._to_dict(mileage_evidence)
                if mileage_evidence
                else None
            ),
        }

    def build_evidence(
        self,
        source_offer: Offer,
        target_offer: Offer,
        sample_size: int = 1,
    ) -> Optional[dict]:

        if not self._same_provider(
            source_offer,
            target_offer,
        ):
            return None

        if not self._same_vehicle(
            source_offer,
            target_offer,
        ):
            return None

        if (
            source_offer.duration
            != target_offer.duration
            and
            source_offer.mileage
            == target_offer.mileage
        ):
            evidence = self._make_evidence(
                "TERM",
                source_offer,
                target_offer,
                sample_size,
            )

            return self._to_dict(
                evidence
            )

        if (
            source_offer.duration
            == target_offer.duration
            and
            source_offer.mileage
            != target_offer.mileage
        ):
            evidence = self._make_evidence(
                "MILEAGE",
                source_offer,
                target_offer,
                sample_size,
            )

            return self._to_dict(
                evidence
            )

        return None

    def _find_group_evidence(
        self,
        offers: List[Offer],
    ) -> List[ContractEvidence]:

        results = []

        for index, source in enumerate(
            offers
        ):

            for target in offers[index + 1:]:

                if not self._same_provider(
                    source,
                    target,
                ):
                    continue

                if not self._same_vehicle(
                    source,
                    target,
                ):
                    continue

                # ----------------------------------------
                # TERM
                # ----------------------------------------

                if (
                    source.duration
                    != target.duration
                    and
                    source.mileage
                    == target.mileage
                ):

                    results.append(
                        self._make_evidence(
                            "TERM",
                            source,
                            target,
                            len(offers),
                        )
                    )

                # ----------------------------------------
                # MILEAGE
                # ----------------------------------------

                elif (
                    source.duration
                    == target.duration
                    and
                    source.mileage
                    != target.mileage
                ):

                    results.append(
                        self._make_evidence(
                            "MILEAGE",
                            source,
                            target,
                            len(offers),
                        )
                    )

        return results

    def _find_matching_evidence(
        self,
        evidence: List[ContractEvidence],
        offer_a: Offer,
        offer_b: Offer,
        evidence_type: str,
    ) -> Optional[ContractEvidence]:

        candidates = []

        for item in evidence:

            if (
                item.evidence_type
                != evidence_type
            ):
                continue

            if (
                item.provider
                != offer_a.provider
                and
                item.provider
                != offer_b.provider
            ):
                continue

            if (
                not self._same_vehicle(
                    item.source_offer,
                    offer_a,
                )
            ):
                continue

            if (
                item.source_offer.provider
                != offer_a.provider
                and
                item.source_offer.provider
                != offer_b.provider
            ):
                continue

            candidates.append(
                item
            )

        if not candidates:
            return None

        # Prefer evidence that directly describes
        # one of the two comparison offers.
        for item in candidates:

            if (
                self._offer_matches_contract(
                    item.source_offer,
                    offer_a,
                )
                and
                self._offer_matches_contract(
                    item.target_offer,
                    offer_b,
                )
            ):
                return item

            if (
                self._offer_matches_contract(
                    item.source_offer,
                    offer_b,
                )
                and
                self._offer_matches_contract(
                    item.target_offer,
                    offer_a,
                )
            ):
                return item

        return candidates[0]

    def _make_evidence(
        self,
        evidence_type: str,
        source: Offer,
        target: Offer,
        sample_size: int,
    ) -> ContractEvidence:

        if (
            source.monthly_fee <= 0
            or target.monthly_fee <= 0
        ):
            raise ValueError(
                "Monthly fee must be positive."
            )

        factor = round(
            target.monthly_fee
            / source.monthly_fee,
            6,
        )

        return ContractEvidence(
            evidence_type=evidence_type,
            provider=source.provider,
            brand=source.brand,
            model=source.model,
            source_duration=source.duration,
            target_duration=target.duration,
            source_mileage=source.mileage,
            target_mileage=target.mileage,
            source_monthly_fee=source.monthly_fee,
            target_monthly_fee=target.monthly_fee,
            sample_size=max(
                1,
                sample_size,
            ),
            factor=factor,
            source_offer=source,
            target_offer=target,
        )

    def _group_offers(
        self,
        offers: List[Offer],
    ) -> Dict[Tuple[str, str, str], List[Offer]]:

        groups: Dict[
            Tuple[str, str, str],
            List[Offer],
        ] = {}

        for offer in offers:

            key = (
                self._normalize_text(
                    offer.provider
                ),
                self._normalize_text(
                    offer.brand
                ),
                self._normalize_model(
                    offer.model
                ),
                self._normalize_text(
                    offer.fuel_type
                ),
            )

            groups.setdefault(
                key,
                [],
            ).append(
                offer
            )

        return groups

    def _same_provider(
        self,
        offer_a: Offer,
        offer_b: Offer,
    ) -> bool:

        return (
            self._normalize_text(
                offer_a.provider
            )
            ==
            self._normalize_text(
                offer_b.provider
            )
        )

    def _same_vehicle(
        self,
        offer_a: Offer,
        offer_b: Offer,
    ) -> bool:

        return (
            self._normalize_text(
                offer_a.brand
            )
            ==
            self._normalize_text(
                offer_b.brand
            )
            and
            self._normalize_model(
                offer_a.model
            )
            ==
            self._normalize_model(
                offer_b.model
            )
            and
            self._normalize_text(
                offer_a.fuel_type
            )
            ==
            self._normalize_text(
                offer_b.fuel_type
            )
        )

    def _normalize_model(
        self,
        value: str,
    ) -> str:

        normalized = (
            self._normalize_text(
                value
            )
        )

        aliases = {
            "COMBO CARGO": "COMBO",
            "S CROSS": "S-CROSS",
            "SCROSS": "S-CROSS",
        }

        return aliases.get(
            normalized,
            normalized,
        )

    def _normalize_text(
        self,
        value: str,
    ) -> str:

        return (
            str(value or "")
            .strip()
            .upper()
            .replace("-", " ")
            .replace("_", " ")
        )

    def _offer_matches_contract(
        self,
        offer_a: Offer,
        offer_b: Offer,
    ) -> bool:

        return (
            offer_a.provider
            == offer_b.provider
            and
            self._same_vehicle(
                offer_a,
                offer_b,
            )
            and
            offer_a.duration
            == offer_b.duration
            and
            offer_a.mileage
            == offer_b.mileage
        )

    def _to_dict(
        self,
        evidence: ContractEvidence,
    ) -> dict:

        return {
            "provider": evidence.provider,
            "brand": evidence.brand,
            "model": evidence.model,
            "source_duration": evidence.source_duration,
            "target_duration": evidence.target_duration,
            "source_mileage": evidence.source_mileage,
            "target_mileage": evidence.target_mileage,
            "source_monthly_fee": evidence.source_monthly_fee,
            "target_monthly_fee": evidence.target_monthly_fee,
            "sample_size": evidence.sample_size,
            "factor": evidence.factor,
        }
