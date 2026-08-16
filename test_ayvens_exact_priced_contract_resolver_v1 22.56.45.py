from contract_normalization.ayvens_exact_priced_contract_resolver import (
    AyvensExactPricedContractResolver,
)


def main():
    r = AyvensExactPricedContractResolver

    print("=" * 92)
    print("AYVENS EXACT PRICED CONTRACT RESOLVER UNIT V1")
    print("=" * 92)

    # Explicit coordinate + explicit price is promotable.
    record = {
        "duration": 60,
        "mileage": 20000,
        "monthly_fee": 210000,
    }

    parsed = r._explicit_coordinate(
        record
    )

    assert parsed == (
        60,
        20000,
        210000,
        "monthly_fee",
    )

    print(
        "TEST 1 PASSED - EXPLICIT PRICED COORDINATE ACCEPTED."
    )

    # Capability metadata without price must never resolve.
    assert (
        r._explicit_coordinate(
            {
                "duration": 60,
                "mileage": 20000,
            }
        )
        is None
    )

    print(
        "TEST 2 PASSED - UNPRICED CONTRACT CAPABILITY REJECTED."
    )

    # A price without both coordinates must never resolve.
    assert (
        r._explicit_coordinate(
            {
                "duration": 60,
                "monthly_fee": 210000,
            }
        )
        is None
    )

    print(
        "TEST 3 PASSED - PRICE WITHOUT FULL COORDINATE REJECTED."
    )

    # URL derivation must remain exact-offer scoped.
    url = (
        r._api_url_from_offer(
            "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
        )
    )

    assert url == (
        "https://autotartosberlet.ayvens.com/"
        "api/cars/byd/atto-2-dm-i"
    )

    print(
        "TEST 4 PASSED - EXACT-OFFER API URL DERIVED."
    )

    print()
    print(
        "ALL AYVENS EXACT PRICED CONTRACT RESOLVER "
        "UNIT TESTS PASSED"
    )


if __name__ == "__main__":
    main()
