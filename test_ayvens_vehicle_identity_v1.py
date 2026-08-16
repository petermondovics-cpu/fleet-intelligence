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

    print(
        "\nALL AYVENS VEHICLE IDENTITY "
        "V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
