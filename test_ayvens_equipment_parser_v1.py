from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PUBLISHED,
)


class FakeLocator:

    def __init__(
        self,
        text="",
        attrs=None,
        count_value=1,
        visible=True,
        children=None,
    ):
        self._text = text
        self._attrs = attrs or {}
        self._count = count_value
        self._visible = visible
        self._children = children or {}
        self.clicked = False

    @property
    def first(self):
        return self

    def count(self):
        return self._count

    def nth(self, index):
        return self._children.get(
            ("nth", index),
            FakeLocator(
                count_value=0
            ),
        )

    def inner_text(self):
        return self._text

    def is_visible(self):
        return self._visible

    def get_attribute(self, name):
        return self._attrs.get(name)

    def click(self, timeout=5000):
        self.clicked = True
        self._attrs["aria-selected"] = "true"

    def locator(self, selector):
        return self._children.get(
            selector,
            FakeLocator(
                count_value=0
            ),
        )


class FakePage:

    def __init__(
        self,
        tab=None,
        panel=None,
    ):
        self.url = (
            "https://autotartosberlet."
            "ayvens.com/test/car"
        )

        self.tab = tab or FakeLocator(
            count_value=0
        )

        self.panel = panel or FakeLocator(
            count_value=0
        )

    def get_by_role(
        self,
        role,
        name=None,
        exact=True,
    ):
        if (
            role == "tab"
            and name == "Alapfelszereltség"
        ):
            return self.tab

        return FakeLocator(
            count_value=0
        )

    def get_by_text(
        self,
        text,
        exact=True,
    ):
        return FakeLocator(
            count_value=0
        )

    def locator(self, selector):
        if selector == "#panel-equipment":
            return self.panel

        if selector == "[role='tabpanel']":
            return self.panel

        return FakeLocator(
            count_value=0
        )

    def wait_for_timeout(self, ms):
        pass


def make_leaf(text):
    return FakeLocator(
        text=text,
        children={
            ":scope > *": FakeLocator(
                count_value=0
            )
        },
    )


def make_panel(
    texts,
):
    children = {}

    for index, text in enumerate(texts):
        children[
            ("nth", index)
        ] = make_leaf(
            text
        )

    candidates = FakeLocator(
        count_value=len(texts),
        children=children,
    )

    return FakeLocator(
        text="\n".join(texts),
        attrs={
            "role": "tabpanel"
        },
        children={
            "li, p, span, div": (
                candidates
            )
        },
    )


def main():

    parser = AyvensEquipmentParser()

    # ========================================================
    # TEST 1 - ACTIVE TAB WITH NO PUBLISHED ITEMS
    # ========================================================

    tab = FakeLocator(
        text="Alapfelszereltség",
        attrs={
            "aria-selected": "true",
            "aria-controls": "panel-equipment",
        },
    )

    empty_panel = make_panel(
        []
    )

    page = FakePage(
        tab=tab,
        panel=empty_panel,
    )

    result = (
        parser.parse_standard_equipment(
            page
        )
    )

    assert (
        result.status
        == EQUIPMENT_NOT_PUBLISHED
    )

    assert result.items == []

    print(
        "TEST 1 PASSED - "
        "EMPTY ACTIVE TAB IS NOT_PUBLISHED"
    )

    # ========================================================
    # TEST 2 - NOT_PUBLISHED IS NOT OBSERVED EMPTY EQUIPMENT
    # ========================================================

    assert result.published is False
    assert result.item_count == 0

    print(
        "TEST 2 PASSED - "
        "NOT_PUBLISHED KEPT DISTINCT FROM EMPTY EQUIPMENT"
    )

    # ========================================================
    # TEST 3 - PUBLISHED EQUIPMENT ITEMS
    # ========================================================

    panel = make_panel(
        [
            "LED fényszóró",
            "Kulcs nélküli nyitás",
            "Adaptív tempomat",
        ]
    )

    page = FakePage(
        tab=tab,
        panel=panel,
    )

    result = (
        parser.parse_standard_equipment(
            page
        )
    )

    assert (
        result.status
        == EQUIPMENT_PUBLISHED
    )

    assert result.item_count == 3

    assert all(
        item.included is True
        for item in result.items
    )

    assert all(
        item.standard is True
        for item in result.items
    )

    print(
        "TEST 3 PASSED - "
        "PUBLISHED STANDARD EQUIPMENT PARSED"
    )

    # ========================================================
    # TEST 4 - EVIDENCE ATTACHED
    # ========================================================

    first = result.items[0]

    assert (
        first.evidence.status
        == "OBSERVED"
    )

    assert (
        first.evidence.source_text
        == "LED fényszóró"
    )

    print(
        "TEST 4 PASSED - "
        "OBSERVED EQUIPMENT EVIDENCE ATTACHED"
    )

    # ========================================================
    # TEST 5 - INACTIVE TAB GETS ACTIVATED
    # ========================================================

    inactive_tab = FakeLocator(
        text="Alapfelszereltség",
        attrs={
            "aria-selected": "false",
            "aria-controls": "panel-equipment",
        },
    )

    page = FakePage(
        tab=inactive_tab,
        panel=panel,
    )

    result = (
        parser.parse_standard_equipment(
            page
        )
    )

    assert inactive_tab.clicked is True
    assert result.published is True

    print(
        "TEST 5 PASSED - "
        "EQUIPMENT TAB ACTIVATED"
    )

    # ========================================================
    # TEST 6 - MISSING TAB IS NOT_PUBLISHED
    # ========================================================

    missing_page = FakePage(
        tab=FakeLocator(
            count_value=0
        ),
        panel=FakeLocator(
            count_value=0
        ),
    )

    result = (
        parser.parse_standard_equipment(
            missing_page
        )
    )

    assert (
        result.status
        == EQUIPMENT_NOT_PUBLISHED
    )

    print(
        "TEST 6 PASSED - "
        "MISSING EQUIPMENT TAB HANDLED SAFELY"
    )

    print(
        "\nALL AYVENS EQUIPMENT "
        "PARSER V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
