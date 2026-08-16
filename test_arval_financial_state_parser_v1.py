from contract_normalization.arval_financial_state_observer import (
    ArvalFinancialStateObserver,
)


def main():
    parse = (
        ArvalFinancialStateObserver
        ._parse_explicit_down_payment
    )

    p = parse(
        "Havi díj 192 312 Ft / hó. "
        "Kezdő befizetés: 20%."
    )
    assert p is not None
    assert p[0] == 20.0
    assert p[1] is None

    z = parse(
        "Az ajánlat kezdő befizetés nélkül érhető el."
    )
    assert z is not None
    assert z[0] == 0.0
    assert z[1] == 0

    a = parse(
        "Önerő: 1 250 000 Ft. Futamidő 60 hónap."
    )
    assert a is not None
    assert a[0] is None
    assert a[1] == 1250000

    unknown = parse(
        "Havi díj: 192 312 Ft / hó. "
        "60 hónap, 20 000 km/év."
    )
    assert unknown is None

    print(
        "TEST PASSED - ARVAL FINANCIAL PARSER ACCEPTS "
        "ONLY EXPLICIT DOWN-PAYMENT EVIDENCE AND DOES "
        "NOT INFER A DEFAULT."
    )


if __name__ == "__main__":
    main()
