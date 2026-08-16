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


def canonical_identity(
    brand,
    model,
    trim,
    fuel,
):
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
    print("BYD MANUFACTURER EQUIPMENT CONNECTOR LIVE V1")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        connector = (
            BYDManufacturerEquipmentConnector(
                browser
            )
        )

        acquisition = (
            ManufacturerEquipmentAcquisition(
                canonical_identity_builder=canonical_identity,
                manufacturer_discovery=connector.discover,
            )
        )

        result = acquisition.acquire(
            task=None,
            offer=Offer(),
            provider_equipment_status="NOT_PUBLISHED",
        )

        print(
            "\nProvider equipment:",
            result.provider_equipment_status,
        )

        print(
            "Manufacturer equipment:",
            result.manufacturer_equipment_status,
        )

        print(
            "Status:",
            result.status,
        )

        print(
            "Source type:",
            result.source_type,
        )

        print(
            "Source URL:",
            result.source_url,
        )

        print(
            "Equipment count:",
            len(result.equipment),
        )

        for item in result.equipment[:15]:
            print("-", item)

        assert (
            result.provider_equipment_status
            == "NOT_PUBLISHED"
        )

        assert result.status in {
            "VALIDATED",
            "UNRESOLVED",
        }

        if result.status == "VALIDATED":
            assert (
                result.manufacturer_equipment_status
                == "VALIDATED"
            )
            assert len(result.equipment) > 0
            assert (
                result.source_type
                in {
                    "MANUFACTURER_MODEL_PAGE",
                    "MANUFACTURER_SPECIFICATION",
                }
            )

        print(
            "\nTEST PASSED - OFFICIAL BYD MANUFACTURER "
            "CONNECTOR RAN WITHOUT CONVERTING MANUFACTURER "
            "EVIDENCE INTO PROVIDER-PUBLISHED EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
