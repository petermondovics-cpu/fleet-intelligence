from playwright.sync_api import sync_playwright

from market_intelligence.exact_offer_lifecycle_resolver import (
    ExactOfferLifecycleResolver,
    HistoricalOfferObservation,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.arval.offer_url_canonicalizer import (
    ArvalOfferUrlCanonicalizer,
)


RAW_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/"
    "byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 100)
    print("LIVE ARVAL CANONICAL URL -> LIFECYCLE V1")
    print("=" * 100)

    canonical = (
        ArvalOfferUrlCanonicalizer()
        .canonical_url(
            RAW_URL
        )
    )

    print(
        "Raw URL:",
        RAW_URL,
    )
    print(
        "Canonical URL:",
        canonical,
    )

    historical = HistoricalOfferObservation(
        offer_key=(
            "ARVAL::BYD::ATTO2::BOOST::60::20000"
        ),
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        trim="1.5 PHEV BOOST AT",
        fuel_type="PHEV",
        monthly_fee=192312,
        duration=60,
        mileage=20000,
        url=canonical,
        observed_at=(
            "2026-08-14T00:00:00+00:00"
        ),
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            resolver = (
                ExactOfferLifecycleResolver(
                    browser,
                    live_loader=lambda page: (
                        ArvalEvidenceAwareBuilder()
                        .build(page)
                    ),
                )
            )

            result = resolver.resolve(
                historical
            )

            print()
            print(
                "Lifecycle status:",
                result.status,
            )
            print(
                "HTTP:",
                result.http_status,
            )
            print(
                "Historical fee:",
                result.historical_monthly_fee,
            )
            print(
                "Live fee:",
                result.live_monthly_fee,
            )
            print(
                "Diagnostic:",
                result.diagnostic,
            )

            # Critical regression assertion:
            # a 404 caused by duplicated URL construction must no longer
            # be used for this lifecycle check.
            assert (
                result.checked_url
                == canonical
            )

            assert (
                result.checked_url
                != RAW_URL
            )

            print()
            print(
                "TEST PASSED - LIFECYCLE CHECK USES "
                "THE CANONICAL ARVAL OFFER URL, NOT "
                "THE DUPLICATED SCRAPER URL."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
