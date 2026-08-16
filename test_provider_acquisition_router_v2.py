from dataclasses import dataclass

from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)


@dataclass
class Offer:
    brand: str
    model: str
    trim: str
    fuel_type: str
    duration: int
    mileage: int
    url: str


@dataclass
class Composite:
    provider: str
    offer: Offer


@dataclass
class Side:
    composite: Composite
    standard_equipment_status: str


@dataclass
class Result:
    status: str = "VALIDATED"
    source_type: str = "MANUFACTURER_MODEL_PAGE"
    source_url: str = "https://www.byd.com/example"
    source_text: str = "official spec"
    provider_equipment_status: str = "NOT_PUBLISHED"
    manufacturer_equipment_status: str = "VALIDATED"
    brand: str = "BYD"
    model: str = "ATTO 2 DM-i"
    trim: str = "Boost"
    fuel_type: str = "PHEV"
    equipment: tuple = ("360 camera",)


class Manufacturer:
    def acquire(self, task, offer, provider_equipment_status):
        assert provider_equipment_status == "NOT_PUBLISHED"
        return Result()


class Connector:
    pass


@dataclass
class Task:
    provider: str = "Arval"


def main():
    arval = Side(
        Composite(
            "Arval",
            Offer(
                "BYD",
                "ATTO 2",
                "1.5 PHEV BOOST AT",
                "PHEV",
                60,
                20000,
                "https://arval.example",
            ),
        ),
        "NOT_PUBLISHED",
    )

    ayvens = Side(
        Composite(
            "Ayvens",
            Offer(
                "BYD",
                "ATTO 2 DM-i",
                "Active 166 HP",
                "PHEV",
                48,
                20000,
                "https://ayvens.example",
            ),
        ),
        "PARSING_UNRESOLVED",
    )

    router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
        manufacturer_equipment=Manufacturer(),
    )

    router._left = arval
    router._right = ayvens

    payload = router._equipment_discovery(
        Task()
    )

    assert payload is not None
    assert payload["evidence_owner"] == "MANUFACTURER"
    assert payload["provider_equipment_status"] == "NOT_PUBLISHED"
    assert payload["manufacturer_equipment_status"] == "VALIDATED"
    assert payload["equipment"] == ("360 camera",)

    print(
        "TEST 1 PASSED - MANUFACTURER EQUIPMENT ROUTED "
        "WITHOUT OVERWRITING PROVIDER EVIDENCE"
    )

    print(
        "\nALL PROVIDER ACQUISITION ROUTER V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
