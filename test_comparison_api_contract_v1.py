from datetime import datetime

from api.comparison_contract import API_VERSION
from api.comparison_presenter import ComparisonPresenterV1
from comparison.full_comparison_orchestrator import (
    FullComparisonBarrier,
    FullComparisonResult,
)
from models.composite_offer import CompositeOffer
from models.financial_conditions import (
    DownPayment,
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    FinancialConditions,
    FinancialEvidence,
    ServicePackage,
)
from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED as VEHICLE_EVIDENCE_OBSERVED,
    VehicleEvidence,
    VehicleSpecification,
)


class Wrapped:
    def __init__(self, composite):
        self.composite = composite


def unknown_dp():
    return DownPayment(
        percent=None,
        amount=None,
        status=EVIDENCE_UNKNOWN,
        evidence=FinancialEvidence(
            status=EVIDENCE_UNKNOWN,
        ),
    )


def observed_zero_dp():
    return DownPayment(
        percent=0.0,
        amount=None,
        status=EVIDENCE_OBSERVED,
        evidence=FinancialEvidence(
            status=EVIDENCE_OBSERVED,
            source_url="https://example.test/ayvens",
            source_text=(
                "Observed zero-down-payment state."
            ),
        ),
    )


def observed_vehicle_evidence(
    value: str,
    field_name: str,
):
    return VehicleEvidence(
        status=VEHICLE_EVIDENCE_OBSERVED,
        source_url="https://example.test/vehicle",
        source_text=f"{field_name}: {value}",
    )


def composite(
    provider,
    fee,
    duration,
    trim,
):
    offer = Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim=trim,
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=20000,
        url=(
            f"https://example.test/"
            f"{provider.lower()}"
        ),
        scraped_at=datetime.now(),
    )

    vehicle = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim=trim,
        fuel_type="PHEV",
        brand_evidence=observed_vehicle_evidence(
            "BYD",
            "brand",
        ),
        model_evidence=observed_vehicle_evidence(
            "ATTO 2",
            "model",
        ),
        trim_evidence=observed_vehicle_evidence(
            trim,
            "trim",
        ),
        fuel_evidence=observed_vehicle_evidence(
            "PHEV",
            "fuel_type",
        ),
    )

    return CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=ServicePackage(),
        financial=FinancialConditions(
            monthly_fee=fee,
            down_payment=unknown_dp(),
        ),
    )


def main():
    left = Wrapped(
        composite(
            "Arval",
            192312,
            60,
            "BOOST",
        )
    )

    right = Wrapped(
        composite(
            "Ayvens",
            189990,
            48,
            "DM-i",
        )
    )

    enriched_right = FinancialConditions(
        monthly_fee=223990,
        down_payment=observed_zero_dp(),
    )

    result = FullComparisonResult(
        status="INSUFFICIENT_EVIDENCE",
        price_comparison_allowed=False,
        price_winner=None,
        normalized_monthly_fee_left=None,
        normalized_monthly_fee_right=None,
        barriers=(
            FullComparisonBarrier(
                code=(
                    "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
                ),
                message=(
                    "Down payment is not explicitly "
                    "observed for both offers."
                ),
                hard=False,
            ),
        ),
        vehicle_status="COMPARABLE",
        service_status="INSUFFICIENT_EVIDENCE",
        equipment_status="INSUFFICIENT_EVIDENCE",
        contract_status=(
            "NEEDS_TERM_NORMALIZATION"
        ),
        financial_status=(
            "INSUFFICIENT_EVIDENCE"
        ),
        contract_normalization_method="NONE",
        contract_normalization_confidence=0,
        equipment_score_left=None,
        equipment_score_right=None,
        variant_status="INSUFFICIENT_EVIDENCE",
    )

    dto = ComparisonPresenterV1().present(
        result,
        left,
        right,
        right_financial=enriched_right,
        right_pricing_basis=(
            "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
        ),
    )

    payload = dto.to_dict()

    assert payload["api_version"] == API_VERSION

    assert (
        payload["left_offer"]["price"][
            "advertised_monthly_fee_huf"
        ]
        == 192312
    )

    assert (
        payload["right_offer"]["price"][
            "advertised_monthly_fee_huf"
        ]
        == 189990
    )

    # Important: enriched financial monthly_fee is NOT
    # mislabeled as a normalized/comparable price.
    # Only the orchestrator may provide that.
    assert (
        payload["right_offer"]["price"][
            "comparable_monthly_fee_huf"
        ]
        is None
    )

    assert (
        payload["right_offer"]["price"][
            "down_payment"
        ]["status"]
        == "OBSERVED"
    )

    assert (
        payload["right_offer"]["price"][
            "down_payment"
        ]["percent"]
        == 0.0
    )

    assert (
        payload["right_offer"]["price"][
            "pricing_basis"
        ]
        == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
    )

    assert (
        payload["left_offer"]["price"][
            "down_payment"
        ]["status"]
        == "UNKNOWN"
    )

    assert (
        payload["price_comparison_allowed"]
        is False
    )

    assert payload["price_winner"] is None

    assert (
        payload["blockers"][0]["code"]
        == "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
    )

    assert (
        payload["blockers"][0]["severity"]
        == "EVIDENCE"
    )

    # Original Ayvens composite remains untouched.
    assert (
        right.composite.offer.monthly_fee
        == 189990
    )

    assert (
        right.composite.financial.monthly_fee
        == 189990
    )

    assert (
        right.composite.financial
        .down_payment.status
        == "UNKNOWN"
    )

    print(
        "TEST PASSED - COMPARISON API CONTRACT V1 "
        "PRESERVES RAW PRICE,"
    )
    print(
        "ENRICHED FINANCIAL EVIDENCE, BLOCKERS, "
        "AND DOMAIN IMMUTABILITY."
    )


if __name__ == "__main__":
    main()
