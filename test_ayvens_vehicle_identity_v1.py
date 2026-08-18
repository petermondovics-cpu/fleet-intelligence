from scrapers.ayvens.vehicle_identity_parser import (
    AyvensVehicleIdentityParser,
)


class FakeLocator:

    def __init__(
        self,
        values=None,
        text="",
    ):
        self.values = values or []
        self.text = text

    @property
    def first(self):
        return self

    def count(self):
        return (
            len(self.values)
            if self.values
            else (1 if self.text else 0)
        )

    def nth(self, index):
        return FakeLocator(
            text=self.values[index]
        )

    def inner_text(self):
        return self.text


class FakePage:

    def __init__(
        self,
        url,
        breadcrumbs,
        trim,
    ):
        self.url = url
        self._breadcrumbs = breadcrumbs
        self._trim = trim

    def locator(self, selector):
        if selector == "li.breadcrumbs-item":
            return FakeLocator(
                values=self._breadcrumbs
            )

        if (
            selector
            == "div.font-size-18px.fw-400.font-source.color-blue"
        ):
            return FakeLocator(
                text=self._trim
            )

        return FakeLocator()


class FakeResponse:
    def __init__(self, payload, ok=True):
        self._payload = payload
        self.ok = ok

    def json(self):
        return self._payload


class FakeRequest:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return self.response


class FakeApiPage(FakePage):
    def __init__(self, url, payload):
        super().__init__(
            url=url,
            breadcrumbs=[],
            trim="",
        )
        self.request = FakeRequest(
            FakeResponse(payload)
        )


def main():

    parser = AyvensVehicleIdentityParser()

    # TEST 1 - OPEL ASTRA
    page = FakePage(
        url=(
            "https://autotartosberlet.ayvens.com/"
            "opel/astra"
        ),
        breadcrumbs=[
            "Főoldal",
            "Tartós bérlet ajánlatok",
            "Opel",
            "Astra",
        ],
        trim=(
            "Edition Turbo dízel AT8 130 HP"
        ),
    )

    assert parser.parse_brand(page) == "Opel"
    assert parser.parse_model_name(page) == "Astra"
    assert (
        parser.parse_trim(page)
        == "Edition Turbo dízel AT8 130 HP"
    )

    print(
        "TEST 1 PASSED - "
        "OPEL ASTRA IDENTITY"
    )

    # TEST 2 - BYD ATTO 2 DM-i
    page = FakePage(
        url=(
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i"
        ),
        breadcrumbs=[
            "Főoldal",
            "Tartós bérlet ajánlatok",
            "BYD",
            "ATTO 2 DM-i",
        ],
        trim="Active 166 HP",
    )

    assert parser.parse_brand(page) == "BYD"
    assert (
        parser.parse_model_name(page)
        == "ATTO 2 DM-i"
    )
    assert (
        parser.parse_trim(page)
        == "Active 166 HP"
    )

    print(
        "TEST 2 PASSED - "
        "BYD ATTO 2 IDENTITY"
    )

    # TEST 3 - EXACT-OFFER API CONFIGURATION FALLBACK
    page = FakeApiPage(
        url=(
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i?campaign=test"
        ),
        payload={
            "data": {
                "configuration": "  Active 166 HP  ",
            },
        },
    )

    assert parser.parse_trim(page) == "Active 166 HP"
    assert page.request.calls == [
        (
            "https://autotartosberlet.ayvens.com/"
            "api/cars/byd/atto-2-dm-i",
            60000,
        )
    ]

    print(
        "TEST 3 PASSED - EXPLICIT EXACT-OFFER API "
        "CONFIGURATION FALLBACK"
    )

    # TEST 4 - CAPABILITY/IDENTITY DATA WITHOUT CONFIGURATION IS REJECTED
    page = FakeApiPage(
        url=(
            "https://autotartosberlet.ayvens.com/"
            "byd/atto-2-dm-i"
        ),
        payload={
            "data": {
                "model": {"name": "ATTO 2 DM-i"},
                "duration_mileage": {
                    "48": {"min": 20000, "max": 60000},
                },
            },
        },
    )

    try:
        parser.parse_trim(page)
    except ValueError as exc:
        assert "explicit provider API configuration" in str(exc)
    else:
        raise AssertionError(
            "Missing API configuration must not produce trim evidence."
        )

    print(
        "TEST 4 PASSED - MISSING CONFIGURATION REMAINS UNRESOLVED"
    )

    print(
        "\nALL AYVENS VEHICLE IDENTITY "
        "V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
