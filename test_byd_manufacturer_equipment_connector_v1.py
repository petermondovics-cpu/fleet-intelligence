from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)


def main():
    text = """
Choose a version
Active
£ 26 995
● Up to 577 miles combined range (fuel & battery)
● Premium Active Black Cloth interior
● Reversing Camera with Rear Parking Sensors
● Automatic LED headlights & Rain-Sensing Front Wipers
● 12.8” Infotainment Touchscreen & 8.8” Driver’s Display
Boost
£ 29 995
Active Specification +
● Up to 621 miles combined range (fuel & battery)
● High-quality vegan leather interior
● Panoramic roof with electric sunshade
● 360◦ Camera with Front & Rear Parking Sensors
● Heated Front Seats & Heated Steering Wheel
● Smartphone Wireless Charging
"""

    parsed = (
        BYDManufacturerEquipmentConnector
        ._parse_configurator_variants(
            text
        )
    )

    assert (
        "Premium Active Black Cloth interior"
        in parsed["ACTIVE"]
    )

    assert (
        "Panoramic roof with electric sunshade"
        in parsed["BOOST"]
    )

    assert (
        "Premium Active Black Cloth interior"
        in parsed["BOOST"]
    )

    assert not any(
        "miles combined range"
        in x.casefold()
        for x in parsed["BOOST"]
    )

    print(
        "TEST 1 PASSED - ACTIVE/BOOST EQUIPMENT MATRIX PARSED"
    )

    assert (
        BYDManufacturerEquipmentConnector
        ._target_variant(
            "1.5 PHEV BOOST AT"
        )
        == "BOOST"
    )

    assert (
        BYDManufacturerEquipmentConnector
        ._target_variant(
            "Active 166 HP"
        )
        == "ACTIVE"
    )

    print(
        "TEST 2 PASSED - PROVIDER TRIMS MAP TO OFFICIAL BYD VARIANTS"
    )

    assert (
        BYDManufacturerEquipmentConnector
        ._official(
            "https://www.byd.com/uk/configurator/atto-2-dm-i"
        )
    )

    assert not (
        BYDManufacturerEquipmentConnector
        ._official(
            "https://random-cars.example/atto-2"
        )
    )

    print(
        "TEST 3 PASSED - OFFICIAL SOURCE DOMAIN ENFORCED"
    )

    print(
        "\nALL BYD MANUFACTURER EQUIPMENT CONNECTOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
