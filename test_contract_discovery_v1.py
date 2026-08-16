from playwright.sync_api import sync_playwright

from models.contract_discovery import (
    ContractDiscoveryEngine,
)
from scrapers.arval.cookies import accept_cookies


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


def handle_cookies(
    page,
    provider,
):
    if provider == "Arval":
        try:
            accept_cookies(page)
        except Exception:
            pass

    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elutasítom')",
        "button:has-text('Elfogadom')",
    ]

    for selector in selectors:

        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(
                timeout=2500
            )
            page.wait_for_timeout(500)
            return
        except Exception:
            continue


def run_test(
    provider,
    url,
):
    print(
        "\n"
        + "=" * 72
    )

    print(
        f"{provider} CONTRACT DISCOVERY V1"
    )

    print(
        "=" * 72
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(2000)

        handle_cookies(
            page,
            provider,
        )

        engine = ContractDiscoveryEngine()

        durations = (
            engine.discover_durations(
                page
            )
        )

        mileages = (
            engine.discover_mileages(
                page
            )
        )

        contracts = (
            engine.discover(
                page
            )
        )

        print(
            f"Durations discovered: "
            f"{durations}"
        )

        print(
            f"Mileages discovered: "
            f"{mileages}"
        )

        print(
            "Contract combinations:"
        )

        for contract in contracts:

            print(
                f"  - "
                f"{contract.duration} hó / "
                f"{contract.mileage:,} km"
            )

        assert all(
            12 <= duration <= 84
            for duration in durations
        )

        assert all(
            5000 <= mileage <= 100000
            for mileage in mileages
        )

        browser.close()

        return (
            durations,
            mileages,
            contracts,
        )


def main():

    arval = run_test(
        "Arval",
        ARVAL_TEST_URL,
    )

    ayvens = run_test(
        "Ayvens",
        AYVENS_TEST_URL,
    )

    print(
        "\n"
        + "=" * 72
    )

    print(
        "FINAL DISCOVERY RESULT"
    )

    print(
        "=" * 72
    )

    print(
        "TEST PASSED - "
        "CONTRACT DISCOVERY COMPLETED"
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "Discovery reports values visible on the "
        "actual page. It does not assume a fixed "
        "48/60 x 20k/30k matrix."
    )


if __name__ == "__main__":
    main()
