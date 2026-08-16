from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)


def main():

    # ========================================================
    # TEST 1 - EXPLICIT PERCENT DOWN PAYMENT
    # ========================================================

    result = ArvalAcquisitionConnector._parse_down_payment(
        "Az ajánlat 20% önerő mellett érvényes."
    )

    assert result is not None
    assert (
        result["payload"]["down_payment_percent"]
        == 20
    )

    print(
        "TEST 1 PASSED - "
        "EXPLICIT DOWN PAYMENT PERCENT PARSED"
    )

    # ========================================================
    # TEST 2 - NO SILENT 20% FROM GENERIC TEXT
    # ========================================================

    result = ArvalAcquisitionConnector._parse_down_payment(
        "Fix havi bérleti díj, teljes körű flottakezeléssel."
    )

    assert result is None

    print(
        "TEST 2 PASSED - "
        "GENERIC LEASING TEXT DOES NOT CREATE DOWN PAYMENT"
    )

    # ========================================================
    # TEST 3 - SERVICE ASSERTIONS
    # ========================================================

    services = (
        ArvalAcquisitionConnector
        ._parse_services(
            "Szerviz és karbantartás, baleset és biztosítás, "
            "szezonális gumicsere és közúti segítségnyújtás. "
            "A My Arval felületen minden információ elérhető."
        )
    )

    codes = {
        item["code"]
        for item in services
    }

    assert "MAINTENANCE" in codes
    assert "INSURANCE" in codes
    assert "TYRES" in codes
    assert "ROADSIDE_ASSISTANCE" in codes
    assert "FLEET_PORTAL" in codes

    print(
        "TEST 3 PASSED - "
        "ARVAL SERVICE ASSERTIONS PARSED"
    )

    print(
        "\nALL ARVAL ACQUISITION CONNECTOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
