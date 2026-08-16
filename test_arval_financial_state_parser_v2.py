from contract_normalization.arval_financial_state_observer import (
    ArvalFinancialStateObserver,
)


def main():
    parse_fee = (
        ArvalFinancialStateObserver
        ._parse_monthly_fee
    )

    body = (
        "BYD ATTO 2 1.5 PHEV BOOST AT "
        "192312 FT +ÁFA / hónap "
        "Időtartam60 hónap "
        "Futásteljesítmény 20000 km/év"
    )

    assert parse_fee(body) == 192312

    assert (
        ArvalFinancialStateObserver
        ._parse_duration(body)
        == 60
    )

    assert (
        ArvalFinancialStateObserver
        ._parse_mileage(body)
        == 20000
    )

    parse_dp = (
        ArvalFinancialStateObserver
        ._parse_explicit_down_payment
    )

    assert parse_dp(body) is None

    p = parse_dp(
        "Kezdő befizetés: 20%."
    )
    assert p is not None
    assert p[0] == 20.0

    z = parse_dp(
        "Az ajánlat kezdő befizetés nélkül érhető el."
    )
    assert z is not None
    assert z[0] == 0.0

    print(
        "TEST PASSED - ARVAL V2 PARSER READS LIVE "
        "'FT +ÁFA / hónap' PRICE + CONTRACT FORMAT "
        "WITHOUT INVENTING DOWN-PAYMENT EVIDENCE."
    )


if __name__ == "__main__":
    main()
