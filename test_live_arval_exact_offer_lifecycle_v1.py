from playwright.sync_api import sync_playwright

from market_intelligence.exact_offer_lifecycle_resolver import (
    LIVE_CHANGED,
    LIVE_UNCHANGED,
    OFFER_NO_LONGER_AVAILABLE,
    OFFER_REPLACED,
    LIFECYCLE_UNRESOLVED,
    ExactOfferLifecycleResolver,
    HistoricalOfferObservation,
)
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajandlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


def identity(offer):
    n = (
        VehicleIdentityNormalizer()
        .normalize(
            getattr(
                offer,
                "brand",
                None,
            ),
            getattr(
                offer,
                "model",
                None,
            ),
            getattr(
                offer,
                "trim",
                None,
            ),
            getattr(
                offer,
                "fuel_type",
                None,
            ),
        )
    )

    return {
        "brand": (
            n.brand or ""
        ).casefold(),
        "model": (
            n.model or ""
        ).casefold(),
        "fuel_type": (
            n.fuel_type or ""
        ).casefold(),
        # Lifecycle exactness keeps trim explicit.
        "trim": " ".join(
            str(
                getattr(
                    offer,
                    "trim",
                    None,
                )
                or ""
            )
            .casefold()
            .split()
        ),
    }


def main():
    print("=" * 100)
    print("LIVE ARVAL EXACT OFFER LIFECYCLE V1")
    print("=" * 100)

    historical = (
        HistoricalOfferObservation(
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
            url=ARVAL_URL,
            observed_at=(
                "2026-08-14T00:00:00+00:00"
            ),
        )
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
                    identity_builder=identity,
                )
            )

            result = resolver.resolve(
                historical
            )

            print()
            print(
                "Status:",
                result.status,
            )
            print(
                "HTTP:",
                result.http_status,
            )
            print(
                "Checked URL:",
                result.checked_url,
            )
            print(
                "Final URL:",
                result.final_url,
            )
            print(
                "Historical observed at:",
                result.historical_observed_at,
            )
            print(
                "Historical monthly fee:",
                result.historical_monthly_fee,
            )
            print(
                "Live monthly fee:",
                result.live_monthly_fee,
            )
            print(
                "Delta:",
                result.monthly_fee_delta_huf,
            )
            print(
                "Historical identity:",
                result.historical_identity,
            )
            print(
                "Live identity:",
                result.live_identity,
            )
            print(
                "Historical contract:",
                result.historical_contract,
            )
            print(
                "Live contract:",
                result.live_contract,
            )
            print(
                "Diagnostic:",
                result.diagnostic,
            )

            assert result.status in {
                LIVE_UNCHANGED,
                LIVE_CHANGED,
                OFFER_REPLACED,
                OFFER_NO_LONGER_AVAILABLE,
                LIFECYCLE_UNRESOLVED,
            }

            assert (
                result.historical_monthly_fee
                == 192312
            )

            assert (
                result.historical_evidence_preserved
                is True
            )

            if result.http_status in {
                404,
                410,
            }:
                assert (
                    result.status
                    == OFFER_NO_LONGER_AVAILABLE
                )
                assert (
                    result.live_monthly_fee
                    is None
                )

            print()
            print(
                "TEST PASSED - LIVE ARVAL LIFECYCLE "
                "CLASSIFICATION PRESERVES THE HISTORICAL "
                "OBSERVATION EVEN WHEN THE EXACT OFFER "
                "IS NO LONGER LIVE."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
