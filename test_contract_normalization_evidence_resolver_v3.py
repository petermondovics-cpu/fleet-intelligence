from types import SimpleNamespace

from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResolverV3,
    RESOLVED,
)
from contract_normalization.provider_contract_state_discovery_v1 import (
    DiscoveredContractPrice,
    ProviderContractStateDiscoveryResult,
    OBSERVED,
    UNRESOLVED,
)

class FakeDiscovery:
    def discover(self, offer, *, coordinates):
        provider = offer.provider
        if provider == "Arval":
            observations = (
                DiscoveredContractPrice("Arval",60,20000,192312,"a","explicit","EXACT_OFFER_UI_STATE"),
                DiscoveredContractPrice("Arval",48,20000,205000,"a","explicit","EXACT_OFFER_UI_STATE"),
            )
        else:
            observations = (
                DiscoveredContractPrice("Ayvens",48,20000,189990,"b","explicit","EXACT_OFFER_PROVIDER_API"),
                DiscoveredContractPrice("Ayvens",60,20000,181000,"b","explicit","EXACT_OFFER_PROVIDER_API"),
            )
        return ProviderContractStateDiscoveryResult(
            OBSERVED, provider, coordinates, observations, "ok"
        )


class RecordingDiscovery:
    def __init__(self, observations_by_provider=None):
        self.observations_by_provider = observations_by_provider or {}
        self.calls = []

    def discover(self, offer, *, coordinates):
        self.calls.append((offer.provider, coordinates))
        observations = tuple(
            item
            for item in self.observations_by_provider.get(offer.provider, ())
            if (item.duration, item.mileage) in coordinates
        )
        return ProviderContractStateDiscoveryResult(
            OBSERVED if observations else UNRESOLVED,
            offer.provider,
            coordinates,
            observations,
            "ok",
        )


def discovered(provider, duration, mileage, fee):
    return DiscoveredContractPrice(
        provider,
        duration,
        mileage,
        fee,
        f"https://example.test/{provider.casefold()}",
        f"{duration}/{mileage} -> {fee}",
        "EXACT_OFFER_UI_STATE",
    )

def main():
    left=SimpleNamespace(provider="Arval",duration=60,mileage=20000,monthly_fee=192312,url="a")
    right=SimpleNamespace(provider="Ayvens",duration=48,mileage=20000,monthly_fee=189990,url="b")

    result=ContractNormalizationEvidenceResolverV3(
        browser=None,
        discovery=FakeDiscovery(),
    ).resolve(left,right)

    assert result.status == RESOLVED
    assert result.selected_coordinate.duration == 60
    assert result.selected_coordinate.mileage == 20000
    assert result.normalized_monthly_fee_left == 192312
    assert result.normalized_monthly_fee_right == 181000

    # Discovery must never reacquire an offer's already-known current
    # coordinate. A different financial UI state at the same duration and
    # mileage must not erase the current advertised observation.
    recording = RecordingDiscovery({
        "Ayvens": (
            discovered("Ayvens", 48, 20000, 223990),
        ),
    })
    result = ContractNormalizationEvidenceResolverV3(
        browser=None,
        discovery=recording,
    ).resolve(left, right)

    assert recording.calls == [
        ("Arval", ((48, 20000), (36, 20000))),
        ("Ayvens", ((60, 20000), (36, 20000))),
    ]
    assert result.attempted_coordinates == (
        (60, 20000),
        (48, 20000),
        (36, 20000),
    )
    assert tuple(
        (item.duration, item.mileage, item.monthly_fee, item.evidence_method)
        for item in result.right_observations
    ) == (
        (48, 20000, 189990, "CURRENT_EXACT_OFFER"),
    )

    # Conflicting prices at a genuinely alternative coordinate must remain
    # rejected. Filtering current targets must not weaken conflict handling.
    conflicting = RecordingDiscovery({
        "Ayvens": (
            discovered("Ayvens", 60, 20000, 181000),
            discovered("Ayvens", 60, 20000, 182000),
        ),
    })
    result = ContractNormalizationEvidenceResolverV3(
        browser=None,
        discovery=conflicting,
    ).resolve(left, right)

    assert result.status != RESOLVED
    assert result.selected_coordinate is None
    assert tuple(
        (item.duration, item.mileage, item.monthly_fee)
        for item in result.right_observations
    ) == ((48, 20000, 189990),)

    print("status:",result.status)
    print("attempted:",result.attempted_coordinates)
    print("common:",tuple((x.duration,x.mileage) for x in result.common_coordinates))
    print("selected:", result.selected_coordinate)
    print("TEST PASSED - V3 RESOLVES ONLY AN EXPLICIT COMMON PRICED COORDINATE.")

if __name__=="__main__":
    main()
