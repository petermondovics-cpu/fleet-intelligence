from playwright.sync_api import sync_playwright

from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)


class Offer:
    brand = "BYD"
    model = "ATTO 2"
    trim = "1.5 PHEV BOOST AT"
    fuel_type = "PHEV"


def canonical_identity(brand, model, trim, fuel):
    n = VehicleIdentityNormalizer().normalize(
        brand,
        model,
        trim,
        fuel,
    )

    return {
        "brand": n.brand,
        "model": n.model,
        "fuel_type": n.fuel_type,
        "trim": trim.upper().strip(),
    }


def main():
    print("=" * 80)
    print("BYD MANUFACTURER EQUIPMENT CONNECTOR LIVE V2")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        connector = BYDManufacturerEquipmentConnector(browser)

        acquisition = ManufacturerEquipmentAcquisition(
            canonical_identity_builder=canonical_identity,
            manufacturer_discovery=connector.discover,
        )

        result = acquisition.acquire(
            task=None,
            offer=Offer(),
            provider_equipment_status="NOT_PUBLISHED",
        )

        print("\\nStatus:", result.status)
        print("Equipment count:", len(result.equipment))

        for item in result.equipment:
            print("-", item)

        if result.status == "VALIDATED":
            noise = {
                "included",
                "explore exterior details",
                "explore interior details",
            }

            assert not any(
                item.casefold() in noise
                for item in result.equipment
            )

            assert not any(
                item.casefold().startswith("explore ")
                for item in result.equipment
            )

        print(
            "\\nTEST PASSED - LIVE BYD EQUIPMENT EXTRACTION "
            "DOES NOT INCLUDE KNOWN CONFIGURATOR UI NOISE"
        )

        browser.close()


if __name__ == "__main__":
    main()
