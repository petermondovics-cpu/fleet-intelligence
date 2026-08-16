from playwright.sync_api import sync_playwright

from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from scrapers.ayvens.equipment_publication_resolver import (
    AyvensEquipmentPublicationResolver,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)
        if not loc.count():
            continue
        try:
            loc.first.click(timeout=1500)
            page.wait_for_timeout(200)
            return
        except Exception:
            pass


def main():
    print("=" * 100)
    print("AYVENS EQUIPMENT PUBLICATION FALLBACK DIAGNOSTIC V2")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        try:
            page = browser.new_page()
            page.goto(
                AYVENS_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1500)
            dismiss(page)

            builder = AyvensEvidenceAwareBuilder()

            composite = (
                builder.composite_builder.build(page)
            )

            standard = (
                builder.composite_builder
                .equipment
                .parse_standard_equipment(page)
            )

            optional = (
                builder.composite_builder
                .equipment
                .parse_optional_equipment(page)
            )

            print()
            print("--- RAW DOM PARSER ---")
            print("Standard:", standard.status)
            print("Standard diagnostic:", getattr(standard, "diagnostic", None))
            print("Optional:", optional.status)
            print("Optional diagnostic:", getattr(optional, "diagnostic", None))

            print()
            print("--- OFFER IDENTITY ---")
            offer = composite.offer
            print("URL:", offer.url)
            print("Brand:", offer.brand)
            print("Model:", offer.model)
            print("Trim:", offer.trim)
            print("Fuel:", offer.fuel_type)

            resolver = AyvensEquipmentPublicationResolver()

            print()
            print("--- DERIVED API URL ---")
            print(
                resolver._api_url_from_offer(
                    offer.url
                )
            )

            print()
            print("--- DIRECT PUBLICATION RESOLUTION ---")
            resolution = resolver.resolve(
                page,
                offer,
            )
            print("Status:", resolution.status)
            print("Source:", resolution.source_url)
            print("Standard count:", resolution.standard_count)
            print("Optional count:", resolution.optional_count)
            print("Diagnostic:", resolution.diagnostic)

            print()
            print("--- BUILDER FINAL RESULT ---")
            wrapped = (
                AyvensEvidenceAwareBuilder()
                .build(page)
            )

            print(
                "Standard:",
                wrapped.equipment_evidence.standard_status,
            )
            print(
                "Optional:",
                wrapped.equipment_evidence.optional_status,
            )
            print(
                "Fully comparable:",
                wrapped.equipment_evidence.fully_comparable,
            )

            print()
            print("=" * 100)
            print(
                "DIAGNOSTIC COMPLETE - NO EQUIPMENT OR "
                "PUBLICATION STATE WAS FABRICATED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
