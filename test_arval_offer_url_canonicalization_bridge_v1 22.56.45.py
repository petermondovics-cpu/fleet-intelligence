from models.offer import Offer
from scrapers.arval.offer_url_canonicalization_bridge import (
    ArvalOfferUrlCanonicalizationBridge,
)


def main():

    bad = (
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajandlat/"
        "byd-atto-2-15-phev-boost-at/"
        "byd-atto-2-15-phev-boost-at"
    )

    good = (
        "https://www.arval.hu/kis-es-kozepvallalkozasok/"
        "tartos-berleti-ajandlat/"
        "byd-atto-2-15-phev-boost-at"
    )

    offer = Offer(
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        trim="1.5 PHEV BOOST AT",
        fuel_type="PHEV",
        monthly_fee=192312,
        duration=60,
        mileage=20000,
        url=bad,
    )

    normalized = (
        ArvalOfferUrlCanonicalizationBridge()
        .canonicalize_offer(
            offer
        )
    )

    assert normalized.url == good

    # Commercial evidence is untouched.
    assert (
        normalized.monthly_fee
        == 192312
    )
    assert normalized.duration == 60
    assert normalized.mileage == 20000
    assert normalized.trim == offer.trim

    # Original observation object is untouched.
    assert offer.url == bad

    print(
        "TEST PASSED - URL CANONICALIZATION "
        "CHANGES ONLY THE OFFER URL AND DOES "
        "NOT MUTATE COMMERCIAL EVIDENCE."
    )


if __name__ == "__main__":
    main()
