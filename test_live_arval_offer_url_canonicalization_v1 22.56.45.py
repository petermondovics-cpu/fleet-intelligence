from playwright.sync_api import sync_playwright

from scrapers.arval.offer_url_canonicalizer import (
    ArvalOfferUrlCanonicalizer,
)


DUPLICATED = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 100)
    print("LIVE ARVAL OFFER URL CANONICALIZATION V1")
    print("=" * 100)

    canonicalizer = (
        ArvalOfferUrlCanonicalizer()
    )

    result = (
        canonicalizer.canonicalize(
            DUPLICATED
        )
    )

    print()
    print(
        "Original:",
        result.original_url,
    )
    print(
        "Canonical:",
        result.canonical_url,
    )
    print(
        "Changed:",
        result.changed,
    )
    print(
        "Reason:",
        result.reason,
    )

    assert result.changed is True

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            response = page.goto(
                result.canonical_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                1800
            )

            status = (
                response.status
                if response is not None
                else None
            )

            print()
            print(
                "HTTP:",
                status,
            )
            print(
                "Final URL:",
                page.url,
            )

            body = (
                page.locator("body")
                .inner_text()
            )

            print(
                "Contains BYD ATTO 2:",
                "byd atto 2"
                in body.casefold(),
            )
            print(
                "Contains 192312:",
                "192312"
                in body.replace(
                    " ",
                    "",
                ),
            )

            # A provider may temporarily fail, so the live test does not
            # fabricate success. It only rejects the known duplicated URL.
            assert (
                result.canonical_url
                != result.original_url
            )

            if status == 200:
                print()
                print(
                    "GREEN - CANONICAL URL IS LIVE."
                )
            else:
                print()
                print(
                    "CANONICAL URL DID NOT RETURN HTTP 200 "
                    "IN THIS SESSION; KEEP LIVE STATE "
                    "SEPARATE FROM URL CANONICALIZATION."
                )

            print()
            print(
                "TEST PASSED - DUPLICATED ARVAL "
                "OFFER SLUG IS REMOVED BEFORE LIVE "
                "REVISIT."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
