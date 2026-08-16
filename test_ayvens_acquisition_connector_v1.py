from scrapers.ayvens.acquisition_connector import (
    AyvensAcquisitionConnector,
)


def main():

    services = AyvensAcquisitionConnector._parse_services(
        "Teljes körű karbantartás. Téli-, nyári gumiabroncs. "
        "Assistance szolgáltatás. MyAyvens online ügyintézési rendszer. "
        "Vonatkozó adók. Biztosítási csomag."
    )

    codes = {x["code"] for x in services}

    expected = {
        "MAINTENANCE",
        "TYRES",
        "MOBILITY",
        "ADMINISTRATION",
        "TAXES",
        "INSURANCE",
    }

    assert expected.issubset(codes)

    print("TEST 1 PASSED - AYVENS SERVICES PARSED")

    result = AyvensAcquisitionConnector._parse_down_payment(
        "A futamidő 36-60 hónap között, az éves futás 20 000-60 000 km."
    )

    assert result is None

    print(
        "TEST 2 PASSED - QUOTE CONTROLS DO NOT CREATE DOWN PAYMENT"
    )

    result = AyvensAcquisitionConnector._parse_down_payment(
        "Az ajánlat 15% önerő mellett érvényes."
    )

    assert result is not None
    assert result["payload"]["down_payment_percent"] == 15

    print("TEST 3 PASSED - EXPLICIT DOWN PAYMENT PARSED")

    assert (
        AyvensAcquisitionConnector._clean_url(
            "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i?x=1"
        )
        ==
        "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
    )

    print("TEST 4 PASSED - URL IDENTITY NORMALIZED")

    print(
        "\nALL AYVENS ACQUISITION CONNECTOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
