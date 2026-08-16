from types import SimpleNamespace
from comparison.comparison_decision_explainer_v1 import ComparisonDecisionExplainerV1, INSUFFICIENT_EVIDENCE

def side(provider, fee, duration, mileage):
    offer = SimpleNamespace(provider=provider, monthly_fee=fee, duration=duration, mileage=mileage)
    return SimpleNamespace(provider=provider, composite=SimpleNamespace(offer=offer))

def main():
    print("=" * 100)
    print("COMPARISON DECISION EXPLAINER V1 UNIT TEST")
    print("=" * 100)
    final = SimpleNamespace(
        price_comparison_allowed=False, price_winner=None,
        contract_normalization_confidence=0,
        barriers=(
            SimpleNamespace(code="VEHICLE_VARIANT_DIFFERENCE"),
            SimpleNamespace(code="VARIANT_EQUIPMENT_VALUE_DIFFERENCE"),
            SimpleNamespace(code="EQUIPMENT_VALUE_DIFFERENCE"),
            SimpleNamespace(code="SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE"),
            SimpleNamespace(code="CONTRACT_NORMALIZATION_INCOMPLETE"),
            SimpleNamespace(code="DOWN_PAYMENT_EVIDENCE_INCOMPLETE"),
        ),
    )
    result = ComparisonDecisionExplainerV1().explain(
        final, side("Arval", 192312, 60, 20000), side("Ayvens", 189990, 48, 20000)
    )
    assert result.verdict == INSUFFICIENT_EVIDENCE
    assert result.price_winner is None
    assert result.observed_price_difference.lower_provider == "Ayvens"
    assert result.observed_price_difference.difference_huf == 2322
    assert result.observed_price_difference.normalized is False
    assert "NO_COMMON_PRICED_CONTRACT_STATE" in result.decision_reasons
    assert "Ayvens" in result.next_best_action and "60 months" in result.next_best_action
    assert "Arval" in result.next_best_action and "48 months" in result.next_best_action
    assert "no price winner can be declared" in result.management_summary
    print("Verdict:", result.verdict)
    print("Observed difference:", result.observed_price_difference)
    print("Next best action:", result.next_best_action)
    print("Summary:", result.management_summary)
    print()
    print("TEST PASSED - NOMINAL DIFFERENCE IS EXPOSED WITHOUT FABRICATING A NORMALIZED ADVANTAGE.")

if __name__ == "__main__":
    main()
