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
class EquipmentEvidence:
    standard_status: str
    optional_status: str


@dataclass
class Side:
    composite: Composite
    equipment_evidence: EquipmentEvidence


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
        if provider_equipment_status != "NOT_PUBLISHED":
            return type(
                "Unresolved",
                (),
                {
                    "status": "UNRESOLVED",
                },
            )()
        return Result()


class Connector:
    pass


@dataclass
class Task:
    provider: str


def make_side(provider, status):
    return Side(
        Composite(
            provider,
            Offer(
                "BYD",
                "ATTO 2",
                "Boost",
                "PHEV",
                60,
                20000,
                f"https://{provider.lower()}.example",
            ),
        ),
        EquipmentEvidence(
            standard_status=status,
            optional_status=status,
        ),
    )


def main():
    arval = make_side("Arval", "NOT_PUBLISHED")
    ayvens = make_side("Ayvens", "PARSING_UNRESOLVED")

    router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
        manufacturer_equipment=Manufacturer(),
    )

    router._left = arval
    router._right = ayvens

    assert (
        router._provider_equipment_status(arval)
        == "NOT_PUBLISHED"
    )
    assert (
        router._provider_equipment_status(ayvens)
        == "PARSING_UNRESOLVED"
    )

    print(
        "TEST 1 PASSED - REAL EQUIPMENT EVIDENCE STATUS IS PRESERVED"
    )

    payload = router._equipment_discovery(
        Task("Arval")
    )

    assert payload is not None
    assert payload["equipment_items"] == ("360 camera",)
    assert payload["equipment"] == ("360 camera",)
    assert payload["provider_equipment_status"] == "NOT_PUBLISHED"
    assert payload["evidence_owner"] == "MANUFACTURER"

    print(
        "TEST 2 PASSED - EXECUTOR-COMPATIBLE equipment_items FIELD EMITTED"
    )

    ayvens_payload = router._equipment_discovery(
        Task("Ayvens")
    )

    assert ayvens_payload is None

    print(
        "TEST 3 PASSED - PARSING_UNRESOLVED DOES NOT SILENTLY "
        "FALL BACK TO MANUFACTURER EVIDENCE"
    )

    print(
        "\\nALL PROVIDER ACQUISITION ROUTER V3 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
