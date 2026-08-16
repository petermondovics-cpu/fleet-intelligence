from dataclasses import dataclass
from comparison.provider_acquisition_router import ProviderAcquisitionRouter

@dataclass
class Offer:
    provider: str
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

@dataclass
class Task:
    provider: str
    action_type: str = "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT"
    target_dimension: str = "CONTRACT"
    priority: int = 10
    blocker_code: str = "CONTRACT_NORMALIZATION_INCOMPLETE"
    strategy: str = "DISCOVER"
    allowed_sources: tuple = ("PROVIDER_PRICED_OFFER_PAGE",)
    prohibited_sources: tuple = ()
    canonical_vehicle_key: str = "BYD|ATTO 2|PHEV"
    message: str = "test"

class Connector:
    def contract_discovery(self, task): return None

def mk(provider, duration, mileage):
    o = Offer(provider, duration, mileage, f"https://example.test/{provider}")
    return Side(Composite(provider, o))

def main():
    left = mk("Arval", 60, 20000)
    right = mk("Ayvens", 48, 20000)
    r = ProviderAcquisitionRouter(arval_connector=Connector(), ayvens_connector=Connector())

    a = r._route_task(Task("Arval"), left, right)
    y = r._route_task(Task("Ayvens"), left, right)

    assert (a.target_duration, a.target_mileage) == (48, 20000)
    assert (y.target_duration, y.target_mileage) == (60, 20000)

    print("TEST 1 PASSED - ARVAL TARGET 48/20000")
    print("TEST 2 PASSED - AYVENS TARGET 60/20000")
    print("\nALL TARGET CONTRACT ROUTING V1 TESTS PASSED")

if __name__ == "__main__":
    main()
