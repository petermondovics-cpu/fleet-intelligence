from contract_normalization.arval_contract_variant_observer import (
    ContractVariantObservationResult,
    ObservedContractPrice,
)
from contract_normalization.contract_variant_evidence_adapter import (
    ContractVariantEvidenceAdapter,
)


def main():

    observation = (
        ContractVariantObservationResult(
            status="OBSERVED",
            provider="Arval",
            source_url="https://example.test/arval",
            observations=(
                ObservedContractPrice(
                    duration=60,
                    mileage=20000,
                    monthly_fee=192312,
                    source_text="60 month observed",
                ),
                ObservedContractPrice(
                    duration=48,
                    mileage=20000,
                    monthly_fee=205000,
                    source_text="48 month observed",
                ),
            ),
            diagnostic="ok",
        )
    )

    adapter = (
        ContractVariantEvidenceAdapter()
    )

    evidence = (
        adapter
        .build_duration_evidence(
            observation,
            source_duration=60,
            target_duration=48,
            mileage=20000,
        )
    )

    assert evidence is not None

    payload = (
        adapter
        .to_normalizer_dict(
            evidence
        )
    )

    assert (
        payload["provider"]
        == "Arval"
    )

    assert (
        payload["source_monthly_fee"]
        == 192312
    )

    assert (
        payload["target_monthly_fee"]
        == 205000
    )

    assert (
        payload["sample_size"]
        == 1
    )

    print(
        "TEST PASSED - EXISTING CONTRACT VARIANT EVIDENCE "
        "ADAPTER ACCEPTS DIRECTLY OBSERVED ARVAL SOURCE + "
        "TARGET CONTRACT STATES."
    )


if __name__ == "__main__":
    main()
