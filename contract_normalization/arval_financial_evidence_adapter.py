from dataclasses import dataclass
from typing import Optional

from contract_normalization.arval_financial_state_observer import (
    FinancialStateObservationResult,
    OBSERVED,
)


@dataclass(frozen=True)
class ArvalFinancialEvidence:
    source_type: str
    source_url: str
    source_text: str
    down_payment_percent: Optional[float]
    down_payment_amount_huf: Optional[int]
    monthly_fee: int
    duration: Optional[int]
    mileage: Optional[int]
    pricing_basis: str
    applicability_scope: str


class ArvalFinancialEvidenceAdapter:
    """
    Converts an explicit exact-offer Arval financial observation into a
    conservative provider-evidence payload.

    UNRESOLVED observations are never promoted.
    """

    def build(
        self,
        observation: FinancialStateObservationResult,
    ) -> Optional[ArvalFinancialEvidence]:

        if observation.status != OBSERVED:
            return None

        if len(observation.states) != 1:
            return None

        state = observation.states[0]

        if (
            state.down_payment_percent is None
            and state.down_payment_amount_huf is None
        ):
            return None

        if state.down_payment_percent == 0.0:
            basis = "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
        elif state.down_payment_percent is not None:
            basis = "OBSERVED_DOWN_PAYMENT_PERCENT_STATE"
        else:
            basis = "OBSERVED_DOWN_PAYMENT_AMOUNT_STATE"

        return ArvalFinancialEvidence(
            source_type="PROVIDER_OFFER_PAGE",
            source_url=observation.source_url,
            source_text=state.source_text,
            down_payment_percent=state.down_payment_percent,
            down_payment_amount_huf=state.down_payment_amount_huf,
            monthly_fee=state.monthly_fee,
            duration=state.duration,
            mileage=state.mileage,
            pricing_basis=basis,
            applicability_scope="EXACT_OFFER",
        )

    @staticmethod
    def to_candidate_payload(
        evidence: ArvalFinancialEvidence,
    ) -> dict:

        payload = {
            "source_type": evidence.source_type,
            "source_url": evidence.source_url,
            "source_text": evidence.source_text,
            "down_payment_percent": evidence.down_payment_percent,
            "monthly_fee": evidence.monthly_fee,
            "duration": evidence.duration,
            "mileage": evidence.mileage,
            "pricing_basis": evidence.pricing_basis,
            "applicability_scope": evidence.applicability_scope,
        }

        if evidence.down_payment_amount_huf is not None:
            payload["down_payment_amount_huf"] = (
                evidence.down_payment_amount_huf
            )

        return payload
