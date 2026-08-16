from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)


def observed(text="Observed source"):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com/offer",
        source_text=text,
    )


def unknown():
    return FinancialEvidence(
        status=EVIDENCE_UNKNOWN
    )


def main():

    # ========================================================
    # TEST 1 - SERVICE INCLUDED
    # ========================================================

    casco = ServiceItem(
        name="Casco biztosítás",
        category="INSURANCE",
        included=True,
        evidence=observed(
            "Casco biztosítás a havidíjban"
        ),
    )

    package = ServicePackage(
        items=[casco]
    )

    assert package.has_service(
        "INSURANCE",
        "Casco biztosítás",
    ) is True

    assert len(
        package.included()
    ) == 1

    print(
        "TEST 1 PASSED - "
        "INCLUDED SERVICE"
    )

    # ========================================================
    # TEST 2 - SERVICE EXCLUDED
    # ========================================================

    fuel_card = ServiceItem(
        name="Üzemanyagkártya",
        category="FUEL",
        included=False,
        evidence=observed(
            "Üzemanyagkártya nem része a csomagnak"
        ),
    )

    package = ServicePackage(
        items=[
            casco,
            fuel_card,
        ]
    )

    assert package.has_service(
        "FUEL",
        "Üzemanyagkártya",
    ) is False

    assert len(
        package.excluded()
    ) == 1

    print(
        "TEST 2 PASSED - "
        "EXCLUDED SERVICE"
    )

    # ========================================================
    # TEST 3 - UNKNOWN IS NOT EXCLUDED
    # ========================================================

    tyres = ServiceItem(
        name="Téli gumi",
        category="TYRES",
        included=None,
        evidence=unknown(),
    )

    package = ServicePackage(
        items=[tyres]
    )

    assert package.has_service(
        "TYRES",
        "Téli gumi",
    ) is None

    assert len(
        package.unknown()
    ) == 1

    print(
        "TEST 3 PASSED - "
        "UNKNOWN SERVICE PRESERVED"
    )

    # ========================================================
    # TEST 4 - UNKNOWN SERVICE CANNOT ASSERT FALSE
    # ========================================================

    try:
        ServiceItem(
            name="Assistance",
            category="MOBILITY",
            included=False,
            evidence=unknown(),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "UNKNOWN service incorrectly "
            "accepted as excluded."
        )

    print(
        "TEST 4 PASSED - "
        "UNKNOWN SERVICE ASSERTION REJECTED"
    )

    # ========================================================
    # TEST 5 - OBSERVED 20% DOWN PAYMENT
    # ========================================================

    down_payment = DownPayment(
        percent=20.0,
        amount=None,
        status=EVIDENCE_OBSERVED,
        evidence=observed(
            "20% önerő"
        ),
    )

    assert down_payment.percent == 20.0
    assert down_payment.amount is None

    print(
        "TEST 5 PASSED - "
        "OBSERVED 20% DOWN PAYMENT"
    )

    # ========================================================
    # TEST 6 - UNKNOWN DOWN PAYMENT
    # ========================================================

    down_payment = DownPayment(
        percent=None,
        amount=None,
        status=EVIDENCE_UNKNOWN,
        evidence=unknown(),
    )

    assert down_payment.percent is None
    assert down_payment.amount is None

    print(
        "TEST 6 PASSED - "
        "UNKNOWN DOWN PAYMENT PRESERVED"
    )

    # ========================================================
    # TEST 7 - 20% IS NOT AUTOMATICALLY ASSIGNED
    # ========================================================

    conditions = FinancialConditions(
        monthly_fee=189990,
        down_payment=down_payment,
    )

    assert (
        conditions.down_payment.percent
        is None
    )

    print(
        "TEST 7 PASSED - "
        "NO SILENT 20% ASSUMPTION"
    )

    # ========================================================
    # TEST 8 - DOWN PAYMENT RANGE VALIDATION
    # ========================================================

    try:
        DownPayment(
            percent=120.0,
            amount=None,
            status=EVIDENCE_OBSERVED,
            evidence=observed(
                "120% önerő"
            ),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Invalid down-payment percentage accepted."
        )

    print(
        "TEST 8 PASSED - "
        "DOWN PAYMENT RANGE VALIDATED"
    )

    # ========================================================
    # TEST 9 - OBSERVED DOWN PAYMENT NEEDS A VALUE
    # ========================================================

    try:
        DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_OBSERVED,
            evidence=observed(),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "OBSERVED down payment accepted "
            "without a value."
        )

    print(
        "TEST 9 PASSED - "
        "OBSERVED DOWN PAYMENT REQUIRES VALUE"
    )

    # ========================================================
    # TEST 10 - FINANCIAL CONDITIONS
    # ========================================================

    observed_down_payment = DownPayment(
        percent=20.0,
        amount=None,
        status=EVIDENCE_OBSERVED,
        evidence=observed(
            "20% önerő"
        ),
    )

    conditions = FinancialConditions(
        monthly_fee=189990,
        down_payment=observed_down_payment,
        other_one_off_fees=0,
        other_recurring_fees=0,
        monthly_fee_evidence=observed(
            "189 990 Ft/hó"
        ),
    )

    assert conditions.monthly_fee == 189990
    assert (
        conditions.down_payment.percent
        == 20.0
    )

    print(
        "TEST 10 PASSED - "
        "FINANCIAL CONDITIONS"
    )

    print(
        "\nALL SERVICE PACKAGE + "
        "DOWN PAYMENT V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
