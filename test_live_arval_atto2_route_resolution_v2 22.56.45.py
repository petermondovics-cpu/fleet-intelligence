from playwright.sync_api import sync_playwright

from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
)


DOUBLE = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 100)
    print("LIVE ARVAL ATTO 2 ROUTE RESOLUTION V2")
    print("=" * 100)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            result = (
                ArvalOfferRouteResolver()
                .resolve(
                    page,
                    DOUBLE,
                )
            )

            print()
            print(
                "Status:",
                result.status,
            )
            print(
                "Requested:",
                result.requested_url,
            )
            print(
                "Candidates:",
                result.candidates,
            )
            print(
                "Resolved:",
                result.resolved_url,
            )
            print(
                "Diagnostic:",
                result.diagnostic,
            )

            assert (
                result.status
                == ROUTE_LIVE
            )

            assert (
                result.resolved_url
                == DOUBLE
            )

            body = (
                page.locator(
                    "body"
                )
                .inner_text()
            )

            print(
                "Contains 192312:",
                "192312"
                in body.replace(
                    " ",
                    "",
                ),
            )

            print()
            print(
                "TEST PASSED - LIVE ARVAL ATTO 2 "
                "PROVES THE PROVIDER-PUBLISHED DOUBLE-SLUG "
                "ROUTE IS THE VALID EXACT-OFFER ROUTE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
