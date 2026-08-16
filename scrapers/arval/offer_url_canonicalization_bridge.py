from dataclasses import replace
from typing import Iterable, Tuple

from models.offer import Offer
from scrapers.arval.offer_url_canonicalizer import (
    ArvalOfferUrlCanonicalizer,
)


class ArvalOfferUrlCanonicalizationBridge:
    """
    Applies Arval URL canonicalization at the offer boundary.

    This bridge creates replacement Offer instances rather than mutating
    existing observations in-place.
    """

    def __init__(self):
        self.urls = (
            ArvalOfferUrlCanonicalizer()
        )

    def canonicalize_offer(
        self,
        offer: Offer,
    ) -> Offer:

        result = (
            self.urls.canonicalize(
                offer.url
            )
        )

        if not result.changed:
            return offer

        return replace(
            offer,
            url=result.canonical_url,
        )

    def canonicalize_all(
        self,
        offers: Iterable[Offer],
    ) -> Tuple[Offer, ...]:

        return tuple(
            self.canonicalize_offer(
                offer
            )
            for offer in offers
        )
