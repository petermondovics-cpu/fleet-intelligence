from playwright.sync_api import sync_playwright

from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper
from models.contract_variant import (
    ContractVariant,
    DEFAULT_CONTRACT_VARIANTS,
)


ARVAL_TEST_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_TEST_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def test_scraper(
    scraper,
    url,
    provider,
):

    print(
        "\n"
        + "=" * 72
    )

    print(
        f"{provider} CONTRACT SELECTOR LIVE TEST"
    )

    print(
        "=" * 72
    )

    variants = DEFAULT_CONTRACT_VARIANTS

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        passed = 0
        rejected = 0

        for variant in variants:

            print(
                "\n"
                + "-" * 72
            )

            print(
                f"REQUESTED: "
                f"{variant.duration} hó / "
                f"{variant.mileage:,} km"
            )

            try:

                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )

                page.wait_for_timeout(1500)

                scraper.select_contract_variant(
                    page,
                    variant,
                )

                page.wait_for_timeout(1000)

                # Use the provider's actual parser to
                # verify what the page now displays.
                if provider == "Arval":

                    from scrapers.arval.parser import (
                        ArvalParser,
                    )

                    parser = ArvalParser()

                    observed_duration = (
                        parser.parse_duration(
                            page
                        )
                    )

                    observed_mileage = (
                        parser.parse_mileage(
                            page
                        )
                    )

                    monthly_fee = (
                        parser.parse_monthly_fee(
                            page
                        )
                    )

                else:

                    from scrapers.ayvens.parser import (
                        AyvensParser,
                    )

                    parser = AyvensParser()

                    observed_duration = (
                        parser.parse_duration(
                            page
                        )
                    )

                    observed_mileage = (
                        parser.parse_mileage(
                            page
                        )
                    )

                    monthly_fee = (
                        parser.parse_monthly_fee(
                            page
                        )
                    )

                print(
                    f"OBSERVED: "
                    f"{observed_duration} hó / "
                    f"{observed_mileage:,} km"
                )

                print(
                    f"PRICE: "
                    f"{monthly_fee:,} Ft"
                )

                if (
                    observed_duration
                    != variant.duration
                    or
                    observed_mileage
                    != variant.mileage
                ):

                    print(
                        "STATUS: REJECTED"
                    )

                    print(
                        "Reason: requested contract "
                        "was not actually selected."
                    )

                    rejected += 1

                    continue

                assert (
                    monthly_fee > 0
                )

                print(
                    "STATUS: PASS"
                )

                passed += 1

            except Exception as exc:

                print(
                    "STATUS: REJECTED"
                )

                print(
                    f"Reason: {exc}"
                )

                rejected += 1

        browser.close()

    print(
        "\n"
        + "=" * 72
    )

    print(
        f"{provider} SUMMARY"
    )

    print(
        "=" * 72
    )

    print(
        f"Passed:   {passed}"
    )

    print(
        f"Rejected: {rejected}"
    )

    print(
        f"Total:    {len(variants)}"
    )

    return passed, rejected


def main():

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FLEETIQ CONTRACT SELECTOR LIVE TEST V1"
    )

    print(
        "=" * 72
    )

    arval = ArvalScraper()

    ayvens = AyvensScraper()

    arval_passed, arval_rejected = (
        test_scraper(
            arval,
            ARVAL_TEST_URL,
            "Arval",
        )
    )

    ayvens_passed, ayvens_rejected = (
        test_scraper(
            ayvens,
            AYVENS_TEST_URL,
            "Ayvens",
        )
    )

    total_passed = (
        arval_passed
        + ayvens_passed
    )

    total_rejected = (
        arval_rejected
        + ayvens_rejected
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FINAL RESULT"
    )

    print(
        "=" * 72
    )

    print(
        f"Passed:   {total_passed}"
    )

    print(
        f"Rejected: {total_rejected}"
    )

    print(
        f"Total:    "
        f"{total_passed + total_rejected}"
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "A rejected variant is NOT a test failure "
        "by itself. It means the website did not "
        "allow the requested contract configuration "
        "to be selected with the current selector."
    )


if __name__ == "__main__":
    main()
