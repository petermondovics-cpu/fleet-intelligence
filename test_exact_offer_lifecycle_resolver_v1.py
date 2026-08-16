from pathlib import Path
import tempfile
from types import SimpleNamespace

from market_intelligence.exact_offer_lifecycle_resolver import (
    LIVE_CHANGED,
    LIVE_UNCHANGED,
    OFFER_NO_LONGER_AVAILABLE,
    OFFER_REPLACED,
    LIFECYCLE_UNRESOLVED,
    ExactOfferLifecycleResolver,
    HistoricalOfferObservation,
)
from market_intelligence.offer_lifecycle_repository import (
    OfferLifecycleRepository,
)


class FakeResponse:
    def __init__(self, status):
        self.status = status


class FakePage:
    def __init__(self, status, final_url):
        self.status = status
        self.url = final_url

    def goto(self, url, **kwargs):
        self.url = self.url or url
        return FakeResponse(
            self.status
        )

    def wait_for_timeout(self, ms):
        pass

    def close(self):
        pass


class FakeBrowser:
    def __init__(self, status, final_url=None):
        self.status = status
        self.final_url = final_url

    def new_page(self):
        return FakePage(
            self.status,
            self.final_url,
        )


def historical():
    return HistoricalOfferObservation(
        offer_key="arval-byd-atto2-boost-60-20",
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        monthly_fee=192312,
        duration=60,
        mileage=20000,
        url="https://example.test/exact-offer",
        observed_at="2026-08-13T10:00:00+00:00",
    )


def loaded(
    *,
    brand="BYD",
    model="ATTO 2",
    trim="Boost",
    fee=192312,
    duration=60,
    mileage=20000,
):
    offer = SimpleNamespace(
        provider="Arval",
        brand=brand,
        model=model,
        trim=trim,
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url="https://example.test/exact-offer",
    )

    return SimpleNamespace(
        composite=SimpleNamespace(
            offer=offer
        )
    )


def resolver(
    status,
    live,
):
    return ExactOfferLifecycleResolver(
        FakeBrowser(
            status,
            "https://example.test/exact-offer",
        ),
        live_loader=lambda page: live,
    )


def main():
    print("=" * 96)
    print("EXACT OFFER LIFECYCLE RESOLVER V1")
    print("=" * 96)

    # --------------------------------------------------------
    # 1. LIVE UNCHANGED
    # --------------------------------------------------------

    result = resolver(
        200,
        loaded(),
    ).resolve(
        historical()
    )

    assert result.status == LIVE_UNCHANGED
    assert result.monthly_fee_delta_huf == 0
    assert result.historical_monthly_fee == 192312

    print("TEST 1 PASSED - LIVE_UNCHANGED")

    # --------------------------------------------------------
    # 2. LIVE CHANGED
    # --------------------------------------------------------

    result = resolver(
        200,
        loaded(
            fee=199999
        ),
    ).resolve(
        historical()
    )

    assert result.status == LIVE_CHANGED
    assert result.monthly_fee_delta_huf == 7687
    assert result.historical_monthly_fee == 192312
    assert result.live_monthly_fee == 199999

    print("TEST 2 PASSED - LIVE_CHANGED")

    # --------------------------------------------------------
    # 3. OFFER REPLACED
    # --------------------------------------------------------

    result = resolver(
        200,
        loaded(
            trim="Active",
        ),
    ).resolve(
        historical()
    )

    assert result.status == OFFER_REPLACED
    assert result.monthly_fee_delta_huf is None

    print("TEST 3 PASSED - OFFER_REPLACED")

    # --------------------------------------------------------
    # 4. NO LONGER AVAILABLE
    # --------------------------------------------------------

    result = resolver(
        404,
        loaded(),
    ).resolve(
        historical()
    )

    assert (
        result.status
        == OFFER_NO_LONGER_AVAILABLE
    )
    assert result.live_monthly_fee is None
    assert result.historical_monthly_fee == 192312
    assert result.historical_evidence_preserved is True

    print(
        "TEST 4 PASSED - HTTP 404 BECOMES "
        "OFFER_NO_LONGER_AVAILABLE WITHOUT ERASING HISTORY"
    )

    # --------------------------------------------------------
    # 5. ACCESS ERROR IS NOT REMOVAL
    # --------------------------------------------------------

    result = resolver(
        403,
        loaded(),
    ).resolve(
        historical()
    )

    assert result.status == LIFECYCLE_UNRESOLVED

    print(
        "TEST 5 PASSED - HTTP 403 DOES NOT BECOME OFFER REMOVAL"
    )

    # --------------------------------------------------------
    # 6. APPEND-ONLY PERSISTENCE
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        db = str(
            Path(tmp)
            / "lifecycle.db"
        )

        repository = (
            OfferLifecycleRepository(
                db
            )
        )

        gone = resolver(
            404,
            loaded(),
        ).resolve(
            historical()
        )

        row_id = repository.save(
            gone
        )

        assert row_id > 0

        latest = (
            repository.latest_for_offer(
                historical().offer_key
            )
        )

        assert latest is not None
        assert (
            latest.status
            == OFFER_NO_LONGER_AVAILABLE
        )
        assert (
            latest.historical_monthly_fee
            == 192312
        )

        history = (
            repository.history_for_offer(
                historical().offer_key
            )
        )

        assert len(history) == 1

    print(
        "TEST 6 PASSED - LIFECYCLE IS APPEND-ONLY "
        "AND HISTORICAL PRICE IS PRESERVED"
    )

    print()
    print(
        "ALL EXACT OFFER LIFECYCLE V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
