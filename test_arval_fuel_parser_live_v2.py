from playwright.sync_api import sync_playwright

from scrapers.arval.fuel_parser import (
    ArvalFuelParser,
)


CASES = [
    (
        "PHEV",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
            "byd-atto-2-15-phev-boost-at"
        ),
    ),
    (
        "EV",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/"
            "byd-sealion-7-825kwh-design-awd/"
            "byd-sealion-7-825-kwh-design-awd"
        ),
    ),
    (
        "Diesel",
        (
            "https://www.arval.hu/kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/"
            "opel-combo-cargo-15-dizel-75-kw100-le/"
            "opel-combo-cargo-15-dizel-75-kw100-le"
        ),
    ),
]


def dismiss_cookies(page):
    for selector in [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]:
        loc = page.locator(selector)

        if loc.count() == 0:
            continue

        try:
            loc.first.click(timeout=2000)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def main():

    print("=" * 72)
    print("ARVAL FUEL PARSER LIVE V2")
    print("=" * 72)

    parser = ArvalFuelParser()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        for expected, url in CASES:

            page = browser.new_page()

            try:
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                page.wait_for_timeout(1800)
                dismiss_cookies(page)

                actual = parser.parse(page)

                print(
                    f"\nExpected: {expected}"
                )
                print(
                    f"Actual:   {actual}"
                )
                print(
                    f"URL:      {url}"
                )

                assert actual == expected

                print("PASS")

            finally:
                page.close()

        browser.close()

    print(
        "\nALL ARVAL FUEL PARSER "
        "LIVE V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
