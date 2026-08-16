from models.offer import Offer
from models.contract_discovery import (
    DiscoveredContract,
)
from contract_collection.engine import (
    ContractCollectionEngine,
)


def main():

    contracts = [
        DiscoveredContract(
            duration=48,
            mileage=20000,
        ),
        DiscoveredContract(
            duration=60,
            mileage=20000,
        ),
        DiscoveredContract(
            duration=48,
            mileage=30000,
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

    def parse_contract(contract):

        prices = {
            (48, 20000): 189990,
            (60, 20000): 194990,
            (48, 30000): 199990,
        }

        return Offer(
            provider="TEST",
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
            monthly_fee=prices[
                (
                    contract.duration,
                    contract.mileage,
                )
            ],
            duration=contract.duration,
            mileage=contract.mileage,
            url="https://example.com/test",
        )

    engine = ContractCollectionEngine()

    results = engine.collect(
        contracts=contracts,
        select_contract=select_contract,
        parse_selected_contract=parse_contract,
    )

    assert len(results) == 3

    assert all(
        result.status == "COLLECTED"
        for result in results
    )

    assert len(
        engine.offers(results)
    ) == 3

    assert selected == [
        (48, 20000),
        (60, 20000),
        (48, 30000),
    ]

    print(
        "TEST 1 PASSED - "
        "ALL DISCOVERED CONTRACTS COLLECTED"
    )

    # ------------------------------------------------
    # Validation must reject an offer when the
    # provider parser reports a different contract.
    # ------------------------------------------------

    def parse_wrong_contract(contract):

        return Offer(
            provider="TEST",
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
            monthly_fee=189990,
            duration=48,
            mileage=20000,
            url="https://example.com/test",
        )

    wrong_result = engine.collect(
        contracts=[
            DiscoveredContract(
                duration=60,
                mileage=30000,
            )
        ],
        select_contract=lambda contract: None,
        parse_selected_contract=parse_wrong_contract,
    )

    assert (
        wrong_result[0].status
        == "REJECTED"
    )

    assert (
        wrong_result[0].offer
        is None
    )

    assert (
        "Duration validation failed"
        in wrong_result[0].reason
    )

    print(
        "TEST 2 PASSED - "
        "WRONG CONTRACT REJECTED"
    )

    # ------------------------------------------------
    # Price must also be validated.
    # ------------------------------------------------

    def parse_zero_price(contract):

        return Offer(
            provider="TEST",
            brand="BYD",
            model="ATTO 2",
            trim="TEST",
            fuel_type="PHEV",
            monthly_fee=0,
            duration=contract.duration,
            mileage=contract.mileage,
            url="https://example.com/test",
        )

    price_result = engine.collect(
        contracts=[
            DiscoveredContract(
                duration=48,
                mileage=20000,
            )
        ],
        select_contract=lambda contract: None,
        parse_selected_contract=parse_zero_price,
    )

    assert (
        price_result[0].status
        == "REJECTED"
    )

    assert (
        "Monthly fee validation failed"
        in price_result[0].reason
    )

    print(
        "TEST 3 PASSED - "
        "INVALID PRICE REJECTED"
    )

    print(
        "\nALL CONTRACT COLLECTION V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
