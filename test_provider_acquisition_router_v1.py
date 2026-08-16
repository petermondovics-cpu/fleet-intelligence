from dataclasses import dataclass

from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)


@dataclass
class Offer:
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


@dataclass(frozen=True)
class Task:
    provider: str
    action_type: str
    target_dimension: str
    priority: int
    blocker_code: str
    strategy: str
    allowed_sources: tuple
    prohibited_sources: tuple
    canonical_vehicle_key: str
    message: str


class Connector:
    def contract_discovery(self, task):
        return {
            "provider": task.provider,
            "duration": task.current_duration,
            "mileage": task.current_mileage,
        }


def main():

    left = Side(
        Composite(
            "Arval",
            Offer(
                60,
                20000,
                "https://arval.example/offer",
            ),
        )
    )

    right = Side(
        Composite(
            "Ayvens",
            Offer(
                48,
                20000,
                "https://ayvens.example/offer",
            ),
        )
    )

    router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
    )

    arval_task = Task(
        provider="Arval",
        action_type="X",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="X",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    routed = router._route_task(
        arval_task,
        left,
        right,
    )

    assert routed.current_duration == 60
    assert routed.current_mileage == 20000
    assert (
        routed.current_url
        == "https://arval.example/offer"
    )

    print(
        "TEST 1 PASSED - "
        "CURRENT PROVIDER CONTRACT CONTEXT ATTACHED"
    )

    ayvens_task = Task(
        provider="Ayvens",
        action_type="X",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="X",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    routed = router._route_task(
        ayvens_task,
        left,
        right,
    )

    assert routed.current_duration == 48

    assert (
        router._connector_for("Arval")
        is router.arval
    )

    assert (
        router._connector_for("Ayvens")
        is router.ayvens
    )

    print(
        "TEST 2 PASSED - "
        "TASKS ROUTE TO CORRECT PROVIDER CONNECTOR"
    )

    print(
        "\nALL PROVIDER ACQUISITION ROUTER V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
