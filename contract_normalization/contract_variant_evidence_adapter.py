from dataclasses import dataclass
from typing import Optional, Tuple

from contract_normalization.ayvens_contract_variant_observer import (
    ContractVariantObservationResult,
)


@dataclass(frozen=True)
class ObservedContractNormalizationEvidence:
    provider: str
    source_duration: int
    target_duration: int
    mileage: int

    source_monthly_fee: int
    target_monthly_fee: int

    sample_size: int

    source_url: str
    evidence_text: str


class ContractVariantEvidenceAdapter:
    """
    Contract Variant Evidence Adapter V1.

    Converts exact-offer observed contract states into the evidence shape
    already expected by the contract normalization layer.

    No evidence is produced unless both source and target coordinates were
    directly observed at the same annual mileage.
    """

    def build_duration_evidence(
        self,
        observation: ContractVariantObservationResult,
        *,
        source_duration: int,
        target_duration: int,
        mileage: int,
    ) -> Optional[
        ObservedContractNormalizationEvidence
    ]:

        states = {
            (
                item.duration,
                item.mileage,
            ): item
            for item in (
                observation.observations
            )
        }

        source = states.get(
            (
                source_duration,
                mileage,
            )
        )

        target = states.get(
            (
                target_duration,
                mileage,
            )
        )

        if (
            source is None
            or target is None
        ):
            return None

        return ObservedContractNormalizationEvidence(
            provider=observation.provider,
            source_duration=source_duration,
            target_duration=target_duration,
            mileage=mileage,
            source_monthly_fee=(
                source.monthly_fee
            ),
            target_monthly_fee=(
                target.monthly_fee
            ),
            sample_size=1,
            source_url=(
                observation.source_url
            ),
            evidence_text=(
                "Direct exact-offer contract variant observation: "
                f"{source_duration} hó / {mileage} km/év = "
                f"{source.monthly_fee} Ft/hó; "
                f"{target_duration} hó / {mileage} km/év = "
                f"{target.monthly_fee} Ft/hó."
            ),
        )

    @staticmethod
    def to_normalizer_dict(
        evidence: ObservedContractNormalizationEvidence,
    ) -> dict:

        return {
            "provider": evidence.provider,
            "source_monthly_fee": (
                evidence
                .source_monthly_fee
            ),
            "target_monthly_fee": (
                evidence
                .target_monthly_fee
            ),
            "sample_size": (
                evidence
                .sample_size
            ),
            "source_duration": (
                evidence
                .source_duration
            ),
            "target_duration": (
                evidence
                .target_duration
            ),
            "mileage": evidence.mileage,
            "source_url": (
                evidence
                .source_url
            ),
            "evidence_text": (
                evidence
                .evidence_text
            ),
        }
