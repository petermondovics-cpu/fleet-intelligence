from scrapers.arval.offer_route_resolver import (
    ArvalOfferRouteResolver,
)

def main():
    print("=" * 100)
    print("ARVAL OFFER ROUTE RESOLVER V2 RECOVERY TEST")
    print("=" * 100)

    double = (
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajantlat/"
        "byd-atto-2-15-phev-boost-at/"
        "byd-atto-2-15-phev-boost-at"
    )

    single = (
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajantlat/"
        "peugeot/"
        "peugeot-408-hybrid-145-e-dct6-allure-5d"
    )

    assert ArvalOfferRouteResolver.candidates(double) == (
        double,
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajantlat/"
        "byd-atto-2-15-phev-boost-at",
    )

    assert ArvalOfferRouteResolver.candidates(single) == (
        single,
    )

    print("TEST PASSED - PROVIDER-PUBLISHED DOUBLE-SLUG ROUTE REMAINS FIRST CANDIDATE.")

if __name__ == "__main__":
    main()
