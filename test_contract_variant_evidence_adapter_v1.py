from contract_normalization.ayvens_contract_variant_observer import (
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
            provider="Ayvens",
            source_url="https://example.test/ayvens",
            observations=(
                ObservedContractPrice(
                    duration=48,
                    mileage=20000,
                    monthly_fee=189990,
                    source_text="48 month observed",
                ),
                ObservedContractPrice(
                    duration=60,
                    mileage=20000,
                    monthly_fee=179990,
                    source_text="60 month observed",
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
            source_duration=48,
            target_duration=60,
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
        payload[
            "provider"
        ]
        == "Ayvens"
    )

    assert (
        payload[
            "source_monthly_fee"
        ]
        == 189990
    )

    assert (
        payload[
            "target_monthly_fee"
        ]
        == 179990
    )

    assert (
        payload[
            "sample_size"
        ]
        == 1
    )

    print(
        "TEST PASSED - CONTRACT VARIANT EVIDENCE ADAPTER "
        "PROMOTES ONLY DIRECTLY OBSERVED SOURCE + TARGET "
        "CONTRACT STATES INTO NORMALIZATION EVIDENCE."
    )


if __name__ == "__main__":
    main()
