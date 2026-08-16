from datetime import datetime

from contract_evidence.engine import (
    ContractEvidenceEngine,
)
from contract_normalization.engine import (
    ContractNormalizationEngine,
)
from comparison.engine import ComparisonResult
from models.offer import Offer


def create_offer(
    provider,
    fee,
    duration,
    mileage=20000,
    brand="BYD",
    model="ATTO 2",
    fuel_type="EV",
):
    return Offer(
        provider=provider,
        brand=brand,
        model=model,
        trim="",
        fuel_type=fuel_type,
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url="",
        scraped_at=datetime.now(),
    )


def create_comparison(
    offer_a,
    offer_b,
):

    comparable = (
        offer_a.duration == offer_b.duration
        and offer_a.mileage == offer_b.mileage
    )

    return ComparisonResult(
        brand=offer_a.brand,
        model=offer_a.model,
        fuel_type_a=offer_a.fuel_type,
        fuel_type_b=offer_b.fuel_type,
        vehicle_confidence=100,
        vehicle_match_type="EXACT_MATCH",
        contract_comparable=comparable,
        contract_difference="",
        duration_similarity=100,
        mileage_similarity=100,
        contract_similarity=100,
        offers=[
            offer_a,
            offer_b,
        ],
        best_provider=(
            offer_a.provider
            if offer_a.monthly_fee
            <= offer_b.monthly_fee
            else offer_b.provider
        ),
        best_monthly_fee=min(
            offer_a.monthly_fee,
            offer_b.monthly_fee,
        ),
        price_difference=abs(
            offer_a.monthly_fee
            - offer_b.monthly_fee
        ),
        annual_saving=(
            abs(
                offer_a.monthly_fee
                - offer_b.monthly_fee
            ) * 12
        ),
        price_winner=(
            offer_a.provider
            if (
                comparable
                and
                offer_a.monthly_fee
                < offer_b.monthly_fee
            )
            else (
                offer_b.provider
                if (
                    comparable
                    and
                    offer_b.monthly_fee
                    < offer_a.monthly_fee
                )
                else "NOT_COMPARABLE"
            )
        ),
        price_winner_is_valid=comparable,
        price_difference_percent=0.0,
        variant_confidence=100,
        variant_match_type="EXACT_VARIANT",
        variant_key_a="BYD|ATTO 2|EV",
        variant_key_b="BYD|ATTO 2|EV",
    )


def main():

    engine = ContractEvidenceEngine()

    # ------------------------------------------------
    # TEST 1
    # TERM EVIDENCE
    # ------------------------------------------------

    arval_48 = create_offer(
        "Arval",
        180000,
        48,
        20000,
    )

    arval_60 = create_offer(
        "Arval",
        192000,
        60,
        20000,
    )

    evidence = engine.build_evidence(
        arval_48,
        arval_60,
    )

    assert evidence is not None
    assert evidence["provider"] == "Arval"
    assert evidence["source_duration"] == 48
    assert evidence["target_duration"] == 60
    assert evidence["source_mileage"] == 20000
    assert evidence["target_mileage"] == 20000
    assert evidence["source_monthly_fee"] == 180000
    assert evidence["target_monthly_fee"] == 192000

    print(
        "TEST 1 PASSED - "
        "TERM EVIDENCE"
    )

    # ------------------------------------------------
    # TEST 2
    # MILEAGE EVIDENCE
    # ------------------------------------------------

    arval_20 = create_offer(
        "Arval",
        180000,
        48,
        20000,
    )

    arval_30 = create_offer(
        "Arval",
        195000,
        48,
        30000,
    )

    evidence = engine.build_evidence(
        arval_20,
        arval_30,
    )

    assert evidence is not None
    assert evidence["provider"] == "Arval"
    assert evidence["source_duration"] == 48
    assert evidence["target_duration"] == 48
    assert evidence["source_mileage"] == 20000
    assert evidence["target_mileage"] == 30000

    print(
        "TEST 2 PASSED - "
        "MILEAGE EVIDENCE"
    )

    # ------------------------------------------------
    # TEST 3
    # PROVIDER MISMATCH
    # ------------------------------------------------

    ayvens = create_offer(
        "Ayvens",
        190000,
        60,
        20000,
    )

    evidence = engine.build_evidence(
        arval_48,
        ayvens,
    )

    assert evidence is None

    print(
        "TEST 3 PASSED - "
        "PROVIDER MISMATCH REJECTED"
    )

    # ------------------------------------------------
    # TEST 4
    # MODEL MISMATCH
    # ------------------------------------------------

    different_model = create_offer(
        "Arval",
        195000,
        60,
        20000,
        model="ATTO 3",
    )

    evidence = engine.build_evidence(
        arval_48,
        different_model,
    )

    assert evidence is None

    print(
        "TEST 4 PASSED - "
        "MODEL MISMATCH REJECTED"
    )

    # ------------------------------------------------
    # TEST 5
    # FUEL MISMATCH
    # ------------------------------------------------

    phev = create_offer(
        "Arval",
        195000,
        60,
        20000,
        fuel_type="PHEV",
    )

    evidence = engine.build_evidence(
        arval_48,
        phev,
    )

    assert evidence is None

    print(
        "TEST 5 PASSED - "
        "FUEL MISMATCH REJECTED"
    )

    # ------------------------------------------------
    # TEST 6
    # BOTH DIMENSIONS DIFFER
    # ------------------------------------------------

    both_different = create_offer(
        "Arval",
        210000,
        60,
        30000,
    )

    evidence = engine.build_evidence(
        arval_48,
        both_different,
    )

    assert evidence is None

    print(
        "TEST 6 PASSED - "
        "TERM + MILEAGE MIX REJECTED"
    )

    # ------------------------------------------------
    # TEST 7
    # IDENTICAL CONTRACT
    # ------------------------------------------------

    identical = create_offer(
        "Arval",
        180000,
        48,
        20000,
    )

    evidence = engine.build_evidence(
        arval_48,
        identical,
    )

    assert evidence is None

    print(
        "TEST 7 PASSED - "
        "IDENTICAL CONTRACT IGNORED"
    )

    # ------------------------------------------------
    # TEST 8
    # MULTIPLE OBSERVATIONS
    # ------------------------------------------------

    offers = [
        create_offer(
            "Arval",
            180000,
            48,
            20000,
        ),
        create_offer(
            "Arval",
            185000,
            54,
            20000,
        ),
        create_offer(
            "Arval",
            192000,
            60,
            20000,
        ),
        create_offer(
            "Ayvens",
            190000,
            48,
            20000,
        ),
    ]

    results = engine.find_all(
        offers
    )

    arval_term_results = [
        item
        for item in results
        if (
            item.provider == "Arval"
            and item.evidence_type == "TERM"
        )
    ]

    assert len(
        arval_term_results
    ) == 3

    assert all(
        item.sample_size == 3
        for item in arval_term_results
    )

    print(
        "TEST 8 PASSED - "
        "MULTIPLE OBSERVATIONS"
    )

    # ------------------------------------------------
    # TEST 9
    # EVIDENCE DIRECTION
    # ------------------------------------------------

    evidence = engine.build_evidence(
        arval_60,
        arval_48,
    )

    assert evidence is not None
    assert evidence["source_duration"] == 60
    assert evidence["target_duration"] == 48
    assert evidence["source_monthly_fee"] == 192000
    assert evidence["target_monthly_fee"] == 180000

    print(
        "TEST 9 PASSED - "
        "EVIDENCE DIRECTION"
    )

    # ------------------------------------------------
    # TEST 10
    # V4 NORMALIZATION COMPATIBILITY
    # ------------------------------------------------

    normalization_engine = (
        ContractNormalizationEngine()
    )

    comparison = create_comparison(
        arval_48,
        arval_60,
    )

    evidence = engine.build_evidence(
        arval_48,
        arval_60,
    )

    result = (
        normalization_engine
        .normalize_with_evidence(
            comparison,
            {
                "term_evidence": evidence,
            },
        )
    )

    assert (
        result.normalization_status
        == "NORMALIZATION_ESTIMATED"
    )

    assert (
        result.normalized_price_available
        is True
    )

    assert (
        result.term_normalization_available
        is True
    )

    print(
        "TEST 10 PASSED - "
        "V4 NORMALIZATION COMPATIBILITY"
    )

    print(
        "\nALL CONTRACT EVIDENCE V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
