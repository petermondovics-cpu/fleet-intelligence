from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


PRICE_SELECTOR = (
    "div.font-size-40px.font-size-40px, "
    "div.font-size-40px.fw-500.whitespace-nowrap"
)


class FakeFirst:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def wait_for(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error


class FakeLocator:
    def __init__(self, first):
        self.first = first


class FakePage:
    def __init__(self, error=None):
        self.first = FakeFirst(error)
        self.selectors = []
        self.goto_calls = []
        self.waits = []
        self.closed = False

    def goto(self, url, **kwargs):
        self.goto_calls.append((url, kwargs))

    def locator(self, selector):
        self.selectors.append(selector)
        return FakeLocator(self.first)

    def wait_for_timeout(self, ms):
        self.waits.append(ms)

    def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self, page):
        self.page = page

    def new_page(self):
        return self.page


class FakeBuilder:
    def build(self, page):
        return "BUILT"


class TestBridge(MarketPairFullComparisonBridge):
    @classmethod
    def _builder_for(cls, provider):
        return FakeBuilder()

    @staticmethod
    def _dismiss(page):
        pass


def main():
    page = FakePage()

    MarketPairFullComparisonBridge._wait_for_ayvens_priced_offer(
        page
    )

    assert page.selectors == [PRICE_SELECTOR]
    assert page.first.calls == [
        {
            "state": "attached",
            "timeout": 60000,
        }
    ]

    print(
        "TEST 1 PASSED - AYVENS LOAD WAITS FOR EXPLICIT "
        "PRICED-OFFER DOM"
    )

    page = FakePage(
        TimeoutError(
            "priced-offer DOM did not appear"
        )
    )

    try:
        MarketPairFullComparisonBridge._wait_for_ayvens_priced_offer(
            page
        )
    except TimeoutError as exc:
        assert "priced-offer DOM" in str(exc)
    else:
        raise AssertionError(
            "Missing priced-offer DOM must remain a load failure."
        )

    print(
        "TEST 2 PASSED - MISSING PRICE DOM REMAINS EXPLICIT FAILURE"
    )

    page = FakePage()
    url = "https://provider.example/exact-offer"

    result = TestBridge._load(
        FakeBrowser(page),
        "Ayvens",
        url,
    )

    assert result == "BUILT"
    assert page.goto_calls == [
        (
            url,
            {
                "wait_until": "commit",
                "timeout": 60000,
            },
        )
    ]
    assert page.selectors == [PRICE_SELECTOR]
    assert page.waits == [300]
    assert page.closed is True

    print(
        "TEST 3 PASSED - AYVENS LOAD USES HTTP COMMIT THEN "
        "PRICED-OFFER READINESS"
    )

    print(
        "\nALL AYVENS BRIDGE OFFER READINESS V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
