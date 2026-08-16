from types import SimpleNamespace
from api.comparison_presenter_v2 import ComparisonPresenterV2

def evidence():
    return SimpleNamespace(status="OBSERVED", source_url="https://example.test", source_text="evidence")

def financial(percent):
    return SimpleNamespace(
        down_payment=SimpleNamespace(
            status="OBSERVED",
            percent=percent,
            amount=None,
            evidence=evidence(),
        )
    )

def side(provider, fee, duration):
    composite = SimpleNamespace(
        provider=provider,
        offer=SimpleNamespace(
            duration=duration,
            mileage=20000,
            monthly_fee=fee,
            url="https://example.test/" + provider.casefold(),
        ),
        vehicle=SimpleNamespace(
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
        ),
        financial=financial(0.0),
    )
    return SimpleNamespace(composite=composite)

def main():
    result = SimpleNamespace(
        status="INSUFFICIENT_EVIDENCE",
        price_comparison_allowed=False,
        price_winner=None,
        normalized_monthly_fee_left=None,
        normalized_monthly_fee_right=None,
        vehicle_status="COMPARABLE",
        variant_status="VALUE_DIFFERENCE",
        service_status="PARTIAL_EQUIVALENCE",
        equipment_status="VALUE_DIFFERENCE",
        contract_status="EVIDENCE_UNRESOLVED",
        financial_status="INSUFFICIENT_EVIDENCE",
        barriers=(SimpleNamespace(
            code="CONTRACT_NORMALIZATION_INCOMPLETE",
            hard=False,
            message="No common exact price.",
        ),),
        contract_normalization_method="EXPLICIT_COMMON_CONTRACT_STATE",
        contract_normalization_confidence=0,
        equipment_score_left=37,
        equipment_score_right=16,
    )

    decision = SimpleNamespace(
        verdict="INSUFFICIENT_EVIDENCE",
        price_winner=None,
        price_comparison_allowed=False,
        observed_price_difference=SimpleNamespace(
            lower_provider="Ayvens",
            difference_huf=2322,
            difference_percent=1.21,
            normalized=False,
        ),
        decision_reasons=("NO_COMMON_PRICED_CONTRACT_STATE",),
        confidence=0,
        management_summary="No price winner can be declared.",
        next_best_action="Obtain one common exact priced state.",
    )

    response = ComparisonPresenterV2().present(
        result, decision,
        side("Arval", 192312, 60),
        side("Ayvens", 189990, 48),
    )
    payload = response.to_dict()

    assert payload["api_version"] == "comparison.v2"
    assert payload["decision"]["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert payload["decision"]["observed_price_difference"]["difference_huf"] == 2322
    assert payload["decision"]["observed_price_difference"]["normalized"] is False

    v1 = response.to_v1().to_dict()
    assert v1["api_version"] == "comparison.v1"
    assert v1["left_offer"]["price"]["advertised_monthly_fee_huf"] == 192312
    assert "decision" not in v1

    print("TEST PASSED - V2 ADDS DECISION DATA WHILE PRESERVING EXPLICIT V1 PROJECTION.")

if __name__ == "__main__":
    main()
