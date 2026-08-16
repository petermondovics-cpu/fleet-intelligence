from types import SimpleNamespace

from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResolverV3,
    RESOLVED,
)
from contract_normalization.provider_contract_state_discovery_v1 import (
    DiscoveredContractPrice,
    ProviderContractStateDiscoveryResult,
    OBSERVED,
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

    print("status:",result.status)
    print("attempted:",result.attempted_coordinates)
    print("common:",tuple((x.duration,x.mileage) for x in result.common_coordinates))
    print("selected:",result.selected_coordinate.duration,result.selected_coordinate.mileage)
    print("TEST PASSED - V3 RESOLVES ONLY AN EXPLICIT COMMON PRICED COORDINATE.")

if __name__=="__main__":
    main()
