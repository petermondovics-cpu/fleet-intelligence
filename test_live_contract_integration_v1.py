from playwright.sync_api import sync_playwright

from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper


ARVAL_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def run_arval(page):
    print("\n" + "=" * 72)
    print("ARVAL LIVE INTEGRATION TEST")
    print("=" * 72)

    scraper = ArvalScraper()

    offers = scraper.collect_offer(
        page,
        ARVAL_URL,
    )

    print(
        f"\nArval validated offers: "
        f"{len(offers)}"
    )

    assert len(offers) >= 1

    for offer in offers:

        print(
            f"  PASS: "
            f"{offer.duration} hó / "
            f"{offer.mileage:,} km / "
            f"{offer.monthly_fee:,} Ft"
        )

        assert offer.duration > 0
        assert offer.mileage > 0
        assert offer.monthly_fee > 0
        assert offer.provider == "Arval"

    print(
        "TEST 1 PASSED - "
        "ARVAL LIVE CONTRACT COLLECTION"
    )


def run_ayvens(page):
    print("\n" + "=" * 72)
    print("AYVENS LIVE INTEGRATION TEST")
    print("=" * 72)

    scraper = AyvensScraper()

    offers = scraper.collect_offer(
        page,
        AYVENS_URL,
    )

    print(
        f"\nAyvens validated offers: "
        f"{len(offers)}"
    )

    assert len(offers) >= 1

    for offer in offers:

        print(
            f"  PASS: "
            f"{offer.duration} hó / "
            f"{offer.mileage:,} km / "
            f"{offer.monthly_fee:,} Ft"
        )

        assert offer.duration > 0
        assert offer.mileage > 0
        assert offer.monthly_fee > 0
        assert offer.provider == "Ayvens"

    print(
        "TEST 2 PASSED - "
        "AYVENS LIVE CONTRACT COLLECTION"
    )


def main():

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FLEETIQ LIVE CONTRACT INTEGRATION V1"
    )

    print(
        "=" * 72
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        try:
            run_arval(page)
        except Exception as exc:
            print(
                "\n❌ ARVAL LIVE TEST FAILED"
            )
            print(exc)
            raise

        try:
            run_ayvens(page)
        except Exception as exc:
            print(
                "\n❌ AYVENS LIVE TEST FAILED"
            )
            print(exc)
            raise

        browser.close()

    print(
        "\n"
        + "=" * 72
    )

    print(
        "ALL LIVE CONTRACT INTEGRATION V1 "
        "TESTS PASSED"
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    main()
