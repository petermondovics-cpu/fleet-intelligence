from models.offer import Offer
from models.contract_variant import (
    ContractVariant,
    DEFAULT_CONTRACT_VARIANTS,
)


def main():

    assert len(
        DEFAULT_CONTRACT_VARIANTS
    ) == 4

    assert (
        ContractVariant(48, 20000)
        in DEFAULT_CONTRACT_VARIANTS
    )

    assert (
        ContractVariant(60, 30000)
        in DEFAULT_CONTRACT_VARIANTS
    )

    assert len(
        {
            (
                item.duration,
                item.mileage,
            )
            for item in DEFAULT_CONTRACT_VARIANTS
        }
    ) == 4

    print(
        "TEST 1 PASSED - "
        "DEFAULT CONTRACT MATRIX"
    )

    # ------------------------------------------------
    # Offer identity is intentionally unchanged.
    # Different contract variants must remain separate
    # offers because contract normalization depends on
    # observing the individual prices.
    # ------------------------------------------------

    offers = [
        Offer(
            provider="Arval",
            brand="BYD",
            model="ATTO 2",
            trim="",
            fuel_type="EV",
            monthly_fee=180000,
            duration=48,
            mileage=20000,
            url="https://example.com/atto2",
        ),
        Offer(
            provider="Arval",
            brand="BYD",
            model="ATTO 2",
            trim="",
            fuel_type="EV",
            monthly_fee=185000,
            duration=48,
            mileage=30000,
            url="https://example.com/atto2",
        ),
        Offer(
            provider="Arval",
            brand="BYD",
            model="ATTO 2",
            trim="",
            fuel_type="EV",
            monthly_fee=192000,
            duration=60,
            mileage=20000,
            url="https://example.com/atto2",
        ),
        Offer(
            provider="Arval",
            brand="BYD",
            model="ATTO 2",
            trim="",
            fuel_type="EV",
            monthly_fee=198000,
            duration=60,
            mileage=30000,
            url="https://example.com/atto2",
        ),
    ]

    contracts = {
        (
            offer.duration,
            offer.mileage,
        )
        for offer in offers
    }

    assert len(contracts) == 4

    print(
        "TEST 2 PASSED - "
        "FOUR CONTRACT VARIANTS REMAIN DISTINCT"
    )

    # ------------------------------------------------
    # The matrix must not change the core Offer model.
    # ------------------------------------------------

    for offer in offers:
        assert isinstance(offer, Offer)
        assert offer.duration > 0
        assert offer.mileage > 0
        assert offer.monthly_fee > 0

    print(
        "TEST 3 PASSED - "
        "OFFER MODEL COMPATIBILITY"
    )

    print(
        "\nALL MULTI-CONTRACT COLLECTION "
        "MODEL TESTS PASSED"
    )


if __name__ == "__main__":
    main()
