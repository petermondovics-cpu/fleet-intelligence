from scrapers.arval.offer_route_resolver import (
    ArvalOfferRouteResolver,
)


DOUBLE = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

SINGLE = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at"
)

DISTINCT = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "peugeot/"
    "peugeot-408-hybrid-145-e-dct6-allure-5d"
)


def main():

    r = ArvalOfferRouteResolver()

    print("=" * 96)
    print("ARVAL OFFER ROUTE RESOLVER V2")
    print("=" * 96)

    candidates = r.candidates(
        DOUBLE
    )

    assert candidates == (
        DOUBLE,
        SINGLE,
    )

    print(
        "TEST 1 PASSED - PROVIDER-PUBLISHED "
        "DOUBLE ROUTE IS TRIED FIRST."
    )

    assert r.candidates(
        DISTINCT
    ) == (
        DISTINCT,
    )

    print(
        "TEST 2 PASSED - DISTINCT FINAL SEGMENTS "
        "ARE NEVER COLLAPSED."
    )

    assert (
        r._collapse_identical_final_segment(
            DOUBLE
        )
        == SINGLE
    )

    print(
        "TEST 3 PASSED - COLLAPSED ROUTE EXISTS "
        "ONLY AS A FALLBACK CANDIDATE."
    )

    print()
    print(
        "ALL ARVAL OFFER ROUTE RESOLVER V2 "
        "UNIT TESTS PASSED"
    )


if __name__ == "__main__":
    main()
