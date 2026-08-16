from contract_normalization.arval_financial_state_observer import (
    FinancialStateObservationResult,
    ObservedFinancialState,
)
from contract_normalization.arval_financial_evidence_adapter import (
    ArvalFinancialEvidenceAdapter,
)


def main():
    adapter = ArvalFinancialEvidenceAdapter()

    observed = FinancialStateObservationResult(
        status="OBSERVED",
        provider="Arval",
        source_url="https://example.test/arval",
        states=(
            ObservedFinancialState(
                monthly_fee=192312,
                down_payment_percent=20.0,
                down_payment_amount_huf=None,
                duration=60,
                mileage=20000,
                source_text="Kezdő befizetés: 20%.",
            ),
        ),
        diagnostic="ok",
    )

    evidence = adapter.build(observed)

    assert evidence is not None
    assert evidence.down_payment_percent == 20.0
    assert evidence.monthly_fee == 192312
    assert evidence.applicability_scope == "EXACT_OFFER"

    payload = adapter.to_candidate_payload(evidence)

    assert payload["down_payment_percent"] == 20.0
    assert payload["monthly_fee"] == 192312
    assert (
        payload["pricing_basis"]
        == "OBSERVED_DOWN_PAYMENT_PERCENT_STATE"
    )

    unresolved = FinancialStateObservationResult(
        status="UNRESOLVED",
        provider="Arval",
        source_url="https://example.test/arval",
        states=(),
        diagnostic="No explicit DP.",
    )

    assert adapter.build(unresolved) is None

    print(
        "TEST PASSED - ARVAL FINANCIAL EVIDENCE ADAPTER "
        "PROMOTES ONLY EXPLICIT EXACT-OFFER FINANCIAL EVIDENCE."
    )


if __name__ == "__main__":
    main()
