from types import SimpleNamespace

from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResultV3,
    CommonContractCoordinateV3,
    ExplicitContractPriceV3,
)


def side(provider, fee, duration, mileage):
    offer = SimpleNamespace(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="TEST",
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url=f"https://example.test/{provider.casefold()}",
    )

    vehicle = SimpleNamespace(
        brand="BYD",
        model="ATTO 2",
        trim="TEST",
        fuel_type="PHEV",
    )

    composite = SimpleNamespace(
        provider=provider,
        offer=offer,
        vehicle=vehicle,
        financial=SimpleNamespace(
            down_payment=SimpleNamespace(
                status="UNKNOWN",
                percent=None,
                amount=None,
                evidence=SimpleNamespace(
                    status="UNKNOWN",
                    source_url=None,
                    source_text=None,
                ),
            )
        ),
        services=(),
        equipment=(),
    )

    return SimpleNamespace(
        composite=composite
    )


def main():
    left = side(
        "Arval",
        192312,
        60,
        20000,
    )
    right = side(
        "Ayvens",
        189990,
        48,
        20000,
    )

    left_price = ExplicitContractPriceV3(
        provider="Arval",
        duration=60,
        mileage=20000,
        monthly_fee=192312,
        source_url="https://example.test/arval",
        source_text="Explicit Arval 60/20000 state.",
        evidence_method="CURRENT_EXACT_OFFER",
    )

    right_price = ExplicitContractPriceV3(
        provider="Ayvens",
        duration=60,
        mileage=20000,
        monthly_fee=181000,
        source_url="https://example.test/ayvens",
        source_text="Explicit Ayvens 60/20000 state.",
        evidence_method="EXACT_OFFER_PROVIDER_API",
    )

    common = CommonContractCoordinateV3(
        duration=60,
        mileage=20000,
        left=left_price,
        right=right_price,
    )

    evidence = ContractNormalizationEvidenceResultV3(
        status="RESOLVED",
        left_provider="Arval",
        right_provider="Ayvens",
        attempted_coordinates=(
            (60, 20000),
            (48, 20000),
        ),
        left_observations=(
            left_price,
        ),
        right_observations=(
            right_price,
        ),
        common_coordinates=(
            common,
        ),
        selected_coordinate=common,
        diagnostic="Resolved explicit common state.",
    )

    result = (
        FullComparisonOrchestrator()
        .compare(
            left,
            right,
            observed_offer_pool=[
                left.composite.offer,
                right.composite.offer,
            ],
            left_variant_items=(),
            right_variant_items=(),
            left_variant_equipment_status="VALIDATED",
            right_variant_equipment_status="VALIDATED",
            left_service_package=SimpleNamespace(items=()),
            right_service_package=SimpleNamespace(items=()),
            contract_evidence=evidence,
        )
    )

    assert (
        result.contract_status
        == "EXACT_COMMON_CONTRACT_OBSERVED"
    )
    assert (
        result.normalized_monthly_fee_left
        == 192312
    )
    assert (
        result.normalized_monthly_fee_right
        == 181000
    )
    assert (
        result.contract_normalization_method
        == "EXPLICIT_COMMON_CONTRACT_STATE"
    )
    assert (
        result.contract_normalization_confidence
        == 100
    )

    blocker_codes = tuple(
        item.code
        for item in result.barriers
    )

    assert (
        "CONTRACT_NORMALIZATION_INCOMPLETE"
        not in blocker_codes
    )

    print(
        "TEST PASSED - ORCHESTRATOR CONSUMES V3 "
        "CONTRACT EVIDENCE WITHOUT DTO ADAPTER."
    )


if __name__ == "__main__":
    main()
