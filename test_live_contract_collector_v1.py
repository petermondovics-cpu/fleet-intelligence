from models.offer import Offer
from models.contract_discovery import (
    DiscoveredContract,
)
from live_contract_collector import (
    LiveContractCollector,
)


def main():

    contracts = [
        DiscoveredContract(
            duration=60,
            mileage=20000,
        ),
        DiscoveredContract(
            duration=48,
            mileage=20000,
        ),
    ]

    selected = []

    def select_contract(contract):

        selected.append(
            (
                contract.duration,
                contract.mileage,
            )
        )

    def parse_selected_contract(contract):

        price = {
            (60, 20000): 192312,
            (48, 20000): 189990,
        }[
            (
                contract.duration,
                contract.mileage,
            )
        ]

        return Offer(
            provider="LIVE_TEST",
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
            monthly_fee=price,
            duration=contract.duration,
            mileage=contract.mileage,
            url="https://example.com/live-test",
        )

    collector = LiveContractCollector()

    result = collector.collect(
        provider="LIVE_TEST",
        url="https://example.com/live-test",
        contracts=contracts,
        select_contract=select_contract,
        parse_selected_contract=parse_selected_contract,
    )

    assert result.provider == "LIVE_TEST"
    assert len(result.results) == 2
    assert len(result.offers) == 2

    assert selected == [
        (60, 20000),
        (48, 20000),
    ]

    assert {
        (
            offer.duration,
            offer.mileage,
        )
        for offer in result.offers
    } == {
        (60, 20000),
        (48, 20000),
    }

    print(
        "TEST 1 PASSED - "
        "LIVE COLLECTOR ORCHESTRATION"
    )

    # ------------------------------------------------
    # A parser mismatch must never leak into offers.
    # ------------------------------------------------

    def parse_wrong_contract(contract):

        return Offer(
            provider="LIVE_TEST",
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
            monthly_fee=192312,
            duration=48,
            mileage=20000,
            url="https://example.com/live-test",
        )

    wrong = collector.collect(
        provider="LIVE_TEST",
        url="https://example.com/live-test",
        contracts=[
            DiscoveredContract(
                duration=60,
                mileage=20000,
            )
        ],
        select_contract=lambda contract: None,
        parse_selected_contract=parse_wrong_contract,
    )

    assert len(wrong.offers) == 0
    assert (
        wrong.results[0].status
        == "REJECTED"
    )

    print(
        "TEST 2 PASSED - "
        "VALIDATION BARRIER PRESERVED"
    )

    print(
        "\nALL LIVE CONTRACT COLLECTOR V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
