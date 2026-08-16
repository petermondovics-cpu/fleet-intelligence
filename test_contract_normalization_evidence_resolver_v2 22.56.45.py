from types import SimpleNamespace

from contract_normalization.contract_normalization_evidence_resolver_v2 import (
    RESOLVED,
    UNRESOLVED,
    ContractNormalizationEvidenceResolverV2,
)


class FakeArvalObserver:
    def __init__(self, observations=()):
        self.observations = observations

    def observe(self, url, targets):
        wanted = tuple(
            item for item in self.observations
            if (item.duration, item.mileage) in targets
        )
        return SimpleNamespace(
            status="OBSERVED" if wanted else "UNRESOLVED",
            source_url=url,
            observations=wanted,
        )


class FakeAyvensResolver:
    def __init__(self, observations=()):
        self.observations = observations

    def resolve(self, url, *, targets):
        wanted = tuple(
            item for item in self.observations
            if (item.duration, item.mileage) in targets
        )
        return SimpleNamespace(
            status="OBSERVED" if wanted else "UNRESOLVED",
            source_url=url,
            observations=wanted,
        )


def observation(duration, mileage, fee, method="EXACT_OFFER_UI_STATE"):
    return SimpleNamespace(
        duration=duration,
        mileage=mileage,
        monthly_fee=fee,
        source_text=f"{duration}/{mileage} -> {fee}",
        evidence_method=method,
    )


def offer(provider, duration, mileage, fee):
    return SimpleNamespace(
        provider=provider,
        duration=duration,
        mileage=mileage,
        monthly_fee=fee,
        url="https://example.test/" + provider.casefold(),
    )


def main():
    print("=" * 100)
    print("CONTRACT NORMALIZATION EVIDENCE RESOLVER V2")
    print("=" * 100)

    arval = offer("Arval", 60, 20000, 192312)
    ayvens = offer("Ayvens", 48, 20000, 189990)

    result = ContractNormalizationEvidenceResolverV2(
        None,
        arval_observer=FakeArvalObserver(),
        ayvens_resolver=FakeAyvensResolver(),
    ).resolve(arval, ayvens)

    assert result.status == UNRESOLVED
    assert result.attempted_coordinates == ((60, 20000), (48, 20000))
    assert result.normalized_price_available is False
    print("TEST 1 PASSED - ONE-SIDED CURRENT STATES DO NOT NORMALIZE.")

    result = ContractNormalizationEvidenceResolverV2(
        None,
        arval_observer=FakeArvalObserver(),
        ayvens_resolver=FakeAyvensResolver(
            (
                observation(
                    60,
                    20000,
                    181500,
                    method="EXACT_OFFER_PROVIDER_API",
                ),
            )
        ),
    ).resolve(arval, ayvens)

    assert result.status == RESOLVED
    assert result.selected_coordinate.duration == 60
    assert result.normalized_monthly_fee_left == 192312
    assert result.normalized_monthly_fee_right == 181500
    print("TEST 2 PASSED - EXPLICIT AYVENS 60/20K RESOLVES AGAINST CURRENT ARVAL 60/20K.")

    result = ContractNormalizationEvidenceResolverV2(
        None,
        arval_observer=FakeArvalObserver(
            (observation(48, 20000, 201000),)
        ),
        ayvens_resolver=FakeAyvensResolver(),
    ).resolve(arval, ayvens)

    assert result.status == RESOLVED
    assert result.selected_coordinate.duration == 48
    assert result.normalized_monthly_fee_left == 201000
    assert result.normalized_monthly_fee_right == 189990
    print("TEST 3 PASSED - EXPLICIT ARVAL 48/20K RESOLVES AGAINST CURRENT AYVENS 48/20K.")

    result = ContractNormalizationEvidenceResolverV2(
        None,
        arval_observer=FakeArvalObserver(),
        ayvens_resolver=FakeAyvensResolver(),
    ).resolve(arval, ayvens)

    assert result.status == UNRESOLVED
    assert result.selected_coordinate is None
    print("TEST 4 PASSED - UNPRICED CAPABILITY CANNOT BECOME NORMALIZATION EVIDENCE.")

    print()
    print("ALL CONTRACT NORMALIZATION EVIDENCE RESOLVER V2 TESTS PASSED")


if __name__ == "__main__":
    main()
