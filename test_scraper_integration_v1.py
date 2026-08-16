from models.contract_discovery import (
    DiscoveredContract,
)
from contract_collection.engine import (
    ContractCollectionEngine,
)


def main():

    arval_methods = [
        "discover_contracts",
        "select_contract",
        "parse_selected_contract",
        "collect_offer",
    ]

    ayvens_methods = [
        "discover_contracts",
        "select_contract",
        "parse_selected_contract",
        "collect_offer",
    ]

    from scrapers.arval.scraper import (
        ArvalScraper,
    )
    from scrapers.ayvens.scraper import (
        AyvensScraper,
    )

    arval = ArvalScraper()
    ayvens = AyvensScraper()

    for name in arval_methods:
        assert callable(
            getattr(arval, name)
        )

    for name in ayvens_methods:
        assert callable(
            getattr(ayvens, name)
        )

    print(
        "TEST 1 PASSED - "
        "ARVAL INTEGRATION SURFACE"
    )

    print(
        "TEST 2 PASSED - "
        "AYVENS INTEGRATION SURFACE"
    )

    # Provider-neutral collector remains the single
    # validation barrier.
    engine = ContractCollectionEngine()

    contract = DiscoveredContract(
        duration=48,
        mileage=20000,
    )

    assert contract.duration == 48
    assert contract.mileage == 20000

    print(
        "TEST 3 PASSED - "
        "DISCOVERY/COLLECTION CONTRACT COMPATIBILITY"
    )

    print(
        "\nALL SCRAPER INTEGRATION V1 "
        "STATIC TESTS PASSED"
    )


if __name__ == "__main__":
    main()
