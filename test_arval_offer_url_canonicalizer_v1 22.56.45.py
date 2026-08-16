from scrapers.arval.offer_url_canonicalizer import (
    ArvalOfferUrlCanonicalizer,
)


DUPLICATED = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

EXPECTED = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    engine = (
        ArvalOfferUrlCanonicalizer()
    )

    print("=" * 96)
    print("ARVAL OFFER URL CANONICALIZER V1")
    print("=" * 96)

    result = engine.canonicalize(
        DUPLICATED
    )

    assert result.changed is True
    assert (
        result.canonical_url
        == EXPECTED
    )

    print(
        "TEST 1 PASSED - IDENTICAL FINAL OFFER "
        "SLUG IS COLLAPSED."
    )

    distinct = (
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajandlat/"
        "peugeot/"
        "peugeot-408-hybrid-145-e-dct6-allure-5d"
    )

    result = engine.canonicalize(
        distinct
    )

    assert result.changed is False
    assert (
        result.canonical_url
        == distinct
    )

    print(
        "TEST 2 PASSED - DISTINCT BRAND/MODEL "
        "PATH SEGMENTS ARE PRESERVED."
    )

    query = (
        DUPLICATED
        + "?campaign=test#offer"
    )

    result = engine.canonicalize(
        query
    )

    assert result.canonical_url == (
        EXPECTED
        + "?campaign=test#offer"
    )

    print(
        "TEST 3 PASSED - QUERY STRING AND "
        "FRAGMENT ARE PRESERVED."
    )

    non_arval = (
        "https://example.com/"
        "tartos-berleti-ajandlat/x/x"
    )

    result = engine.canonicalize(
        non_arval
    )

    assert result.changed is False

    print(
        "TEST 4 PASSED - NON-ARVAL URL IS "
        "NEVER MODIFIED."
    )

    non_offer = (
        "https://www.arval.hu/x/x"
    )

    result = engine.canonicalize(
        non_offer
    )

    assert result.changed is False

    print(
        "TEST 5 PASSED - NON-OFFER ARVAL PATH "
        "IS NEVER MODIFIED."
    )

    print()
    print(
        "ALL ARVAL OFFER URL CANONICALIZER "
        "V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
