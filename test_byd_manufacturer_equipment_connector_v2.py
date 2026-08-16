from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)


def main():
    text = """
Choose a version
Active
£ 26 995
Premium Active Black Cloth interior
Reversing Camera with Rear Parking Sensors
Automatic LED headlights & Rain-Sensing Front Wipers
12.8” Infotainment Touchscreen & 8.8” Driver’s Display
Boost
£ 29 995
Active Specification +
High-quality vegan leather interior
Panoramic roof with electric sunshade
360◦ Camera with Front & Rear Parking Sensors
Heated Front Seats & Heated Steering Wheel
Smartphone Wireless Charging
Aluminium Roof Rail & Rear Privacy Glass
Paint
Midnight Blue
Included
Explore exterior details
"""

    parsed = (
        BYDManufacturerEquipmentConnector
        ._parse_configurator_variants(text)
    )

    boost = parsed["BOOST"]

    assert "Panoramic roof with electric sunshade" in boost
    assert "Aluminium Roof Rail & Rear Privacy Glass" in boost

    assert "Midnight Blue" not in boost
    assert "Included" not in boost
    assert "Explore exterior details" not in boost

    print(
        "TEST 1 PASSED - BOOST EQUIPMENT BLOCK STOPS "
        "BEFORE PAINT/CONFIGURATOR NOISE"
    )

    assert (
        "Premium Active Black Cloth interior"
        in boost
    )

    print(
        "TEST 2 PASSED - BOOST STILL INHERITS ACTIVE SPECIFICATION"
    )

    print(
        "\\nALL BYD MANUFACTURER EQUIPMENT CONNECTOR V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
