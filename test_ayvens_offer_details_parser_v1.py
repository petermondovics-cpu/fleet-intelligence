from models.financial_conditions import (
    EVIDENCE_UNKNOWN,
)
from scrapers.ayvens.offer_details_parser import (
    AyvensOfferDetailsParser,
)


class FakeLocator:

    def __init__(
        self,
        text="",
        count_value=1,
        attrs=None,
        checked=False,
        children=None,
        parent=None,
    ):
        self._text = text
        self._count = count_value
        self._attrs = attrs or {}
        self._checked = checked
        self._children = children or {}
        self._parent = parent

    @property
    def first(self):
        return self

    def count(self):
        return self._count

    def inner_text(self):
        return self._text

    def is_checked(self):
        return self._checked

    def get_attribute(self, name):
        return self._attrs.get(name)

    def locator(self, selector):
        if selector == "xpath=..":
            return self._parent or FakeLocator(
                count_value=0
            )

        return self._children.get(
            selector,
            FakeLocator(
                count_value=0
            ),
        )

    def get_by_text(
        self,
        text,
        exact=True,
    ):
        return self._children.get(
            ("text", text),
            FakeLocator(
                count_value=0
            ),
        )


class FakePage:

    def __init__(self):
        self.url = "https://example.com/ayvens"

        self.service_root = FakeLocator(
            text=(
                "Havidíjban foglalt szolgáltatások\n"
                "Teljes körű karbantartás\n"
                "Téli-, nyári gumiabroncs\n"
                "Assistance szolgáltatás\n"
                "MyAyvens online ügyintézési rendszer\n"
                "Vonatkozó adók\n"
                "Biztosítási csomag"
            )
        )

        for name in [
            "Teljes körű karbantartás",
            "Téli-, nyári gumiabroncs",
            "Assistance szolgáltatás",
            "MyAyvens online ügyintézési rendszer",
            "Vonatkozó adók",
            "Biztosítási csomag",
        ]:
            self.service_root._children[
                ("text", name)
            ] = FakeLocator(
                text=name
            )

        service_heading_parent = FakeLocator(
            text=self.service_root._text,
            children=self.service_root._children,
        )

        service_heading = FakeLocator(
            text="Havidíjban foglalt szolgáltatások",
            parent=service_heading_parent,
        )

        self.switch = FakeLocator(
            attrs={
                "role": "switch"
            },
            checked=True,
        )

        down_parent = FakeLocator(
            children={
                "input[role='switch']": self.switch
            }
        )

        self.down_label = FakeLocator(
            text="Induló befizetés",
            parent=down_parent,
        )

        self.duration_range = FakeLocator(
            attrs={
                "min": "36",
                "max": "60",
                "step": "12",
            }
        )

        duration_parent = FakeLocator(
            children={
                "input[type='range']": self.duration_range
            }
        )

        self.duration_label = FakeLocator(
            text="Futamidő",
            parent=duration_parent,
        )

        self.mileage_range = FakeLocator(
            attrs={
                "min": "20000",
                "max": "60000",
                "step": "10000",
            }
        )

        mileage_parent = FakeLocator(
            children={
                "input[type='range']": self.mileage_range
            }
        )

        self.mileage_label = FakeLocator(
            text="Futásteljesítmény",
            parent=mileage_parent,
        )

        self._map = {
            "Havidíjban foglalt szolgáltatások": (
                service_heading
            ),
            "Induló befizetés": (
                self.down_label
            ),
            "Futamidő": (
                self.duration_label
            ),
            "Futásteljesítmény": (
                self.mileage_label
            ),
        }

    def get_by_text(
        self,
        text,
        exact=True,
    ):
        return self._map.get(
            text,
            FakeLocator(
                count_value=0
            ),
        )


def main():

    parser = AyvensOfferDetailsParser()
    page = FakePage()

    # ========================================================
    # TEST 1 - SERVICES
    # ========================================================

    services = parser.parse_services(
        page
    )

    assert len(
        services.included()
    ) == 6

    assert (
        services.has_service(
            "MAINTENANCE",
            "Teljes körű karbantartás",
        )
        is True
    )

    assert (
        services.has_service(
            "INSURANCE",
            "Biztosítási csomag",
        )
        is True
    )

    print(
        "TEST 1 PASSED - "
        "AYVENS SERVICES PARSED"
    )

    # ========================================================
    # TEST 2 - DOWN PAYMENT SWITCH DOES NOT BECOME 20%
    # ========================================================

    down_payment = (
        parser.parse_down_payment(
            page
        )
    )

    assert down_payment.percent is None
    assert down_payment.amount is None
    assert (
        down_payment.status
        == EVIDENCE_UNKNOWN
    )

    print(
        "TEST 2 PASSED - "
        "DOWN PAYMENT SWITCH DOES NOT CREATE FALSE VALUE"
    )

    # ========================================================
    # TEST 3 - QUOTE CAPABILITIES
    # ========================================================

    capabilities = (
        parser.parse_quote_capabilities(
            page
        )
    )

    assert (
        capabilities.duration_min
        == 36
    )
    assert (
        capabilities.duration_max
        == 60
    )
    assert (
        capabilities.duration_step
        == 12
    )

    assert (
        capabilities.mileage_min
        == 20000
    )
    assert (
        capabilities.mileage_max
        == 60000
    )
    assert (
        capabilities.mileage_step
        == 10000
    )

    print(
        "TEST 3 PASSED - "
        "QUOTE CAPABILITIES PARSED"
    )

    # ========================================================
    # TEST 4 - CAPABILITIES ARE NOT OFFERS
    # ========================================================

    assert not hasattr(
        capabilities,
        "monthly_fee",
    )

    print(
        "TEST 4 PASSED - "
        "QUOTE CAPABILITIES KEPT SEPARATE FROM PRICING"
    )

    # ========================================================
    # TEST 5 - FINANCIAL CONDITIONS
    # ========================================================

    financial = (
        parser.build_financial_conditions(
            page,
            189990,
        )
    )

    assert (
        financial.monthly_fee
        == 189990
    )

    assert (
        financial.down_payment.percent
        is None
    )

    print(
        "TEST 5 PASSED - "
        "FINANCIAL CONDITIONS BUILT SAFELY"
    )

    print(
        "\nALL AYVENS OFFER DETAILS "
        "PARSER V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
