import sys

from playwright.sync_api import sync_playwright

from scrapers.ayvens.composite_offer_builder import (
    AyvensCompositeOfferBuilder,
)


DEFAULT_URL = (
    "https://autotartosberlet.ayvens.com/"
    "opel/astra"
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
            locator.first.click(timeout=2500)
            page.wait_for_timeout(500)
            print("Cookie overlay handled")
            return
        except Exception:
            continue


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    print("=" * 76)
    print("AYVENS COMPOSITE OFFER LIVE INTEGRATION V1")
    print("=" * 76)
    print("\nURL:", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(3000)
        dismiss_cookies(page)

        builder = AyvensCompositeOfferBuilder()

        composite = builder.build(page)
        capabilities = builder.parse_quote_capabilities(page)

        print("\n--- COMPOSITE OFFER ---")
        print("Provider:", composite.provider)
        print("Brand:", composite.offer.brand)
        print("Model:", composite.offer.model)
        print("Trim:", composite.offer.trim)
        print("Fuel:", composite.offer.fuel_type)
        print("Monthly fee:", f"{composite.monthly_fee:,} Ft")
        print("Duration:", composite.duration, "months")
        print("Mileage:", f"{composite.mileage:,} km/year")
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

        assert composite.provider == "Ayvens"
        assert composite.monthly_fee > 0
        assert composite.duration > 0
        assert composite.mileage > 0
        assert composite.standard_equipment_count > 0
        assert composite.optional_equipment_count > 0
        assert composite.included_service_count >= 1
        assert composite.down_payment_known is False

        print(
            "\nTEST 1 PASSED - "
            "LIVE AYVENS COMPOSITE OFFER BUILT"
        )

        # ------------------------------------------------------------
        # Equipment classification barrier
        # ------------------------------------------------------------
        assert all(
            item.standard is True
            for item in composite.vehicle.standard_equipment
        )

        assert all(
            item.standard is False
            for item in composite.vehicle.optional_equipment
        )

        assert all(
            item.evidence.status == "OBSERVED"
            for item in (
                list(composite.vehicle.standard_equipment)
                + list(composite.vehicle.optional_equipment)
            )
        )

        print(
            "TEST 2 PASSED - "
            "STANDARD/OPTIONAL EQUIPMENT PRESERVED"
        )

        # ------------------------------------------------------------
        # Financial consistency barrier
        # ------------------------------------------------------------
        assert (
            composite.financial.monthly_fee
            == composite.offer.monthly_fee
        )

        assert composite.financial.down_payment.percent is None
        assert composite.financial.down_payment.amount is None

        print(
            "TEST 3 PASSED - "
            "FINANCIAL CONDITIONS CONSISTENT"
        )

        # ------------------------------------------------------------
        # Quote controls are metadata, never Offer variants
        # ------------------------------------------------------------
        print("\n--- QUOTE CAPABILITIES (METADATA ONLY) ---")
        print(
            "Duration:",
            capabilities.duration_min,
            "->",
            capabilities.duration_max,
            "step",
            capabilities.duration_step,
        )
        print(
            "Mileage:",
            capabilities.mileage_min,
            "->",
            capabilities.mileage_max,
            "step",
            capabilities.mileage_step,
        )

        assert not hasattr(capabilities, "monthly_fee")
        assert not hasattr(composite, "quote_capabilities")

        # The CompositeOffer must still contain ONLY the advertised contract.
        assert composite.duration == composite.offer.duration
        assert composite.mileage == composite.offer.mileage
        assert composite.monthly_fee == composite.offer.monthly_fee

        print(
            "TEST 4 PASSED - "
            "QUOTE SLIDERS CANNOT CREATE PRICED OFFER VARIANTS"
        )

        print("\n--- SAMPLE STANDARD EQUIPMENT ---")
        for item in list(
            composite.vehicle.standard_equipment
        )[:5]:
            print("-", item.name)

        print("\n--- SAMPLE OPTIONAL EQUIPMENT ---")
        for item in list(
            composite.vehicle.optional_equipment
        )[:5]:
            print("-", item.name)

        print("\n" + "=" * 76)
        print(
            "ALL AYVENS COMPOSITE OFFER "
            "LIVE V1 TESTS PASSED"
        )
        print("=" * 76)

        browser.close()


if __name__ == "__main__":
    main()
