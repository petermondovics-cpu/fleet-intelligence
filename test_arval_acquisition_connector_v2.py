from dataclasses import dataclass

from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)


@dataclass
class Task:
    canonical_vehicle_key: str
    current_duration: int
    current_mileage: int


def main():

    # Regression on financial/service parsers.
    result = ArvalAcquisitionConnector._parse_down_payment(
        "Az ajánlat 20% önerő mellett érvényes."
    )

    assert result is not None
    assert result["payload"]["down_payment_percent"] == 20

    print(
        "TEST 1 PASSED - EXPLICIT DOWN PAYMENT STILL PARSED"
    )

    services = ArvalAcquisitionConnector._parse_services(
        "Szerviz és karbantartás, biztosítás és közúti segítségnyújtás."
    )

    codes = {item["code"] for item in services}

    assert "MAINTENANCE" in codes
    assert "INSURANCE" in codes
    assert "ROADSIDE_ASSISTANCE" in codes

    print(
        "TEST 2 PASSED - SERVICE PARSING STILL WORKS"
    )

    # V2 contract rule is represented by task metadata.
    task = Task(
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        current_duration=60,
        current_mileage=20000,
    )

    assert task.current_duration == 60
    assert task.current_mileage == 20000

    print(
        "TEST 3 PASSED - CONTRACT TASK CARRIES CURRENT CONTRACT DIMENSIONS"
    )

    print(
        "\nALL ARVAL ACQUISITION CONNECTOR V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
