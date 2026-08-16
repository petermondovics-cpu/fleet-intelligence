from playwright.sync_api import sync_playwright

from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def canonical_identity(
    brand,
    model,
    trim,
    fuel,
):
    n = (
        VehicleIdentityNormalizer()
        .normalize(
            brand,
            model,
            trim,
            fuel,
        )
    )

    return {
        "brand": n.brand,
        "model": n.model,
        "fuel_type": n.fuel_type,
        "trim": (
            trim or ""
        ).upper().strip(),
    }


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
            loc.first.click(
                timeout=1500
            )
            page.wait_for_timeout(
                200
            )
            return
        except Exception:
            pass


def main():
    print("=" * 100)
    print("AYVENS EVIDENCE-AWARE BUILDER V3 + ACTIVE MANUFACTURER FALLBACK LIVE")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            page = browser.new_page()

            page.goto(
                AYVENS_URL,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            page.wait_for_timeout(
                1500
            )
            dismiss(page)

            wrapped = (
                AyvensEvidenceAwareBuilder()
                .build(page)
            )

            page.close()

            evidence = (
                wrapped.equipment_evidence
            )

            print()
            print("--- PROVIDER PUBLICATION STATE ---")
            print(
                "Standard:",
                evidence.standard_status,
            )
            print(
                "Optional:",
                evidence.optional_status,
            )
            print(
                "Fully comparable:",
                evidence.fully_comparable,
            )

            print()
            print("--- OFFER ---")
            print(
                wrapped.composite.offer.brand,
                wrapped.composite.offer.model,
                wrapped.composite.offer.trim,
                wrapped.composite.offer.fuel_type,
            )

            assert (
                evidence.standard_status
                == "NOT_PUBLISHED"
            )
            assert (
                evidence.optional_status
                == "NOT_PUBLISHED"
            )

            manufacturer_connector = (
                BYDManufacturerEquipmentConnector(
                    browser
                )
            )

            manufacturer = (
                ManufacturerEquipmentAcquisition(
                    canonical_identity_builder=(
                        canonical_identity
                    ),
                    manufacturer_discovery=(
                        manufacturer_connector
                        .discover
                    ),
                )
            )

            result = manufacturer.acquire(
                task=None,
                offer=(
                    wrapped
                    .composite
                    .offer
                ),
                provider_equipment_status=(
                    "NOT_PUBLISHED"
                ),
            )

            print()
            print("--- MANUFACTURER FALLBACK ---")
            print(
                "Status:",
                result.status,
            )
            print(
                "Trim:",
                result.trim,
            )
            print(
                "Source:",
                result.source_url,
            )
            print(
                "Items:",
                len(result.equipment),
            )

            for item in result.equipment:
                print("-", item)

            assert (
                result.status
                == "VALIDATED"
            )
            assert (
                (result.trim or "")
                .casefold()
                == "active"
            )
            assert len(
                result.equipment
            ) > 0

            print()
            print(
                "TEST PASSED - AYVENS EXACT-OFFER API "
                "RECLASSIFIES EMPTY EQUIPMENT PUBLICATION "
                "TO NOT_PUBLISHED, THEN EXACT ACTIVE BYD "
                "MANUFACTURER EVIDENCE VALIDATES SAFELY."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
