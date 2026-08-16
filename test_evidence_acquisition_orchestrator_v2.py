from dataclasses import dataclass
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)

@dataclass
class Vehicle:
    brand: str
    model: str
    fuel_type: str
    trim: str = ""

@dataclass
class Composite:
    provider: str
    vehicle: Vehicle

@dataclass
class Side:
    composite: Composite

def main():
    engine = EvidenceAcquisitionOrchestrator()

    arval = Side(
        Composite(
            "Arval",
            Vehicle(
                "BYD",
                "ATTO 2",
                "PHEV",
                "1.5 PHEV BOOST AT",
            ),
        )
    )

    ayvens = Side(
        Composite(
            "Ayvens",
            Vehicle(
                "BYD",
                "ATTO 2 DM-i",
                "PHEV",
                "Active 166 HP",
            ),
        )
    )

    a = engine._vehicle_key(arval)
    b = engine._vehicle_key(ayvens)

    print("Arval canonical key :", a)
    print("Ayvens canonical key:", b)

    assert a == "BYD|ATTO 2|PHEV"
    assert b == "BYD|ATTO 2|PHEV"
    assert a == b

    print(
        "TEST 1 PASSED - "
        "PROVIDER MODEL ALIASES SHARE ONE CANONICAL KEY"
    )

    print(
        "\\nALL EVIDENCE ACQUISITION "
        "ORCHESTRATOR V2 TESTS PASSED"
    )

if __name__ == "__main__":
    main()
