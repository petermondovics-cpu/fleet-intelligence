from playwright.sync_api import sync_playwright

from scrapers.arval.composite_offer_builder import (
    ArvalCompositeOfferBuilder,
)


ARVAL_URL = (
    "https://www.arval.hu/"
    "kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def dismiss_cookies(page):
    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
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
            print(
                "Cookie overlay handled"
            )
            return
        except Exception:
            continue


def main():

    print("=" * 76)
    print(
        "ARVAL COMPOSITE OFFER LIVE INTEGRATION V1"
    )
    print("=" * 76)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print(
            "\nOpening Arval:",
            ARVAL_URL,
        )

        page.goto(
            ARVAL_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            page
        )

        builder = (
            ArvalCompositeOfferBuilder()
        )

        composite = builder.build(
            page
        )

        print(
            "\n--- COMPOSITE OFFER ---"
        )

        print(
            "Provider:",
            composite.provider,
        )

        print(
            "Brand:",
            composite.offer.brand,
        )

        print(
            "Model:",
            composite.offer.model,
        )

        print(
            "Trim:",
            composite.offer.trim,
        )

        print(
            "Fuel:",
            composite.offer.fuel_type,
        )

        print(
            "Monthly fee:",
            f"{composite.monthly_fee:,} Ft",
        )

        print(
            "Duration:",
            composite.duration,
            "months",
        )

        print(
            "Mileage:",
            f"{composite.mileage:,} km/year",
        )

        print(
            "Standard equipment:",
            composite.standard_equipment_count,
        )

        print(
            "Optional equipment:",
            composite.optional_equipment_count,
        )

        print(
            "Included services:",
            composite.included_service_count,
        )

        print(
            "Down payment known:",
            composite.down_payment_known,
        )

        assert (
            composite.provider
            == "Arval"
        )

        assert (
            composite.monthly_fee
            > 0
        )

        assert (
            composite.duration
            > 0
        )

        assert (
            composite.mileage
            > 0
        )

        assert (
            composite.included_service_count
            == 6
        )

        assert (
            composite.standard_equipment_count
            == 0
        )

        assert (
            composite.optional_equipment_count
            == 0
        )

        assert (
            composite.down_payment_known
            is False
        )

        print(
            "\nTEST 1 PASSED - "
            "LIVE ARVAL COMPOSITE OFFER BUILT"
        )

        # service evidence
        assert all(
            item.included is True
            for item in (
                composite.services.items
            )
        )

        assert all(
            item.evidence.status
            == "OBSERVED"
            for item in (
                composite.services.items
            )
        )

        print(
            "TEST 2 PASSED - "
            "ARVAL SERVICE PACKAGE OBSERVED"
        )

        # financial consistency
        assert (
            composite.financial.monthly_fee
            == composite.offer.monthly_fee
        )

        assert (
            composite.financial
            .down_payment.percent
            is None
        )

        assert (
            composite.financial
            .down_payment.amount
            is None
        )

        print(
            "TEST 3 PASSED - "
            "ARVAL FINANCIAL CONDITIONS SAFE"
        )

        print(
            "\nIMPORTANT:"
        )

        print(
            "Arval standard/optional equipment "
            "counts are 0 because the provider "
            "does not publish equipment lists."
        )

        print(
            "This is NOT evidence that the "
            "vehicle has zero equipment."
        )

        print(
            "\n"
            + "=" * 76
        )

        print(
            "ALL ARVAL COMPOSITE OFFER "
            "LIVE V1 TESTS PASSED"
        )

        print(
            "=" * 76
        )

        browser.close()


if __name__ == "__main__":
    main()
